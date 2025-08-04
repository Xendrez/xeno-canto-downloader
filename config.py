"""
Configuration file for Xeno-canto API access
"""

# IMPORTANT: Replace with your actual API key from xeno-canto.org
# To get a key: 
# 1. Register at https://xeno-canto.org
# 2. Verify your email
# 3. Get your key from account settings
API_KEY = "3bc701bcbeb3fe18b900d9eb6516ed25361688eb"

# API Configuration
BASE_URL = "https://xeno-canto.org/api/3/recordings"
REQUEST_DELAY = 1.5  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds to wait on rate limit

# Download Configuration
CACHE_DIR = "xenocanto_cache"
AUDIO_DIR = "xeno-raw"
MAX_RECORDINGS_PER_SPECIES = 30
RESULTS_PER_PAGE = 100  # 50-500, default 100

# Geographic filters
DEFAULT_COUNTRY = "ZA"  # South Africa
DEFAULT_AREA = "Southern Africa"

# Logging
LOG_FILE = "xenocanto_fetch.log"
SUMMARY_FILE = "fetch_summary.csv"