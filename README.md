# Tunisian University Orientation Guide Scraper

A comprehensive web scraping tool for extracting data from the Tunisian University Orientation website (https://guide-orientation.rnu.tn/).

## 🎯 Project Overview

This project scrapes detailed information about Tunisian universities, institutions, and academic programs including:
- University and institution details
- Program specifications and requirements
- Historical admission scores (2011-2024)
- Baccalaureate requirements
- Geographic distribution information

## 📋 **FINAL DATASET - FOR TEAM MEMBERS**

### 🔥 **Hey Wassim! Check out the complete dataset in `/data-for-wassim/`**

We've successfully scraped and cleaned the complete Tunisia university orientation dataset:

**📁 Files Ready for You:**
- **`data-for-wassim/finale-data.json`** (1.08 MB) - Complete dataset in JSON format
- **`data-for-wassim/finale-data.csv`** (627 KB) - Same data in CSV format for Excel/analysis

**📊 Dataset Summary:**
- ✅ **998 university specialization records** - Complete coverage
- ✅ **Historical scores 2011-2024** - 14 years of admission data
- ✅ **Corrected and validated data** - All scores verified and cleaned
- ✅ **Seven percent field logic** - Proper geographic distribution rules
- ✅ **14 essential fields** - Optimized for analysis

**🗂️ Data Fields (14 total):**
1. `ramz_code` - Specialization identifier 
2. `ramz_id` - Internal ID
3. `ramz_link` - Direct link to specialization
4. `university_id` - University identifier
5. `university_name` - University name (Arabic)
6. `bac_type_id` - Baccalaureate type ID
7. `bac_type_name` - Baccalaureate type (Arabic)
8. `field_of_study` - Academic field
9. `historical_scores` - JSON object with scores 2011-2024
10. `seven_percent` - Geographic distribution rule (yes/no)
11. `table_criteria` - Admission criteria
12. `table_institution` - Institution details
13. `table_location` - Location information
14. `table_specialization` - Specialization details

**🎯 Ready for Analysis:**
- Load into Python with `pandas` or `json`
- Import into Excel/Google Sheets  
- Use for data visualization with `matplotlib`/`seaborn`
- Perfect for machine learning projects

## 📊 Data Structure

### Current Final Dataset Structure (finale-data.json/csv)

The final cleaned dataset contains 14 essential fields per specialization record:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `ramz_code` | String | Specialization code | "22103" |
| `ramz_id` | String | Internal system ID | "122103" |
| `ramz_link` | String | Direct URL to specialization | "https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=122103" |
| `university_id` | String | University identifier | "01" |
| `university_name` | String | University name (Arabic) | "جامعة تونس" |
| `bac_type_id` | String | Baccalaureate type ID | "1" |
| `bac_type_name` | String | Baccalaureate type (Arabic) | "آداب" |
| `field_of_study` | String | Academic field | "الآداب واللغات والمراحل التحضيرية الأدبية" |
| `historical_scores` | Object | Historical admission scores | `{"2011": 0.0, "2012": 0.0, ..., "2024": 137.44}` |
| `seven_percent` | String | Geographic distribution rule | "yes" or "no" |
| `table_criteria` | String | Admission criteria | "FG+ALL" |
| `table_institution` | String | Institution name | "المعهد العالي للغات بتونس" |
| `table_location` | String | Location/City | "تونس" |
| `table_specialization` | String | Specialization details | "الإجازة في الألمانية" |

### Historical Scores Data
- **Years covered**: 2011-2024 (14 years)
- **Score range**: 0.0 - 220.0 (validated range)
- **Format**: JSON object with year as key, score as float value
- **Missing data**: 0.0 for years with no data

### Legacy Data Structure (Old Scraping Attempts)

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

### For Team Members (Quick Start)

**🎯 Wassim & Team - Use the ready datasets:**

1. **Navigate to** `data-for-wassim/` folder
2. **Use** `finale-data.json` (for Python/JavaScript) or `finale-data.csv` (for Excel/R)
3. **Dataset contains** 998 complete university specialization records
4. **Ready for analysis** - no additional processing needed

**Python Quick Load:**
```python
import pandas as pd
import json

# Load CSV
df = pd.read_csv('data-for-wassim/finale-data.csv')
print(f"Dataset shape: {df.shape}")

# Load JSON  
with open('data-for-wassim/finale-data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"Total records: {len(data)}")
```

### For Developers (Full Setup)

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
├── requirements.txt              # Python dependencies
├── README.md                    # This documentation
├── codes.csv                    # Specialization codes for seven_percent logic
├── data/                        # Final clean datasets
│   ├── finale-data.json         # 🔥 MAIN DATASET (998 records)
│   ├── finale-data.csv          # 🔥 MAIN DATASET (CSV format)
│   ├── finale_one.json          # Previous version with extra fields
│   └── finale_one.csv           # Previous version (CSV)
├── data-for-wassim/             # 🎯 TEAM DATASET FOLDER
│   ├── finale-data.json         # 🔥 FOR WASSIM - Latest dataset
│   └── finale-data.csv          # 🔥 FOR WASSIM - CSV format
├── restoration/                 # Backup/restoration files
├── scrapers/                   # Specialized scraper modules
├── analysis/                   # Data analysis tools
├── notebooks/                  # Jupyter notebooks for exploration
├── website_analyzer.py         # Website structure analysis tool
├── clean_finale_data.py        # Data cleaning utilities
├── update_seven_percent_field.py # Field update scripts
└── .github/
    └── copilot-instructions.md  # Coding guidelines
```

## 🎯 **Dataset Summary for Analysis**

### � What's in the Dataset?

- **Total Records:** 998 university specializations
- **Universities Covered:** All major Tunisian universities  
- **Historical Data:** 14 years (2011-2024) of admission scores
- **Geographic Coverage:** Complete national coverage
- **Data Quality:** Validated and cleaned scores (0-220 range)

### 🔍 Key Analysis Opportunities

1. **Trend Analysis:** Track admission score evolution over 14 years
2. **University Comparison:** Compare admission requirements across institutions
3. **Geographic Distribution:** Analyze seven_percent field patterns
4. **Field of Study Analysis:** Compare different academic domains
5. **Predictive Modeling:** Forecast future admission trends

### 📊 Score Distribution Stats
- **Valid Score Range:** 0.0 - 220.0
- **Missing Data:** Represented as 0.0
- **Years with Most Data:** 2020-2024
- **Specializations with seven_percent="no":** 321 records (32.2%)
- **Specializations with seven_percent="yes":** 677 records (67.8%)

---

## 🔧 Development & Scraping Documentation

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

### 🔥 Final Dataset (data-for-wassim/)

**📁 finale-data.json** (1.08 MB)
- Complete dataset with 998 records
- Historical scores as nested JSON objects
- Perfect for Python/JavaScript analysis
- UTF-8 encoded for proper Arabic text

**📁 finale-data.csv** (627 KB)  
- Same data in tabular format
- Historical scores as JSON strings in single column
- Ready for Excel, R, or spreadsheet analysis
- UTF-8 encoded for proper Arabic display

### Sample Record Structure

**JSON Format:**
```json
{
  "ramz_code": "22103",
  "ramz_id": "122103", 
  "ramz_link": "https://guide-orientation.rnu.tn/ar/dynamique/filiere.php?id=122103",
  "university_id": "01",
  "university_name": "جامعة تونس",
  "bac_type_id": "1",
  "bac_type_name": "آداب",
  "field_of_study": "الآداب واللغات والمراحل التحضيرية الأدبية",
  "historical_scores": {
    "2011": 0.0,
    "2012": 0.0,
    "2013": 0.0,
    "2024": 137.4415
  },
  "seven_percent": "yes",
  "table_criteria": "FG+ALL",
  "table_institution": "المعهد العالي للغات بتونس", 
  "table_location": "تونس",
  "table_specialization": "الإجازة في الألمانية"
}
```

### Legacy Formats

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
