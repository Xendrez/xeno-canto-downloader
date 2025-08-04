# Xeno-canto API v3 Reference

## API Endpoint
- Base URL: `https://xeno-canto.org/api/3/recordings`

## Authentication
- **Required**: API key for ALL requests
- Obtain key by registering at xeno-canto.org and verifying email
- Pass key as `key` parameter in query string
- **Security**: Never share or publish your API key

## Required Query Parameters
1. `query`: Search string using specific search tags
2. `key`: Your API authentication key

## Optional Parameters
- `per_page`: Number of results per page (50-500, default 100)
- `page`: Page number for pagination

## Query Syntax Rules
1. **Must use search tags** - Generic untagged searches are not allowed
2. **Quote multi-word terms** - e.g., `sp:"Turdus merula"`
3. **Combine tags with +** - e.g., `sp:"larus fuscus"+cnt:netherlands`
4. **Comparison operators** - Use =, <, > within quotes, e.g., `year:"<1970"`

## Search Tags

### Taxonomic Tags
- `sp`: Species (e.g., `sp:"Turdus merula"` or `sp:merula`)
- `gen`: Genus (e.g., `gen:Turdus`)
- `ssp`: Subspecies
- `fam`: Family
- `en`: English name

### Geographic Tags
- `cnt`: Country (e.g., `cnt:brazil` or `cnt:"south africa"`)
- `area`: Geographic area
- `loc`: Location
- `lat`: Latitude
- `lon`: Longitude

### Temporal Tags
- `year`: Year (supports comparisons)
- `month`: Month
- `since`: Recordings since date

### Recording Tags
- `type`: Sound type (song, call, etc.)
- `q`: Quality rating (A-E)
- `len`: Length
- `sex`: Sex of bird
- `stage`: Life stage

### Other Tags
- `rec`: Recordist name
- `rmk`: Remarks
- `grp`: Taxonomic group (birds, grasshoppers, bats)

## Example API Calls

### Basic species search
```
https://xeno-canto.org/api/3/recordings?query=sp:"Turdus merula"&key=YOUR_KEY
```

### Species in specific country
```
https://xeno-canto.org/api/3/recordings?query=sp:"larus fuscus"+cnt:netherlands&key=YOUR_KEY
```

### Genus with quality filter
```
https://xeno-canto.org/api/3/recordings?query=gen:Turdus+q:A&key=YOUR_KEY
```

### Geographic area search
```
https://xeno-canto.org/api/3/recordings?query=cnt:surinam+grp:frogs&key=YOUR_KEY
```

### Temporal search
```
https://xeno-canto.org/api/3/recordings?query=year:"<1970"+grp:birds&key=YOUR_KEY
```

## Response Format

### Metadata
```json
{
    "numRecordings": "total number of recordings",
    "numSpecies": "number of species",
    "page": "current page number",
    "numPages": "total pages available",
    "recordings": [...]
}
```

### Recording Object Fields
- `id`: Unique identifier
- `gen`: Genus
- `sp`: Species
- `ssp`: Subspecies
- `en`: English name
- `rec`: Recordist
- `cnt`: Country
- `loc`: Location
- `lat`: Latitude
- `lon`: Longitude
- `type`: Recording type
- `sex`: Sex
- `stage`: Life stage
- `method`: Recording method
- `url`: Web page URL
- `file`: Direct MP3 download URL
- `file-name`: Original filename
- `sono`: Sonogram URLs
- `q`: Quality rating
- `length`: Duration
- `time`: Time of day
- `date`: Recording date
- `uploaded`: Upload date
- `rmk`: Remarks
- `bird-seen`: Whether bird was seen
- `animal-seen`: Whether animal was seen
- `playback-used`: Whether playback was used
- `temp`: Temperature
- `regnr`: Registration number
- `auto`: Auto-generated recording
- `dvc`: Recording device
- `mic`: Microphone
- `smp`: Sample rate

## Important Notes

1. **URL Encoding**: The query parameter should be properly URL-encoded
2. **Rate Limiting**: 1000 requests per hour per IP
3. **Case Sensitivity**: Most tags are case-insensitive
4. **Spaces in Values**: Use quotes for multi-word values
5. **API v3 Changes**: 
   - Requires search tags (no generic searches)
   - Added `fam` and `en` tags
   - Standardized property names in responses

## Common Issues

1. **HTTP 400 Error**: Usually means query format is incorrect
   - Ensure you're using search tags
   - Check quotes around multi-word terms
   - Verify URL encoding

2. **HTTP 401 Error**: Invalid or missing API key

3. **HTTP 429 Error**: Rate limit exceeded (1000 req/hour)

## Best Practices

1. Use specific search tags for better performance
2. Cache responses to minimize API calls
3. Implement exponential backoff for retries
4. Log all API requests for debugging
5. Use pagination efficiently (higher per_page values)