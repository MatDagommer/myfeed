# Notebooks

This directory contains marimo notebooks for testing and debugging the myfeed functionality.

## test_scrape_papers.py

Interactive notebook for testing the `_scrape_papers` method from NewsAgent.

### Features
- Tests scraping with "AI" and "ADME" topics
- Displays detailed paper information
- Shows raw data structure for debugging
- Provides statistics and analysis
- Makes real HTTP requests to Google Scholar

### Running the notebook

#### Interactive mode (recommended)
```bash
cd notebooks
uv run marimo edit test_scrape_papers.py
```
This will open the notebook in your browser where you can:
- Run cells interactively
- Modify parameters
- Debug step by step
- See real-time results

#### Headless mode (for CI/testing)
```bash
cd notebooks  
uv run marimo run test_scrape_papers.py --headless
```
⚠️ Note: This makes real HTTP requests and may be slow or fail due to rate limiting.

### What you'll see
1. **Setup**: Import and initialize NewsAgent
2. **State Creation**: Create NewsletterState with topics
3. **Scraping**: Run the _scrape_papers method
4. **Results Display**: View formatted paper details  
5. **Raw Data**: Inspect the complete data structure
6. **Analysis**: Statistics and categorization

### Debugging Tips
- Check network connectivity if scraping fails
- Google Scholar may rate limit requests
- Modify topics in the state creation cell to test different searches
- Examine specific papers by indexing into `result_state.raw_papers`
- Use the raw data section to understand field names and structure

### Expected Output
The notebook will show papers related to AI and ADME topics, including:
- Paper titles and links
- Author information
- Abstracts/snippets
- Citation counts
- Version links
- Categorization by topic
- Citation statistics