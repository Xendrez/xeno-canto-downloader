#!/usr/bin/env python3
"""
Update labels.csv with information about which species were found in Xeno-canto
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, Set

from config import CACHE_DIR


def get_species_with_recordings() -> Dict[str, int]:
    """
    Scan cache directory to find which species have recordings.
    Returns dict of {species_name: recording_count}
    """
    species_recordings = {}
    cache_path = Path(CACHE_DIR)
    
    if not cache_path.exists():
        print(f"Cache directory not found: {CACHE_DIR}")
        return species_recordings
    
    # Process all cached JSON files
    for cache_file in cache_path.glob("*.json"):
        try:
            # Extract species name from filename
            # Format: Genus_species_pageN.json
            filename = cache_file.stem  # Remove .json
            parts = filename.split('_page')
            if len(parts) >= 2:
                species_name = parts[0].replace('_', ' ')
                
                # Read the cache file
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    
                # Count recordings
                num_recordings = int(data.get('numRecordings', 0))
                
                # Update the count (in case of multiple pages)
                if species_name in species_recordings:
                    # Don't double count - use the max reported
                    species_recordings[species_name] = max(species_recordings[species_name], num_recordings)
                else:
                    species_recordings[species_name] = num_recordings
                    
        except Exception as e:
            print(f"Error processing {cache_file}: {e}")
            
    return species_recordings


def update_labels_csv(input_file: str = 'labels.csv', output_file: str = 'labels_updated.csv'):
    """Update labels.csv with Xeno-canto availability information"""
    
    # Get species with recordings
    species_recordings = get_species_with_recordings()
    print(f"Found {len(species_recordings)} species with cached data")
    
    # Read the original CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        original_fieldnames = reader.fieldnames
        
        for row in reader:
            rows.append(row)
    
    # Add new columns if they don't exist
    fieldnames = list(original_fieldnames)
    if 'found_in_xenocanto' not in fieldnames:
        fieldnames.append('found_in_xenocanto')
    if 'xenocanto_recordings' not in fieldnames:
        fieldnames.append('xenocanto_recordings')
    
    # Update each row
    found_count = 0
    not_found_count = 0
    
    for row in rows:
        scientific_name = row.get('scientificName', '')
        
        if scientific_name in species_recordings:
            row['found_in_xenocanto'] = 'Yes'
            row['xenocanto_recordings'] = str(species_recordings[scientific_name])
            found_count += 1
        else:
            # Check if we've actually searched for this species
            # (if no cache file exists, we haven't searched yet)
            cache_file = Path(CACHE_DIR) / f"{scientific_name.replace(' ', '_')}_page1.json"
            if cache_file.exists():
                # We searched but found no recordings
                row['found_in_xenocanto'] = 'No'
                row['xenocanto_recordings'] = '0'
                not_found_count += 1
            else:
                # Haven't searched yet
                row['found_in_xenocanto'] = 'Not searched'
                row['xenocanto_recordings'] = ''
    
    # Write the updated CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total species: {len(rows)}")
    print(f"Found in Xeno-canto: {found_count}")
    print(f"Not found in Xeno-canto: {not_found_count}")
    print(f"Not yet searched: {len(rows) - found_count - not_found_count}")
    print(f"\nUpdated file saved as: {output_file}")
    
    # Also print species with most recordings
    if species_recordings:
        print("\nTop 10 species by recording count:")
        sorted_species = sorted(species_recordings.items(), key=lambda x: x[1], reverse=True)[:10]
        for species, count in sorted_species:
            print(f"  {species}: {count} recordings")


if __name__ == "__main__":
    update_labels_csv()