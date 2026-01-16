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

    print("✅ Imports successful!")
    return NewsAgent, NewsletterState, json


@app.cell
def _(NewsAgent):
    # Initialize NewsAgent with dummy API key (we won't use LLM functionality)
    news_agent = NewsAgent(openai_api_key="dummy-key-for-testing")
    print("✅ NewsAgent initialized")
    return (news_agent,)


@app.cell
def _(NewsletterState):
    # Create newsletter state with AI and ADME topics
    state = NewsletterState(topics=["AI", "ADME"])
    print(f"📝 Created state with topics: {state.topics}")
    return (state,)


@app.cell
def _(news_agent, state):
    # Run the _scrape_papers method
    print("🔍 Running _scrape_papers method...")
    print("⚠️  This will make real HTTP requests to Google Scholar")

    try:
        result_state = news_agent._scrape_papers(state)
        print(f"✅ Scraping completed! Found {len(result_state.raw_papers)} papers")
        scrape_success = True
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        result_state = state  # Use original state
        scrape_success = False

    return result_state, scrape_success


@app.cell
def _(result_state, scrape_success):
    # Display results
    if scrape_success and result_state.raw_papers:
        print(f"📊 Total papers found: {len(result_state.raw_papers)}")
        print("\n" + "="*80)
        print("📋 PAPER DETAILS")
        print("="*80)

        for i, _paper in enumerate(result_state.raw_papers, 1):
            print(f"\n📄 Paper {i}:")
            print(f"   📌 Title: {_paper.get('title', 'N/A')[:100]}...")
            print(f"   🔗 URL: {_paper.get('title_link', 'N/A')}")
            print(f"   👥 Authors: {_paper.get('displayed_link', 'N/A')}")
            print(f"   📝 Snippet: {_paper.get('snippet', 'N/A')[:150]}...")
            print(f"   📊 Citations: {_paper.get('cited_by_count', 'N/A')}")
            print(f"   🔄 Versions: {_paper.get('versions_count', 'N/A')}")
    else:
        print("❌ No papers found or scraping failed")

    return


@app.cell
def _(json, result_state, scrape_success):
    # Raw data inspection
    if scrape_success and result_state.raw_papers:
        print("\n" + "="*80)
        print("🔍 RAW DATA STRUCTURE")
        print("="*80)

        # Show the first paper's complete structure
        if result_state.raw_papers:
            print("First paper's complete data structure:")
            print(json.dumps(result_state.raw_papers[0], indent=2, ensure_ascii=False))

        print(f"\n📈 All paper keys found across all results:")
        all_keys = set()
        for _paper in result_state.raw_papers:
            all_keys.update(_paper.keys())
        print(sorted(list(all_keys)))
    else:
        print("❌ No raw data to display")

    return


@app.cell
def _(result_state, scrape_success):
    # Statistics and analysis
    if scrape_success and result_state.raw_papers:
        print("\n" + "="*80)
        print("📊 STATISTICS & ANALYSIS")
        print("="*80)

        # Count papers by topic (rough estimation based on content)
        ai_papers = []
        adme_papers = []
        other_papers = []

        for _paper_item in result_state.raw_papers:
            title = _paper_item.get('title', '').lower()
            snippet = _paper_item.get('snippet', '').lower()
            content = f"{title} {snippet}"

            if 'ai' in content or 'artificial intelligence' in content or 'machine learning' in content:
                ai_papers.append(_paper_item)
            elif 'adme' in content or 'absorption' in content or 'distribution' in content or 'metabolism' in content or 'excretion' in content:
                adme_papers.append(_paper_item)
            else:
                other_papers.append(_paper_item)

        print(f"📊 Paper categorization (rough estimation):")
        print(f"   🤖 AI-related: {len(ai_papers)}")
        print(f"   💊 ADME-related: {len(adme_papers)}")
        print(f"   🔍 Other/Mixed: {len(other_papers)}")

        # Show citation patterns
        citations = []
        for _paper_citation in result_state.raw_papers:
            cited_text = _paper_citation.get('cited_by_count', '')
            if 'Cited by' in cited_text:
                try:
                    num = int(cited_text.split('Cited by')[1].strip())
                    citations.append(num)
                except:
                    pass

        if citations:
            print(f"\n📈 Citation statistics:")
            print(f"   📊 Papers with citation data: {len(citations)}")
            print(f"   📈 Average citations: {sum(citations)/len(citations):.1f}")
            print(f"   🏆 Most cited: {max(citations)}")
            print(f"   📉 Least cited: {min(citations)}")
    else:
        print("❌ No data for analysis")

    return


@app.cell
def _():
    # Instructions for debugging
    print("="*80)
    print("🛠️  DEBUGGING TIPS")
    print("="*80)
    print("""
    This notebook demonstrates the _scrape_papers functionality from NewsAgent.

    🔍 What it does:
    - Scrapes Google Scholar for papers related to 'AI' and 'ADME' topics
    - Extracts title, authors, abstract, citation count, and links
    - Filters out empty values from the results

    🛠️  For debugging:
    1. Check the 'Raw Data Structure' section to see exact field names
    2. Look at 'Statistics & Analysis' for content categorization
    3. Monitor network errors in the console output
    4. Modify the topics in the state creation cell to test different searches

    ⚠️  Notes:
    - This makes real HTTP requests to Google Scholar
    - Google Scholar may rate limit or block requests
    - Results may vary based on network conditions
    - Some CSS selectors might fail if Google changes their HTML structure

    🔧 To modify:
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
