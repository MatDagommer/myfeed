import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    import os
    import json

    # Add the parent directory to Python path to import myfeed
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from myfeed.agent import NewsAgent, NewsletterState

    print("Imports successful!")
    return NewsAgent, NewsletterState, json


@app.cell
def _(NewsAgent):
    # Initialize NewsAgent with dummy API key (we won't use LLM functionality)
    news_agent = NewsAgent(openai_api_key="dummy-key-for-testing")
    print("NewsAgent initialized")
    return (news_agent,)


@app.cell
def _(NewsletterState):
    # Create newsletter state with AI and ADME topics
    state = NewsletterState(topics=["AI", "ADME"])
    print(f"Created state with topics: {state.topics}")
    return (state,)


@app.cell
def _(news_agent, state):
    # Run the _scrape_papers method
    print("Running _scrape_papers method...")
    print("This will make HTTP requests to the OpenAlex API")

    try:
        result_state = news_agent._scrape_papers(state)
        print(f"Scraping completed! Found {len(result_state.raw_papers)} papers")
        scrape_success = True
    except Exception as e:
        print(f"Error during scraping: {e}")
        result_state = state  # Use original state
        scrape_success = False

    return result_state, scrape_success


@app.cell
def _(result_state, scrape_success):
    # Display results
    if scrape_success and result_state.raw_papers:
        print(f"Total papers found: {len(result_state.raw_papers)}")
        print("\n" + "="*80)
        print("PAPER DETAILS")
        print("="*80)

        for i, _paper in enumerate(result_state.raw_papers, 1):
            print(f"\nPaper {i}:")
            title = _paper.get('title', 'N/A')
            print(f"   Title: {title[:100]}..." if len(title) > 100 else f"   Title: {title}")
            print(f"   URL: {_paper.get('url', 'N/A')}")
            print(f"   Authors: {_paper.get('authors', 'N/A')}")
            summary = _paper.get('summary', 'N/A')
            print(f"   Abstract: {summary[:150]}..." if len(summary) > 150 else f"   Abstract: {summary}")
            print(f"   Year: {_paper.get('year', 'N/A')}")
            print(f"   Citations: {_paper.get('citations', 'N/A')}")
            print(f"   Source: {_paper.get('source', 'N/A')}")
    else:
        print("No papers found or scraping failed")

    return


@app.cell
def _(json, result_state, scrape_success):
    # Raw data inspection
    if scrape_success and result_state.raw_papers:
        print("\n" + "="*80)
        print("RAW DATA STRUCTURE")
        print("="*80)

        # Show the first paper's complete structure
        if result_state.raw_papers:
            print("First paper's complete data structure:")
            print(json.dumps(result_state.raw_papers[0], indent=2, ensure_ascii=False))

        print(f"\nAll paper keys found across all results:")
        all_keys = set()
        for _paper in result_state.raw_papers:
            all_keys.update(_paper.keys())
        print(sorted(list(all_keys)))
    else:
        print("No raw data to display")

    return


@app.cell
def _(result_state, scrape_success):
    # Statistics and analysis
    if scrape_success and result_state.raw_papers:
        print("\n" + "="*80)
        print("STATISTICS & ANALYSIS")
        print("="*80)

        # Count papers by topic
        papers_by_topic = {}
        for _paper_item in result_state.raw_papers:
            topic = _paper_item.get('topics', 'Unknown')
            if topic not in papers_by_topic:
                papers_by_topic[topic] = []
            papers_by_topic[topic].append(_paper_item)

        print(f"Paper count by topic:")
        for topic, papers in papers_by_topic.items():
            print(f"   {topic}: {len(papers)} papers")

        # Show citation statistics
        citations = []
        for _paper_citation in result_state.raw_papers:
            cited_text = _paper_citation.get('citations', '0')
            try:
                num = int(cited_text)
                citations.append(num)
            except (ValueError, TypeError):
                pass

        if citations:
            print(f"\nCitation statistics:")
            print(f"   Papers with citation data: {len(citations)}")
            print(f"   Average citations: {sum(citations)/len(citations):.1f}")
            print(f"   Most cited: {max(citations)}")
            print(f"   Least cited: {min(citations)}")

        # Show year distribution
        years = []
        for _paper_year in result_state.raw_papers:
            year_text = _paper_year.get('year', '')
            try:
                year = int(year_text)
                years.append(year)
            except (ValueError, TypeError):
                pass

        if years:
            print(f"\nPublication year range:")
            print(f"   Newest: {max(years)}")
            print(f"   Oldest: {min(years)}")
    else:
        print("No data for analysis")

    return


@app.cell
def _():
    # Instructions for debugging
    print("="*80)
    print("DEBUGGING TIPS")
    print("="*80)
    print("""
    This notebook demonstrates the _scrape_papers functionality from NewsAgent.

    What it does:
    - Fetches papers from the OpenAlex API for 'AI' and 'ADME' topics
    - Extracts title, authors, abstract, year, citation count, and DOI/URL
    - Sorts results by citation count (most cited first)
    - Filters out empty values from the results

    For debugging:
    1. Check the 'Raw Data Structure' section to see exact field names
    2. Look at 'Statistics & Analysis' for citation and year distributions
    3. Monitor network errors in the console output
    4. Modify the topics in the state creation cell to test different searches

    Notes:
    - OpenAlex API is free and does not require authentication
    - Rate limit: 100,000 requests/day, 10 requests/second
    - The 'mailto' parameter is included for polite pool access
    - Abstract is reconstructed from OpenAlex's inverted index format

    To modify:
    - Change topics in the state creation cell
    - Add error handling or logging as needed
    - Examine specific papers by indexing into result_state.raw_papers
    """)
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
