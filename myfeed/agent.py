from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import feedparser
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessageGraph
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
from .config import settings

class NewsItem(BaseModel):
    title: str
    summary: str
    url: str
    source: str
    relevance_score: float

class NewsletterState(BaseModel):
    topics: List[str]
    raw_articles: List[Dict[str, Any]] = []
    filtered_articles: List[NewsItem] = []
    newsletter_content: str = ""

class NewsAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.3
        )
        self.graph = self._create_graph()
        self.mcp_client = None
        self.agent = None
    
    async def _initialize_agent(self):
        """Initialize MCP client with available servers"""
        if self.mcp_client is None:
            self.mcp_client = MultiServerMCPClient(
                {
                    "math": {
                        "transport": "stdio",
                        "command": "python",
                        "args": ["/path/to/math_server.py"],
                    },
                    "weather": {
                        "transport": "http",
                        "url": "http://localhost:8000/mcp",
                    }
                }
            )
            
            tools = await self.mcp_client.get_tools()
            self.agent = create_agent(
                "claude-sonnet-4-5-20250929", 
                tools
            )

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
        except:
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
                
                result = json.loads(response.content)
                
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
                continue
        
        # Sort by relevance score
        filtered_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        state.filtered_articles = filtered_articles[:10]  # Top 10 articles
        
        return state

    def _generate_newsletter(self, state: NewsletterState) -> NewsletterState:
        newsletter_prompt = ChatPromptTemplate.from_template("""
        Create an engaging newsletter for these topics: {topics}
        
        Today's date: {date}
        
        Use the following curated articles to create a newsletter with:
        1. A catchy subject line
        2. A brief introduction
        3. Sections organized by topic or theme
        4. For each article: title, summary, and link
        5. A closing note
        
        Articles:
        {articles}
        
        Make it professional but engaging, suitable for email format.
        """)
        
        articles_text = ""
        for i, article in enumerate(state.filtered_articles, 1):
            articles_text += f"""
{i}. **{article.title}** (Score: {article.relevance_score})
   Source: {article.source}
   Summary: {article.summary}
   URL: {article.url}
   
"""
        
        response = self.llm.invoke(newsletter_prompt.format(
            topics=", ".join(state.topics),
            date=datetime.now().strftime("%B %d, %Y"),
            articles=articles_text
        ))
        
        state.newsletter_content = response.content
        return state

    def generate_newsletter(self, topics: List[str]) -> str:
        initial_state = NewsletterState(topics=topics)
        result = self.agent.ainvoke(initial_state)
        return result.newsletter_content
