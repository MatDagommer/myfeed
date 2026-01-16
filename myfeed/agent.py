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

class NewsletterState(BaseModel):
    topics: List[str]
    raw_articles: List[Dict[str, Any]] = []
    filtered_articles: List[NewsItem] = []
    raw_papers: List[Dict[str, Any]] = []
    filtered_papers: List[PaperItem] = []
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
        papers = []
        
        for topic in state.topics:
            try:
                # Construct Google Scholar search URL
                search_query = topic.replace(" ", "+")
                scholar_url = f"https://scholar.google.com/scholar?q={search_query}&hl=en&as_sdt=0%2C5&as_vis=1"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(scholar_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                papers = []

                for el in soup.select(".gs_r"):
                    try:
                        # Extract required fields with safety checks
                        title_elem = el.select(".gs_rt")
                        if not title_elem:
                            continue
                        
                        title = title_elem[0].text
                        print(title)
                        
                        # Get title link and id safely
                        title_link_elem = el.select(".gs_rt a")
                        title_link = title_link_elem[0]["href"] if title_link_elem else ""
                        paper_id = title_link_elem[0].get("id", "") if title_link_elem else ""
                        
                        # Get author/publication info
                        displayed_link_elem = el.select(".gs_a")
                        displayed_link = displayed_link_elem[0].text if displayed_link_elem else ""
                        
                        # Get snippet
                        snippet_elem = el.select(".gs_rs")
                        snippet = snippet_elem[0].text.replace("\n", "") if snippet_elem else ""
                        
                        # Get citation info (optional)
                        cited_elem = el.select(".gs_nph+ a")
                        cited_by_count = cited_elem[0].text if cited_elem else ""
                        cited_link = "https://scholar.google.com" + cited_elem[0]["href"] if cited_elem else ""
                        
                        # Get versions info (optional)
                        versions_elem = el.select("a~ a+ .gs_nph")
                        versions_count = versions_elem[0].text if versions_elem else ""
                        versions_link = "https://scholar.google.com" + versions_elem[0]["href"] if versions_elem and versions_count else ""
                        
                        papers.append({
                            "title": title,
                            "title_link": title_link,
                            "id": paper_id,
                            "displayed_link": displayed_link,
                            "snippet": snippet,
                            "cited_by_count": cited_by_count,
                            "cited_link": cited_link,
                            "versions_count": versions_count,
                            "versions_link": versions_link,
                        })
                    except Exception as e:
                        print(f"Error processing paper element: {e}")
                        continue
        
                for i in range(len(papers)):
                    papers[i] = {key: value for key, value in papers[i].items() if value != "" and value is not None}
        
                print(papers)
                        
            except Exception as e:
                print(f"Error scraping papers for topic '{topic}': {e}")
                traceback.print_exc()
                continue
        
        state.raw_papers = papers
        return state

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
        filter_prompt = ChatPromptTemplate.from_template("""
        You are an academic newsletter curator. Given these topics of interest: {topics}
        
        Rate the relevance of this research paper on a scale of 0-10 and provide a concise academic summary.
        
        Paper Title: {title}
        Authors: {authors}
        Year: {year}
        Abstract/Summary: {summary}
        Citations: {citations}
        
        Respond in JSON format:
        {{
            "relevance_score": <score>,
            "summary": "<academic_summary>",
            "reasoning": "<brief_reasoning>"
        }}
        """)
        
        filtered_papers = []
        
        for paper in state.raw_papers:
            try:
                response = self.llm.invoke(filter_prompt.format(
                    topics=", ".join(state.topics),
                    title=paper["title"],
                    authors=paper["authors"],
                    year=paper["year"],
                    summary=paper["summary"],
                    citations=paper["citations"]
                ))
                
                print(f"LLM Response for paper '{paper['title'][:50]}...': {response.content}")
                
                if not response.content or not response.content.strip():
                    print(f"Warning: Empty response from LLM for paper: {paper['title']}")
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
                    filtered_papers.append(PaperItem(
                        title=paper["title"],
                        authors=paper["authors"],
                        summary=result["summary"],
                        url=paper["url"],
                        year=paper["year"],
                        citations=paper["citations"],
                        relevance_score=result["relevance_score"]
                    ))
            except Exception as e:
                print(f"Error filtering paper: {e}")
                traceback.print_exc()
                continue
        
        # Sort by relevance score
        filtered_papers.sort(key=lambda x: x.relevance_score, reverse=True)
        state.filtered_papers = filtered_papers[:5]  # Top 5 papers
        
        return state

    def _generate_newsletter(self, state: NewsletterState) -> NewsletterState:
        newsletter_prompt = ChatPromptTemplate.from_template("""
        Create an engaging newsletter for these topics: {topics}
        
        Today's date: {date}
        
        Use the following curated content to create a newsletter with:
        1. A catchy subject line
        2. A brief introduction
        3. A "Latest News" section with the curated articles
        4. A "Recent Papers" section with the academic papers
        5. For each article/paper: title, summary, and link
        6. A closing note
        
        News Articles:
        {articles}
        
        Academic Papers:
        {papers}
        
        Make it professional but engaging, suitable for email format. Clearly separate the news and papers sections.
        """)
        
        articles_text = ""
        for i, article in enumerate(state.filtered_articles, 1):
            articles_text += f"""
{i}. **{article.title}** (Score: {article.relevance_score})
   Source: {article.source}
   Summary: {article.summary}
   URL: {article.url}
   
"""
        
        papers_text = ""
        for i, paper in enumerate(state.filtered_papers, 1):
            papers_text += f"""
{i}. **{paper.title}** (Score: {paper.relevance_score})
   Authors: {paper.authors}
   Year: {paper.year}
   Citations: {paper.citations}
   Summary: {paper.summary}
   URL: {paper.url}
   
"""
        
        response = self.llm.invoke(newsletter_prompt.format(
            topics=", ".join(state.topics),
            date=datetime.now().strftime("%B %d, %Y"),
            articles=articles_text,
            papers=papers_text
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
