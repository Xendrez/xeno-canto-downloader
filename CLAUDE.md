# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
This repository downloads bird audio recordings from the Xeno-canto.org API v3. It fetches metadata, downloads MP3 files, and tracks species availability for research purposes.

## Common Commands

### Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install requests
```

### Running the Application
```bash
# 1. Fetch metadata from API (caches to xenocanto_cache/)
python xenocanto_fetch.py

# 2. Download audio files (saves to xeno-raw/{species}/)
python download_audio.py

# 3. Update species tracking with availability info
python update_labels_with_results.py
```

### Testing
```bash
# Test API queries
python test_api.py
```

## Architecture

### Core Components
- **xenocanto_fetch.py**: Queries Xeno-canto API for bird recording metadata, caches responses in JSON format
- **download_audio.py**: Downloads MP3 files using cached metadata, organizes by species
- **config.py**: Contains API credentials, rate limits (1.5s delay), download limits (30/species), and geographic filters (default: South Africa)

### Data Flow
1. **Input**: `labels.csv` with columns: birdId, birdName, scientificName
2. **Processing**: 
   - API queries are cached to `xenocanto_cache/` to avoid duplicate requests
   - Audio files download to `xeno-raw/{species}/`
   - Rate limiting enforced (1000 requests/hour)
3. **Output**: `labels_updated.csv` with availability tracking, `fetch_summary.csv` with statistics

### Key Implementation Details
- **API Integration**: Uses Xeno-canto API v3 with proper authentication and rate limiting
- **Error Handling**: Automatic retry on rate limits (HTTP 429), exponential backoff for network errors
- **Caching Strategy**: All API responses cached to minimize API calls and enable offline processing
- **File Organization**: Audio files organized by species scientific name with sanitized filenames