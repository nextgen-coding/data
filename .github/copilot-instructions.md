<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Web Scraping Project Instructions

This project focuses on comprehensive web scraping and analysis of the Tunisian University Orientation website (https://guide-orientation.rnu.tn/).

## Project Goals
- Analyze website structure and identify all data sources
- Extract information about universities, programs, requirements, and guidance
- Provide detailed analysis of content organization
- Create reusable scraping tools for similar educational websites

## Key Components
- `website_analyzer.py`: Main analysis tool for understanding website structure
- `scrapers/`: Directory containing specialized scrapers for different data types
- `data/`: Directory for storing scraped data and analysis results
- `analysis/`: Tools for data analysis and visualization
- `notebooks/`: Jupyter notebooks for interactive exploration

## Best Practices
- Always respect robots.txt and rate limiting
- Use proper user agents and headers to avoid being blocked
- Implement error handling and retry mechanisms
- Store data in structured formats (JSON, CSV)
- Document all findings and methodologies
