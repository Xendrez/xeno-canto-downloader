# Xeno-canto API Download Specification

## Overview
A guide for safely downloading bird recordings from Xeno-canto using their API v3, respecting rate limits and authentication requirements.

---

## 1. API Authentication Requirements

### Getting an API Key
- Register at https://xeno-canto.org
- Verify your email address
- Obtain your API key from your account settings
- **IMPORTANT**: Never share your API key publicly

### Using the API Key
- Required for ALL API v3 requests
- Pass as `key` parameter in query string
- Store securely in environment variables or config file

---

## 2. API Endpoint and Structure

### Base Endpoint
```
https://xeno-canto.org/api/3/recordings
```

### Required Parameters
- `query`: Search string using specific search tags
- `key`: Your API authentication key

### Optional Parameters
- `per_page`: Results per page (50-500, default 100)
- `page`: Page number for pagination

---

## 3. Search Query Format

### Search Tags
The API v3 requires using specific search tags:

**Taxonomic Tags:**
- `sp`: Species name (e.g., `sp:"Turdus merula"`)
- `gen`: Genus (e.g., `gen:Turdus`)
- `fam`: Family
- `en`: English name

**Geographic Tags:**
- `cnt`: Country code (e.g., `cnt:ZA` for South Africa)
- `area`: Geographic area (e.g., `area:"Southern Africa"`)
- `loc`: Specific location
- `lat`, `lon`: Coordinates

**Other Tags:**
- `q`: Recording quality (A-E)
- `type`: Sound type (song, call, etc.)
- `year`, `month`: Temporal filters

### Example Queries
```
# Species in South Africa
query=sp:"Turdus merula"+cnt:ZA

# All recordings from Southern Africa with quality A
query=area:"Southern Africa"+q:A

# Genus with specific sound type
query=gen:Turdus+type:song
```

---

## 4. Rate Limits and Best Practices

### Rate Limiting
- **Limit**: 1,000 requests per hour per IP address
- **HTTP 429**: Returned when limit exceeded
- **Strategy**: Stay under 800-900 requests/hour for safety

### Throttling Strategy
1. **Request Delay**: 1-2 seconds between API calls
2. **Batch Processing**: Process one species at a time
3. **Per-Species Cap**: Limit to 30-50 recordings per species
4. **Caching**: Store API responses to avoid duplicate calls

---

## 5. Implementation Steps

### Step 1: Setup and Configuration
```python
# Configuration
API_KEY = "your_api_key_here"  # Store securely
BASE_URL = "https://xeno-canto.org/api/3/recordings"
CACHE_DIR = "xenocanto_cache"
MAX_RECORDINGS_PER_SPECIES = 30
REQUEST_DELAY = 1.5  # seconds
```

### Step 2: Read Species List
```python
# Read from labels.csv
# Format: birdId, birdName, scientificName
```

### Step 3: Build Query for Each Species
```python
# For each species:
query = f'sp:"{genus} {species}"+cnt:ZA'
params = {
    'query': query,
    'key': API_KEY,
    'per_page': 100,
    'page': 1
}
```

### Step 4: Paginated Fetching
```python
# Fetch pages until:
# - No more pages (check response['numPages'])
# - Reached MAX_RECORDINGS_PER_SPECIES
# - HTTP 429 error (implement backoff)
```

### Step 5: Cache Management
```python
# Save responses as:
# xenocanto_cache/{species}_page{N}.json
# Check cache before making API calls
```

### Step 6: Error Handling
```python
# Handle:
# - HTTP 429: Wait 60 seconds, retry
# - HTTP 401: Invalid API key
# - Network errors: Retry with exponential backoff
```

---

## 6. Response Format

### Metadata
```json
{
    "numRecordings": "total number",
    "numSpecies": "species count",
    "page": "current page",
    "numPages": "total pages",
    "recordings": [...]
}
```

### Recording Object
Each recording contains:
- `id`: Unique identifier
- `url`: Web page URL
- `file`: Direct MP3 download URL
- `sono`: Sonogram URLs
- `sp`: Species name
- `loc`: Location
- `cnt`: Country
- `q`: Quality rating
- And many more metadata fields

---

## 7. Download Workflow

### Phase 1: Metadata Collection
1. Fetch and cache all metadata via API
2. Create summary of available recordings
3. Log API usage statistics

### Phase 2: Audio Download (separate script)
1. Read cached JSON files
2. Extract MP3 URLs from `file` field
3. Download audio files to `xeno-raw/{species}/`
4. Skip existing files
5. Validate downloads (checksum, size)

---

## 8. Example Implementation Structure

```
xenocanto_fetch.py      # Main API fetcher
├── Load species list from labels.csv
├── For each species:
│   ├── Check cache
│   ├── Build API query with search tags
│   ├── Fetch pages with throttling
│   ├── Handle errors and rate limits
│   └── Save to cache
└── Generate summary report

download_audio.py       # Audio downloader
├── Read cached JSON files
├── Extract audio URLs
├── Download MP3 files
└── Validate downloads
```

---

## 9. Logging and Monitoring

### Progress Tracking
- Log each API request with timestamp
- Track recordings fetched per species
- Monitor total API calls vs rate limit
- Generate summary CSV: species, recordings_fetched, pages_requested

### Error Logging
- Failed requests with reason
- Rate limit violations
- Authentication failures
- Network errors

---

## 10. Summary Checklist

✅ Obtain and secure API key  
✅ Use API v3 endpoint  
✅ Format queries with search tags  
✅ Implement request throttling  
✅ Cache all API responses  
✅ Handle rate limits gracefully  
✅ Separate metadata fetch from downloads  
✅ Log all operations  
✅ Validate data integrity