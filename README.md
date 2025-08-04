# Xeno-canto Downloader

A Python tool for downloading bird recordings from Xeno-canto.org using their API v3.

## Setup

1. **Get an API Key**
   - Register at https://xeno-canto.org
   - Verify your email
   - Get your API key from account settings
   - Update `API_KEY` in `config.py`

2. **Install Dependencies**
   ```bash
   pip install requests
   ```

3. **Prepare Species List**
   - Create a `labels.csv` file with columns: `birdId`, `birdName`, `scientificName`
   - See `labels_sample.csv` for format example

## Usage

### Step 1: Fetch Metadata
```bash
python xenocanto_fetch.py
```

This will:
- Read species from `labels.csv`
- Query Xeno-canto API for each species
- Cache results in `xenocanto_cache/` directory
- Respect rate limits (1000 requests/hour)
- Generate `fetch_summary.csv` with statistics

### Step 2: Download Audio Files
```bash
python download_audio.py
```

This will:
- Read cached metadata from Step 1
- Download MP3 files to `xeno-raw/{species}/` directories
- Skip already downloaded files
- Log progress to `download_audio.log`

## Configuration

Edit `config.py` to customize:
- `API_KEY`: Your Xeno-canto API key (required)
- `MAX_RECORDINGS_PER_SPECIES`: Limit recordings per species (default: 30)
- `DEFAULT_COUNTRY`: Country filter (default: "ZA" for South Africa)
- `REQUEST_DELAY`: Seconds between requests (default: 1.5)

## Output Structure

```
xeno-canto downloads/
├── xenocanto_cache/          # Cached API responses
│   ├── Cossypha_caffra_page1.json
│   └── ...
├── xeno-raw/                 # Downloaded audio files
│   ├── Cossypha_caffra/
│   │   ├── 123456_XC123456.mp3
│   │   └── ...
│   └── ...
├── xenocanto_fetch.log       # Fetch operation log
├── download_audio.log        # Download operation log
├── fetch_summary.csv         # Summary statistics
└── labels_updated.csv        # Species list with Xeno-canto availability
```

## Tracking Species Availability

### Update labels.csv with results
```bash
python update_labels_with_results.py
```

This will:
- Scan cached data to find which species have recordings
- Create `labels_updated.csv` with two new columns:
  - `found_in_xenocanto`: Yes/No/Not searched
  - `xenocanto_recordings`: Number of recordings available

### Update labels.csv in place
```bash
python update_labels_inplace.py
```

This will:
- Create a timestamped backup of labels.csv
- Update the original labels.csv with Xeno-canto results

## Rate Limiting

- API limit: 1000 requests/hour/IP
- Script stays under 800-900 requests for safety
- Automatic retry on rate limit (HTTP 429)
- 1.5 second delay between requests

## Troubleshooting

1. **HTTP 401 Error**: Invalid API key - check your key in `config.py`
2. **HTTP 429 Error**: Rate limit hit - script will wait 60s and retry
3. **No recordings found**: Check species names match Xeno-canto database
4. **Network errors**: Script will retry up to 3 times with backoff