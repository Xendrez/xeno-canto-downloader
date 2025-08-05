#!/usr/bin/env python3
"""
Create marker files for recordings that previously exceeded size limits
"""

import json
import re
from pathlib import Path

# Read the log file and extract recording IDs that exceeded size limit
def extract_failed_recordings():
    failed_recordings = set()
    log_file = Path("download_audio.log")
    
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return failed_recordings
    
    pattern = re.compile(r"Download exceeded size limit: https://xeno-canto\.org/(\d+)/download")
    
    with open(log_file, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                recording_id = match.group(1)
                failed_recordings.add(recording_id)
    
    return failed_recordings

# Find which species each recording belongs to
def find_recording_species(recording_id, cache_dir="xenocanto_cache"):
    cache_path = Path(cache_dir)
    
    for cache_file in cache_path.glob("*.json"):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                recordings = data.get('recordings', [])
                
                for rec in recordings:
                    if str(rec.get('id')) == recording_id:
                        # Extract species from filename
                        species = cache_file.stem.split('_page')[0]
                        return species.replace('_', ' ')
        except Exception as e:
            print(f"Error reading {cache_file}: {e}")
    
    return None

# Create marker files
def create_marker_files(failed_recordings):
    audio_dir = Path("xeno-raw")
    markers_created = 0
    
    for recording_id in failed_recordings:
        print(f"Processing recording {recording_id}...")
        
        # Find which species this recording belongs to
        species = find_recording_species(recording_id)
        
        if not species:
            print(f"  Could not find species for recording {recording_id}")
            continue
        
        # Create species directory path
        safe_species = species.replace(' ', '_').replace('/', '-')
        species_dir = audio_dir / safe_species
        
        if not species_dir.exists():
            print(f"  Species directory does not exist: {species_dir}")
            continue
        
        # Try to find the recording file pattern
        # We need to find what the filename would have been
        cache_file = Path("xenocanto_cache") / f"{safe_species}_page1.json"
        if not cache_file.exists():
            # Try without page number
            cache_file = Path("xenocanto_cache") / f"{safe_species}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    recordings = data.get('recordings', [])
                    
                    for rec in recordings:
                        if str(rec.get('id')) == recording_id:
                            file_name = rec.get('file-name', f"{recording_id}.mp3")
                            if not file_name.endswith('.mp3'):
                                file_name = f"{file_name}.mp3"
                            
                            # Create the expected filename
                            safe_filename = f"{recording_id}_{file_name}".replace('/', '-')
                            expected_file = species_dir / safe_filename
                            
                            # Create marker file
                            marker_file = expected_file.with_suffix('.size_limit_exceeded')
                            marker_file.touch()
                            markers_created += 1
                            print(f"  Created marker: {marker_file}")
                            break
            except Exception as e:
                print(f"  Error processing cache file: {e}")
    
    return markers_created

def main():
    print("=== Creating Size Limit Markers ===")
    
    # Extract failed recordings from log
    failed_recordings = extract_failed_recordings()
    print(f"Found {len(failed_recordings)} recordings that exceeded size limit")
    
    if not failed_recordings:
        print("No failed recordings found in log")
        return
    
    # Create marker files
    markers_created = create_marker_files(failed_recordings)
    
    print(f"\n=== Summary ===")
    print(f"Total recordings that exceeded size limit: {len(failed_recordings)}")
    print(f"Marker files created: {markers_created}")
    
    # List the recording IDs for reference
    print(f"\nRecording IDs that exceeded size limit:")
    for rec_id in sorted(failed_recordings):
        print(f"  - {rec_id}")

if __name__ == "__main__":
    main()