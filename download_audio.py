#!/usr/bin/env python3
"""
Xeno-canto Audio Downloader
Downloads MP3 files from cached metadata
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from config import AUDIO_DIR, CACHE_DIR, REQUEST_DELAY


class AudioDownloader:
    """Handles downloading MP3 files from Xeno-canto"""
    
    def __init__(self):
        self.session = requests.Session()
        self.total_downloads = 0
        self.total_skipped = 0
        self.total_errors = 0
        self.total_size_exceeded = 0
        self.start_time = datetime.now()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('download_audio.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create audio directory
        Path(AUDIO_DIR).mkdir(exist_ok=True)
    
    def get_cached_files(self) -> List[Path]:
        """Get all cached JSON files"""
        cache_path = Path(CACHE_DIR)
        if not cache_path.exists():
            self.logger.error(f"Cache directory not found: {CACHE_DIR}")
            return []
            
        return sorted(cache_path.glob("*.json"))
    
    def read_cache_file(self, cache_file: Path) -> Optional[Dict]:
        """Read a cached JSON file"""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading {cache_file}: {e}")
            return None
    
    def get_species_from_filename(self, filename: str) -> str:
        """Extract species name from cache filename"""
        # Format: Genus_species_pageN.json
        parts = filename.replace('.json', '').split('_page')
        if parts:
            return parts[0].replace('_', ' ')
        return filename
    
    def create_species_directory(self, species: str) -> Path:
        """Create directory for species audio files"""
        safe_species = species.replace(' ', '_').replace('/', '-')
        species_dir = Path(AUDIO_DIR) / safe_species
        species_dir.mkdir(exist_ok=True)
        return species_dir
    
    def get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def create_size_limit_marker(self, filepath: Path) -> None:
        """Create a marker file to indicate size limit was exceeded"""
        marker_path = filepath.with_suffix('.size_limit_exceeded')
        marker_path.touch()
        self.logger.debug(f"Created size limit marker: {marker_path}")
    
    def check_size_limit_marker(self, filepath: Path) -> bool:
        """Check if a size limit marker exists for this file"""
        marker_path = filepath.with_suffix('.size_limit_exceeded')
        return marker_path.exists()
    
    def download_file(self, url: str, filepath: Path, max_size: int = 50 * 1024 * 1024) -> Tuple[bool, str]:
        """Download a file with size limit (default 50MB)
        Returns: (success, status) where status is 'downloaded', 'size_exceeded', or 'error'
        """
        try:
            # Make request
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size:
                self.logger.warning(f"File too large ({int(content_length)/1024/1024:.1f}MB): {url}")
                self.create_size_limit_marker(filepath)
                return False, 'size_exceeded'
            
            # Download file
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Check size during download
                        if downloaded > max_size:
                            self.logger.warning(f"Download exceeded size limit: {url}")
                            os.remove(filepath)
                            self.create_size_limit_marker(filepath)
                            return False, 'size_exceeded'
            
            # Verify file exists and has content
            if filepath.exists() and filepath.stat().st_size > 0:
                return True, 'downloaded'
            else:
                self.logger.error(f"Downloaded file is empty or missing: {filepath}")
                return False, 'error'
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Download error: {e}")
            if filepath.exists():
                os.remove(filepath)
            return False, 'error'
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {url}: {e}")
            if filepath.exists():
                os.remove(filepath)
            return False, 'error'
    
    def process_recording(self, recording: Dict, species_dir: Path) -> Tuple[bool, bool]:
        """Process a single recording
        Returns: (success, was_downloaded) - second value True if actually downloaded, False if skipped
        """
        try:
            # Extract metadata
            rec_id = recording.get('id', 'unknown')
            file_url = recording.get('file')
            file_name = recording.get('file-name', f"{rec_id}.mp3")
            
            if not file_url:
                self.logger.warning(f"No file URL for recording {rec_id}")
                return False, False
            
            # Ensure .mp3 extension
            if not file_name.endswith('.mp3'):
                file_name = f"{file_name}.mp3"
            
            # Create safe filename
            safe_filename = f"{rec_id}_{file_name}".replace('/', '-')
            filepath = species_dir / safe_filename
            
            # Check if already downloaded
            if filepath.exists():
                self.logger.debug(f"Already downloaded: {safe_filename}")
                self.total_skipped += 1
                return True, False  # Success but not downloaded
            
            # Check if size limit was previously exceeded
            if self.check_size_limit_marker(filepath):
                self.logger.debug(f"Skipping (previously exceeded size limit): {safe_filename}")
                self.total_size_exceeded += 1
                return True, False  # Success but not downloaded
            
            # Download file
            self.logger.info(f"Downloading: {safe_filename}")
            success, status = self.download_file(file_url, filepath)
            
            if success:
                self.total_downloads += 1
                
                # Log some metadata
                quality = recording.get('q', 'unknown')
                duration = recording.get('length', 'unknown')
                self.logger.info(
                    f"Downloaded: {safe_filename} "
                    f"(quality: {quality}, duration: {duration})"
                )
                return True, True  # Success and downloaded
            elif status == 'size_exceeded':
                self.total_size_exceeded += 1
                return True, False  # Treated as success but not downloaded
            else:
                self.total_errors += 1
                return False, False
                
        except Exception as e:
            self.logger.error(f"Error processing recording: {e}")
            self.total_errors += 1
            return False, False
    
    def process_species_cache(self, cache_file: Path) -> None:
        """Process all recordings in a cache file"""
        species = self.get_species_from_filename(cache_file.name)
        self.logger.info(f"\nProcessing species: {species}")
        
        # Read cache data
        data = self.read_cache_file(cache_file)
        if not data:
            return
        
        # Create species directory
        species_dir = self.create_species_directory(species)
        
        # Process recordings
        recordings = data.get('recordings', [])
        if not recordings:
            self.logger.warning(f"No recordings found in {cache_file.name}")
            return
        
        self.logger.info(f"Found {len(recordings)} recordings for {species}")
        
        for i, recording in enumerate(recordings, 1):
            self.logger.info(f"[{i}/{len(recordings)}] Processing recording...")
            
            # Process recording
            success, was_downloaded = self.process_recording(recording, species_dir)
            
            # Rate limiting - only delay after actual downloads
            if was_downloaded:
                time.sleep(REQUEST_DELAY)
    
    def generate_download_summary(self) -> None:
        """Generate download summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        self.logger.info("\n=== Download Summary ===")
        self.logger.info(f"Total downloads: {self.total_downloads}")
        self.logger.info(f"Total skipped (already downloaded): {self.total_skipped}")
        self.logger.info(f"Total skipped (size limit exceeded): {self.total_size_exceeded}")
        self.logger.info(f"Total errors: {self.total_errors}")
        self.logger.info(f"Total time: {elapsed/60:.1f} minutes")
        
        if self.total_downloads > 0:
            self.logger.info(f"Average download time: {elapsed/self.total_downloads:.1f}s per file")
    
    def run(self) -> None:
        """Main execution method"""
        self.logger.info("=== Xeno-canto Audio Downloader Started ===")
        
        # Get cached files
        cache_files = self.get_cached_files()
        if not cache_files:
            self.logger.error("No cached files found. Run xenocanto_fetch.py first.")
            return
        
        self.logger.info(f"Found {len(cache_files)} cache files to process")
        
        # Process each cache file
        for cache_file in cache_files:
            self.process_species_cache(cache_file)
            
            # Log progress
            self.logger.info(
                f"Progress: Downloads: {self.total_downloads}, "
                f"Skipped: {self.total_skipped}, "
                f"Errors: {self.total_errors}"
            )
        
        # Generate summary
        self.generate_download_summary()


if __name__ == "__main__":
    downloader = AudioDownloader()
    downloader.run()