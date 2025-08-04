#!/usr/bin/env python3
"""Test script to debug Xeno-canto API queries"""

import requests
from config import API_KEY

# Test different query formats
test_queries = [
    # Original format
    'sp:"Turdus merula"+cnt:ZA',
    
    # Without quotes
    'sp:Turdus merula+cnt:ZA',
    
    # With underscores
    'sp:Turdus_merula+cnt:ZA',
    
    # Just species
    'sp:"Turdus merula"',
    
    # Using gen and sp separately
    'gen:Turdus+sp:merula',
    
    # Simple single word species
    'sp:merula',
    
    # Test with a known species from the API docs
    'sp:"larus fuscus"',
    
    # Test without country filter
    'sp:"Cossypha caffra"',
]

print("Testing Xeno-canto API v3 queries...")
print(f"Using API key: {API_KEY[:10]}...")

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Testing query: {query}")
    
    # Test with requests library parameter handling
    params = {
        'query': query,
        'key': API_KEY,
        'per_page': 10
    }
    
    try:
        response = requests.get("https://xeno-canto.org/api/3/recordings", params=params)
        print(f"Final URL: {response.url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Found {data.get('numRecordings', 0)} recordings")
            if data.get('recordings'):
                first_rec = data['recordings'][0]
                print(f"  First recording: {first_rec.get('sp')} by {first_rec.get('rec')}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Exception: {e}")