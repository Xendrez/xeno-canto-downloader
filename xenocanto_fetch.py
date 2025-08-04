#!/usr/bin/env python3
"""
Xeno-canto API Fetcher
Fetches bird recording metadata from xeno-canto.org API v3
"""

import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests

from config import (
    API_KEY, BASE_URL, CACHE_DIR, DEFAULT_AREA, DEFAULT_COUNTRY,
    LOG_FILE, MAX_RECORDINGS_PER_SPECIES, MAX_RETRIES, REQUEST_DELAY,
    RESULTS_PER_PAGE, RETRY_DELAY, SUMMARY_FILE
)


class XenoCantoFetcher:
    """Handles fetching recordings from Xeno-canto API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.total_api_calls = 0
        self.start_time = datetime.now()
        self.summary_data = []
        
        # Setup directories
        Path(CACHE_DIR).mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def read_species_list(self, csv_file: str) -> List[Dict[str, str]]:
        """Read species list from CSV file"""
        species_list = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Handle different possible column names
                    species_data = {
                        'birdId': row.get('birdId', ''),
                        'birdName': row.get('birdName', ''),
                        'scientificName': row.get('scientificName', '')
                    }
                    
                    # Ensure we have at least a scientific name
                    if species_data['scientificName']:
                        species_list.append(species_data)
                    else:
                        self.logger.warning(f"Skipping row with no scientific name: {row}")
                        
        except FileNotFoundError:
            self.logger.error(f"Species list file not found: {csv_file}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Error reading species list: {e}")
            sys.exit(1)
            
        self.logger.info(f"Loaded {len(species_list)} species from {csv_file}")
        return species_list
    
    def get_cache_path(self, species: str, page: int) -> Path:
        """Get cache file path for a species and page"""
        safe_species = species.replace(' ', '_').replace('/', '-')
        return Path(CACHE_DIR) / f"{safe_species}_page{page}.json"
    
    def check_cache(self, species: str, page: int) -> Optional[Dict]:
        """Check if cached data exists for species and page"""
        cache_path = self.get_cache_path(species, page)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    self.logger.debug(f"Cache hit: {species} page {page}")
                    return data
            except Exception as e:
                self.logger.warning(f"Error reading cache for {species} page {page}: {e}")
                
        return None
    
    def save_to_cache(self, species: str, page: int, data: Dict) -> None:
        """Save API response to cache"""
        cache_path = self.get_cache_path(species, page)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Cached: {species} page {page}")
        except Exception as e:
            self.logger.error(f"Error saving cache for {species} page {page}: {e}")
    
    def build_query(self, scientific_name: str, country: str = DEFAULT_COUNTRY) -> str:
        """Build API query string with search tags"""
        # Format: sp:"Genus species"+cnt:ZA
        query = f'sp:"{scientific_name}"'
        
        if country:
            query += f'+cnt:{country}'
            
        return query
    
    def make_api_request(self, query: str, page: int = 1) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        params = {
            'query': query,
            'key': API_KEY,
            'per_page': RESULTS_PER_PAGE,
            'page': page
        }
        
        url = f"{BASE_URL}?{urlencode(params)}"
        
        for attempt in range(MAX_RETRIES):
            try:
                # Rate limiting
                time.sleep(REQUEST_DELAY)
                
                # Make request
                response = self.session.get(url)
                self.total_api_calls += 1
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    self.logger.error("Invalid API key (HTTP 401)")
                    sys.exit(1)
                elif response.status_code == 429:
                    self.logger.warning(f"Rate limit hit (HTTP 429). Waiting {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    self.logger.error(f"HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(REQUEST_DELAY * (attempt + 1))
                    
        return None
    
    def fetch_species_recordings(self, species_data: Dict[str, str]) -> Tuple[int, int]:
        """Fetch all recordings for a species with pagination"""
        scientific_name = species_data['scientificName']
        self.logger.info(f"Fetching recordings for: {scientific_name}")
        
        query = self.build_query(scientific_name)
        recordings_fetched = 0
        pages_requested = 0
        page = 1
        
        while recordings_fetched < MAX_RECORDINGS_PER_SPECIES:
            # Check cache first
            cached_data = self.check_cache(scientific_name, page)
            
            if cached_data:
                data = cached_data
            else:
                # Fetch from API
                data = self.make_api_request(query, page)
                
                if not data:
                    self.logger.error(f"Failed to fetch page {page} for {scientific_name}")
                    break
                    
                # Save to cache
                self.save_to_cache(scientific_name, page, data)
                pages_requested += 1
            
            # Process response
            recordings = data.get('recordings', [])
            if not recordings:
                break
                
            # Count recordings
            page_recordings = len(recordings)
            recordings_fetched += page_recordings
            
            self.logger.info(
                f"{scientific_name}: Page {page}/{data.get('numPages', '?')} - "
                f"{page_recordings} recordings (total: {recordings_fetched})"
            )
            
            # Check if more pages exist
            if page >= int(data.get('numPages', 0)):
                break
                
            # Check if we've hit our limit
            if recordings_fetched >= MAX_RECORDINGS_PER_SPECIES:
                self.logger.info(f"Reached recording limit for {scientific_name}")
                break
                
            page += 1
        
        return recordings_fetched, pages_requested
    
    def generate_summary(self) -> None:
        """Generate summary CSV file"""
        try:
            with open(SUMMARY_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['species', 'recordings_fetched', 'pages_requested'])
                writer.writerows(self.summary_data)
                
            self.logger.info(f"Summary saved to {SUMMARY_FILE}")
        except Exception as e:
            self.logger.error(f"Error writing summary: {e}")
    
    def run(self, csv_file: str = 'labels.csv') -> None:
        """Main execution method"""
        self.logger.info("=== Xeno-canto Fetcher Started ===")
        self.logger.info(f"API calls limit: ~800-900 per hour")
        
        # Read species list
        species_list = self.read_species_list(csv_file)
        
        # Process each species
        for i, species_data in enumerate(species_list, 1):
            scientific_name = species_data['scientificName']
            
            # Check API call rate
            if self.total_api_calls >= 800:
                self.logger.warning("Approaching API rate limit. Stopping.")
                break
            
            self.logger.info(f"\n[{i}/{len(species_list)}] Processing: {scientific_name}")
            
            # Fetch recordings
            recordings_fetched, pages_requested = self.fetch_species_recordings(species_data)
            
            # Add to summary
            self.summary_data.append([scientific_name, recordings_fetched, pages_requested])
            
            # Log progress
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.total_api_calls / (elapsed / 3600) if elapsed > 0 else 0
            self.logger.info(
                f"Progress: {i}/{len(species_list)} species, "
                f"{self.total_api_calls} API calls, "
                f"{rate:.1f} calls/hour"
            )
        
        # Generate summary
        self.generate_summary()
        
        # Final stats
        total_time = (datetime.now() - self.start_time).total_seconds()
        self.logger.info("\n=== Fetch Complete ===")
        self.logger.info(f"Total species processed: {len(self.summary_data)}")
        self.logger.info(f"Total API calls: {self.total_api_calls}")
        self.logger.info(f"Total time: {total_time/60:.1f} minutes")
        self.logger.info(f"Average rate: {self.total_api_calls/(total_time/3600):.1f} calls/hour")


if __name__ == "__main__":
    fetcher = XenoCantoFetcher()
    fetcher.run()