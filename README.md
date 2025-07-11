# Tunisian University Orientation Guide Scraper

A comprehensive web scraping tool for extracting data from the Tunisian University Orientation website (https://guide-orientation.rnu.tn/).

## 🎯 Project Overview

This project scrapes detailed information about Tunisian universities, institutions, and academic programs including:
- University and institution details
- Program specifications and requirements
- Historical admission scores
- Baccalaureate requirements
- Geographic distribution information

## 📊 Data Structure

The scraper extracts the following information for each specialization:

| Field | Description | Example |
|-------|-------------|---------|
| `ramz_code` | Specialization code | "10101" |
| `university` | University name | "جامعة تونس" |
| `governorate` | Governorate | "تونس" |
| `institution` | Institution name | "كلية العلوم الإنسانية والإجتماعية بتونس" |
| `address` | Institution address | "94 شارع 9 أفريل 1938ـ تـونس 1007" |
| `phone` | Contact phone | "71564713/71564797" |
| `specialization` | Program name | "الإجازة في العربية" |
| `training_field` | Training domain | "الآداب واللغات والمراحل التحضيرية الأدبية" |
| `specializations` | Specializations | "اللغة والآداب والحضارة" |
| `measure` | Measurement criteria | "FG+AR" |
| `bac_type` | Baccalaureate type | "آداب" |
| `capacity_2025` | 2025 capacity | "50" |
| `requires_test` | Requires entrance test | "لا" |
| `geographic_distribution` | Geographic distribution (7%) | "نعم" |
| `conditions` | Entry conditions | "لاشئ" |
| `study_duration` | Study duration | "03 سنوات" |
| `last_oriented_score_2024` | Last admission score 2024 | "97.8750" |
| `score_history` | Historical scores by year | `{"2023": "95.2", "2024": "97.8"}` |

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone or download this project
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

- `requests` - HTTP library for making web requests
- `beautifulsoup4` - HTML parsing library
- `selenium` - Web browser automation (for complex interactions)
- `pandas` - Data manipulation and analysis
- `aiohttp` - Asynchronous HTTP client
- `fake-useragent` - Generate fake user agent headers
- `tqdm` - Progress bars
- `matplotlib`, `seaborn` - Data visualization
- `jupyter` - Interactive notebooks

## 📁 Project Structure

```
ba/
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── website_analyzer.py      # Website structure analysis
├── university_scraper.py    # Main comprehensive scraper
├── test_single_ramz.py     # Test script for single page
├── data/                   # Directory for scraped data
├── scrapers/              # Specialized scrapers
├── analysis/              # Data analysis tools
├── notebooks/             # Jupyter notebooks
└── .github/
    └── copilot-instructions.md
```

## 🔧 Usage

### 1. Test Single Page Scraping

First, test the scraper on a single page to understand the data structure:

```bash
python test_single_ramz.py
```

This will:
- Test scraping a few sample ramz pages
- Show you the exact data structure
- Create a sample CSV file
- Display what information can be extracted

### 2. Analyze Website Structure

Understand the website's dropdown options and form structure:

```bash
python website_analyzer.py
```

### 3. Full Comprehensive Scraping

Run the complete scraper to extract all data:

```bash
python university_scraper.py
```

This will:
1. **Analyze dropdown options** - Extract all baccalaureate types
2. **Collect ramz links** - Get all specialization links for each bac type
3. **Test scraping** - Test on a few samples first
4. **Full parallel scraping** - Scrape all data using multiple threads
5. **Save results** - Export to both JSON and CSV formats

## ⚡ Parallel Processing

The scraper uses parallel processing to speed up data collection:

- **Default**: 5 concurrent workers
- **Adjustable**: Modify `max_workers` parameter
- **Rate limiting**: Built-in delays to respect server limits
- **Error handling**: Robust error handling and retry mechanisms

## 📊 Output Formats

### CSV Output
- Clean tabular format
- Easy to import into Excel/Google Sheets
- Score history as JSON string

### JSON Output
- Preserves complex data structures
- Machine-readable format
- Includes raw HTML for debugging

## 🔍 Workflow Explanation

The scraping process follows this workflow:

1. **Main Page Analysis**
   ```
   https://guide-orientation.rnu.tn/ → Extract dropdown options
   ```

2. **Search Form Submission**
   ```
   Select bac type → Submit form → Get search results
   ```

3. **Ramz Link Extraction**
   ```
   Search results table → Extract ramz popup links
   ```

4. **Detailed Page Scraping**
   ```
   ramz popup pages → Extract detailed information
   ```

## 🛠️ Technical Details

### URL Pattern
- Main search: `https://guide-orientation.rnu.tn/ar/dynamique/index_ar.php`
- Detail pages: `https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=XXXXXXX`

### JavaScript Handling
The website uses JavaScript popups for detail pages:
```javascript
PopupCentrer("ar/dynamique/filiere.php?id=410104", 800, 750, "toolbar=no...")
```

### Arabic Text Extraction
Uses regex patterns to extract Arabic labels:
- `الجامعة` (University)
- `المؤسسة` (Institution)  
- `الشعبة / الإجازة` (Specialization)
- etc.

## 📈 Expected Results

Based on your previous runs:
- **~3,161 total ramz links** across all bac types
- **Multiple baccalaureate types** (آداب, علوم, تقني, etc.)
- **Comprehensive coverage** of all Tunisian universities

## 🚨 Important Notes

### Ethical Scraping
- Respects robots.txt
- Implements rate limiting
- Uses appropriate user agents
- Includes error handling

### Rate Limiting
- 1-2 second delays between requests
- Adjustable based on server response
- Parallel workers with distributed delays

### Error Handling
- Robust exception handling
- Detailed logging
- Failed request tracking
- Retry mechanisms

## 🎛️ Configuration

You can customize the scraper behavior:

```python
scraper = UniversityGuideScraper(
    max_workers=8,    # Number of parallel workers
    delay=1           # Delay between requests (seconds)
)
```

## 📋 Sample Output

A complete record looks like this:

```csv
ramz_code,university,governorate,institution,specialization,last_oriented_score_2024,...
10101,جامعة تونس,تونس,كلية العلوم الإنسانية والإجتماعية بتونس,الإجازة في العربية,97.8750,...
```

## 🔄 Running the Complete Scraper

1. **Start with test**: `python test_single_ramz.py`
2. **Verify structure**: Check the generated CSV sample
3. **Run full scraper**: `python university_scraper.py`
4. **Monitor progress**: Watch the console output
5. **Check results**: Look in the `data/` folder

The scraper will save timestamped files:
- `complete_university_data_YYYYMMDD_HHMMSS.json`
- `complete_university_data_YYYYMMDD_HHMMSS.csv`

## 🤝 Contributing

Feel free to improve the scraper by:
- Adding more data fields
- Improving Arabic text extraction
- Optimizing performance
- Adding data analysis features

## ⚠️ Disclaimer

This tool is for educational and research purposes. Always respect the website's terms of service and rate limits.
