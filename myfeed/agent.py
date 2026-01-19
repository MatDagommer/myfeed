from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import feedparser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import json
import traceback
from datetime import datetime

class NewsItem(BaseModel):
    title: str
    summary: str
    url: str
    source: str
    relevance_score: float

class PaperItem(BaseModel):
    title: str
    authors: str
    summary: str
    url: str
    year: str
    citations: str
    relevance_score: float
    publication_date: str = ""  # Full publication date (YYYY-MM-DD)

class NewsletterState(BaseModel):
    topics: List[str]
    raw_articles: List[Dict[str, Any]] = []
    filtered_articles: List[NewsItem] = []
    raw_papers: List[Dict[str, Any]] = []
    filtered_papers: List[PaperItem] = []
    today_papers: List[PaperItem] = []  # Papers from today
    recent_papers: List[PaperItem] = []  # Papers from last 2 weeks
    newsletter_content: str = ""

class NewsAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=openai_api_key,
            temperature=0.3
        )
        self.graph = self._create_graph()
        self.mcp_client = None
        self.agent = None

    def _scrape_news(self, state: NewsletterState) -> NewsletterState:
        sources = [
            "https://feeds.feedburner.com/oreilly/radar",
            "https://techcrunch.com/feed/",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.wired.com/feed/rss",
            "https://feeds.feedburner.com/venturebeat/SZYF",
        ]
        
        articles = []
        
        for source_url in sources:
            try:
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:5]:  # Get top 5 from each source
                    articles.append({
                        "title": entry.title,
                        "summary": getattr(entry, 'summary', ''),
                        "url": entry.link,
                        "source": feed.feed.title,
                        "published": getattr(entry, 'published', ''),
                        "content": self._extract_content(entry.link)
                    })
            except Exception as e:
                print(f"Error scraping {source_url}: {e}")
                traceback.print_exc()
                continue
        
        state.raw_articles = articles
        return state

    def _extract_content(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:1000]  # Limit content length
        except Exception as e:
            print(f"Error extracting content from URL: {e}")
            traceback.print_exc()
            return ""

    def _scrape_papers(self, state: NewsletterState) -> NewsletterState:
        """Scrape papers from OpenAlex API for given topics."""
        all_papers = []

        for topic in state.topics:
            try:
                # Construct OpenAlex API URL
                openalex_url = "https://api.openalex.org/works"
                params = {
                    "search": topic,
                    "per_page": 10,  # Get top 10 results per topic
                    "sort": "publication_date:desc",  # Sort by most recent
                    "mailto": "myfeed@example.com",  # Polite pool
                }

                headers = {
                    'User-Agent': 'MyFeed/1.0 (mailto:myfeed@example.com)'
                }

                response = requests.get(openalex_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                for work in data.get("results", []):
                    try:
                        # Extract title
                        title = work.get("title") or work.get("display_name", "")
                        if not title:
                            continue

                        print(title)

                        # Extract authors
                        authorships = work.get("authorships", [])
                        authors = ", ".join([
                            a.get("author", {}).get("display_name", "")
                            for a in authorships[:5]  # Limit to first 5 authors
                            if a.get("author", {}).get("display_name")
                        ])
                        if len(authorships) > 5:
                            authors += " et al."

                        # Extract abstract from inverted index
                        abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

                        # Extract URL - prefer DOI, then landing page
                        doi = work.get("doi", "")
                        primary_location = work.get("primary_location") or {}
                        landing_page = primary_location.get("landing_page_url", "")
                        url = doi if doi else landing_page

                        # Extract other metadata
                        openalex_id = work.get("id", "")
                        publication_year = str(work.get("publication_year", ""))
                        publication_date = work.get("publication_date", "")
                        cited_by_count = str(work.get("cited_by_count", 0))

                        # Get source/journal info
                        source = primary_location.get("source") or {}
                        source_name = source.get("display_name", "")

                        paper = {
                            "title": title,
                            "url": url,
                            "id": openalex_id,
                            "authors": authors if authors else source_name,
                            "summary": abstract,
                            "year": publication_year,
                            "publication_date": publication_date,
                            "citations": cited_by_count,
                            "source": source_name,
                            "topics": topic
                        }

                        # Filter out empty values
                        paper = {k: v for k, v in paper.items() if v}
                        all_papers.append(paper)

                    except Exception as e:
                        print(f"Error processing paper: {e}")
                        continue

                print(f"Found {len(data.get('results', []))} papers for topic '{topic}'")

            except Exception as e:
                print(f"Error scraping papers for topic '{topic}': {e}")
                traceback.print_exc()
                continue

        state.raw_papers = all_papers
        return state

    def _reconstruct_abstract(self, inverted_index: dict) -> str:
        """Reconstruct abstract text from OpenAlex inverted index format."""
        if not inverted_index:
            return ""

        try:
            # Build list of (position, word) tuples
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))

            # Sort by position and join
            word_positions.sort(key=lambda x: x[0])
            abstract = " ".join([word for _, word in word_positions])

            # Limit length
            return abstract[:1000] if len(abstract) > 1000 else abstract
        except Exception:
            return ""

    def _filter_articles(self, state: NewsletterState) -> NewsletterState:
        filter_prompt = ChatPromptTemplate.from_template("""
        You are a newsletter curator. Given these topics of interest: {topics}
        
        Rate the relevance of this article on a scale of 0-10 and provide a concise summary.
        
        Article Title: {title}
        Article Summary: {summary}
        Article Content: {content}
        
        Respond in JSON format:
        {{
            "relevance_score": <score>,
            "summary": "<your_summary>",
            "reasoning": "<brief_reasoning>"
        }}
        """)
        
        filtered_articles = []
        
        for article in state.raw_articles:
            try:
                response = self.llm.invoke(filter_prompt.format(
                    topics=", ".join(state.topics),
                    title=article["title"],
                    summary=article["summary"],
                    content=article["content"]
                ))
                
                print(f"LLM Response for article '{article['title'][:50]}...': {response.content}")
                
                if not response.content or not response.content.strip():
                    print(f"Warning: Empty response from LLM for article: {article['title']}")
                    continue
                
                # Try to extract JSON from the response if it's wrapped in markdown or other text
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON. Raw content: {repr(response.content)}")
                    continue
                
                if result["relevance_score"] >= 6:  # Only include relevant articles
                    filtered_articles.append(NewsItem(
                        title=article["title"],
                        summary=result["summary"],
                        url=article["url"],
                        source=article["source"],
                        relevance_score=result["relevance_score"]
                    ))
            except Exception as e:
                print(f"Error filtering article: {e}")
                traceback.print_exc()
                continue
        
        # Sort by relevance score
        filtered_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        state.filtered_articles = filtered_articles[:10]  # Top 10 articles
        
        return state

    def _filter_papers(self, state: NewsletterState) -> NewsletterState:
        from datetime import datetime, timedelta

        filter_prompt = ChatPromptTemplate.from_template("""
        You are an academic newsletter curator. Given these topics of interest: {topics}

        Rate the relevance of this research paper on a scale of 0-10 and provide a concise academic summary.

        Paper Title: {title}
        Authors: {authors}
        Abstract/Summary: {summary}
        Citations: {citations}

        Respond in JSON format:
        {{
            "relevance_score": <score>,
            "summary": "<academic_summary>",
            "reasoning": "<brief_reasoning>"
        }}
        """)

        # Calculate date ranges
        today = datetime.now().date()
        two_weeks_ago = today - timedelta(days=14)

        today_papers = []
        recent_papers = []
        all_filtered_papers = []

        for paper in state.raw_papers:
            try:
                # Use .get() for safer access to optional fields
                title = paper.get("title", "")
                authors = paper.get("authors", "Unknown")
                summary = paper.get("summary", "")
                citations = paper.get("citations", "0")
                url = paper.get("url", "")
                year = paper.get("year", "")
                publication_date = paper.get("publication_date", "")

                if not title:
                    continue

                response = self.llm.invoke(filter_prompt.format(
                    topics=", ".join(state.topics),
                    title=title,
                    authors=authors,
                    summary=summary,
                    citations=citations
                ))

                print(f"LLM Response for paper '{title[:50]}...': {response.content}")

                if not response.content or not response.content.strip():
                    print(f"Warning: Empty response from LLM for paper: {title}")
                    continue

                # Try to extract JSON from the response if it's wrapped in markdown or other text
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON. Raw content: {repr(response.content)}")
                    continue

                if result["relevance_score"] >= 6:  # Only include relevant papers
                    paper_item = PaperItem(
                        title=title,
                        authors=authors,
                        summary=result["summary"],
                        url=url,
                        year=year,
                        citations=citations,
                        relevance_score=result["relevance_score"],
                        publication_date=publication_date
                    )

                    # Categorize by date
                    if publication_date:
                        try:
                            pub_date = datetime.strptime(publication_date, "%Y-%m-%d").date()
                            if pub_date == today:
                                today_papers.append(paper_item)
                            elif pub_date >= two_weeks_ago:
                                recent_papers.append(paper_item)
                        except ValueError:
                            # If date parsing fails, add to recent papers
                            recent_papers.append(paper_item)
                    else:
                        # If no date, add to recent papers
                        recent_papers.append(paper_item)

                    all_filtered_papers.append(paper_item)
            except Exception as e:
                print(f"Error filtering paper: {e}")
                traceback.print_exc()
                continue

        # Sort by relevance score
        today_papers.sort(key=lambda x: x.relevance_score, reverse=True)
        recent_papers.sort(key=lambda x: x.relevance_score, reverse=True)

        # Keep top 1-3 papers for each category
        state.today_papers = today_papers[:3]
        state.recent_papers = recent_papers[:3]

        # Keep all filtered papers for backwards compatibility
        all_filtered_papers.sort(key=lambda x: x.relevance_score, reverse=True)
        state.filtered_papers = all_filtered_papers[:5]

        return state

    def _generate_newsletter(self, state: NewsletterState) -> NewsletterState:
        newsletter_prompt = ChatPromptTemplate.from_template("""
        Create an engaging newsletter for these topics: {topics}

        Today's date: {date}

        Use the following curated content to create a newsletter with:
        1. A catchy subject line
        2. A brief introduction
        3. A "Latest News" section with the curated articles
        4. A "Today's Papers" section with papers published today (if any)
        5. A "Recent Papers (Last 2 Weeks)" section with papers from the last two weeks
        6. For each article/paper: title, summary, and link
        7. A closing note

        News Articles:
        {articles}

        Today's Papers (Published Today):
        {today_papers}

        Recent Papers (Last 2 Weeks):
        {recent_papers}

        Make it professional but engaging, suitable for email format. Clearly separate all sections. If there are no papers for today, mention that there are no new papers published today and focus on the recent papers section.
        """)

        articles_text = ""
        for i, article in enumerate(state.filtered_articles, 1):
            articles_text += f"""
{i}. **{article.title}** (Score: {article.relevance_score})
   Source: {article.source}
   Summary: {article.summary}
   [Read more]({article.url})

"""

        today_papers_text = ""
        if state.today_papers:
            for i, paper in enumerate(state.today_papers, 1):
                today_papers_text += f"""
{i}. **{paper.title}** (Score: {paper.relevance_score})
   Authors: {paper.authors}
   Year: {paper.year}
   Citations: {paper.citations}
   Summary: {paper.summary}
   [Read paper]({paper.url})

"""
        else:
            today_papers_text = "No papers published today.\n"

        recent_papers_text = ""
        if state.recent_papers:
            for i, paper in enumerate(state.recent_papers, 1):
                recent_papers_text += f"""
{i}. **{paper.title}** (Score: {paper.relevance_score})
   Authors: {paper.authors}
   Year: {paper.year}
   Citations: {paper.citations}
   Summary: {paper.summary}
   [Read paper]({paper.url})

"""
        else:
            recent_papers_text = "No recent papers found in the last 2 weeks.\n"

        response = self.llm.invoke(newsletter_prompt.format(
            topics=", ".join(state.topics),
            date=datetime.now().strftime("%B %d, %Y"),
            articles=articles_text,
            today_papers=today_papers_text,
            recent_papers=recent_papers_text
        ))

        state.newsletter_content = response.content
        return state

    def _create_graph(self) -> StateGraph:
        workflow = StateGraph(NewsletterState)
        
        workflow.add_node("scrape_news", self._scrape_news)
        workflow.add_node("scrape_papers", self._scrape_papers)
        workflow.add_node("filter_articles", self._filter_articles)
        workflow.add_node("filter_papers", self._filter_papers)
        workflow.add_node("generate_newsletter", self._generate_newsletter)
        
        workflow.set_entry_point("scrape_news")
        workflow.add_edge("scrape_news", "scrape_papers")
        workflow.add_edge("scrape_papers", "filter_articles")
        workflow.add_edge("filter_articles", "filter_papers")
        workflow.add_edge("filter_papers", "generate_newsletter")
        workflow.add_edge("generate_newsletter", END)
        
        return workflow.compile()

    def generate_newsletter(self, topics: List[str]) -> str:
        initial_state = NewsletterState(topics=topics)
        result = self.graph.invoke(initial_state)
        
        # Handle both dict and NewsletterState return types
        if isinstance(result, dict):
            return result.get("newsletter_content", "")
        else:
            return result.newsletter_content
