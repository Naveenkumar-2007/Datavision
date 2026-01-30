"""
Web Scraper MCP Tool - FREE
============================

A free web scraping tool that can:
1. Scrape webpage content
2. Extract structured data (tables, lists)
3. Search the web (using free DuckDuckGo)
4. Get news headlines

NO API KEYS REQUIRED - uses free public services.
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin
import asyncio

# These are standard library + already installed packages
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# User agent to avoid blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


@dataclass
class ScrapedPage:
    """Result from scraping a webpage"""
    url: str
    title: str
    text_content: str
    tables: List[Dict[str, Any]]
    links: List[Dict[str, str]]
    metadata: Dict[str, Any]


@dataclass 
class SearchResult:
    """A single search result"""
    title: str
    url: str
    snippet: str


class WebScraperMCP:
    """
    Free web scraping MCP tool.
    
    No API keys required - uses public web services.
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def scrape_url(self, url: str) -> ScrapedPage:
        """
        Scrape content from a URL.
        
        Returns structured content including text, tables, and links.
        """
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Get title
            title = soup.title.string if soup.title else ""
            
            # Get main text content
            text_content = soup.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)
            
            # Extract tables
            tables = []
            for table in soup.find_all('table')[:5]:  # Limit to 5 tables
                table_data = self._parse_table(table)
                if table_data:
                    tables.append(table_data)
            
            # Extract links
            links = []
            for a in soup.find_all('a', href=True)[:20]:  # Limit to 20 links
                href = a['href']
                if href.startswith('http'):
                    links.append({
                        "text": a.get_text(strip=True),
                        "url": href
                    })
                elif href.startswith('/'):
                    links.append({
                        "text": a.get_text(strip=True),
                        "url": urljoin(url, href)
                    })
            
            # Get metadata
            metadata = {}
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                metadata['description'] = meta_desc.get('content', '')
            
            return ScrapedPage(
                url=url,
                title=title,
                text_content=text_content[:10000],  # Limit content
                tables=tables,
                links=links,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ScrapedPage(
                url=url,
                title="Error",
                text_content=f"Failed to scrape: {str(e)}",
                tables=[],
                links=[],
                metadata={"error": str(e)}
            )
    
    def _parse_table(self, table) -> Optional[Dict[str, Any]]:
        """Parse an HTML table into structured data"""
        
        try:
            rows = table.find_all('tr')
            if not rows:
                return None
            
            # Get headers
            headers = []
            header_row = rows[0].find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_row]
            
            # Get data rows
            data = []
            for row in rows[1:10]:  # Limit rows
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    data.append(row_data)
            
            return {
                "headers": headers,
                "rows": data
            }
            
        except Exception as e:
            logger.warning(f"Error parsing table: {e}")
            return None
    
    def search_duckduckgo(
        self, 
        query: str, 
        max_results: int = 5
    ) -> List[SearchResult]:
        """
        Search the web using DuckDuckGo (FREE, no API key).
        
        Returns list of search results.
        """
        
        try:
            # DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for result in soup.find_all('div', class_='result')[:max_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    results.append(SearchResult(
                        title=title_elem.get_text(strip=True),
                        url=title_elem.get('href', ''),
                        snippet=snippet_elem.get_text(strip=True) if snippet_elem else ""
                    ))
            
            logger.info(f"DuckDuckGo search for '{query}': {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_news(
        self, 
        query: str = "", 
        max_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Get news headlines (FREE, using Google News RSS).
        
        Returns list of news items.
        """
        
        try:
            if query:
                # Search news
                rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
            else:
                # Top headlines
                rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
            
            response = self.session.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            
            news = []
            for item in soup.find_all('item')[:max_results]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                news.append({
                    "title": title.get_text() if title else "",
                    "url": link.get_text() if link else "",
                    "date": pub_date.get_text() if pub_date else "",
                    "source": source.get_text() if source else ""
                })
            
            logger.info(f"Got {len(news)} news items for '{query}'")
            return news
            
        except Exception as e:
            logger.error(f"News error: {e}")
            return []
    
    def extract_text_from_url(self, url: str, max_length: int = 5000) -> str:
        """
        Simple helper to get just text from a URL.
        """
        
        result = self.scrape_url(url)
        return result.text_content[:max_length]


# MCP Tool Interface
class WebMCPTool:
    """
    MCP-compatible interface for the web scraper.
    """
    
    name = "web_scraper"
    description = "Search the web, scrape webpages, and get news - FREE, no API key required"
    
    def __init__(self):
        self.scraper = WebScraperMCP()
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a web scraping action.
        
        Actions:
        - scrape: Scrape a URL
        - search: Search the web
        - news: Get news headlines
        """
        
        try:
            if action == "scrape":
                url = params.get("url", "")
                if not url:
                    return {"error": "URL required"}
                
                result = self.scraper.scrape_url(url)
                return {
                    "title": result.title,
                    "content": result.text_content[:3000],
                    "tables": result.tables,
                    "links": result.links[:10]
                }
            
            elif action == "search":
                query = params.get("query", "")
                if not query:
                    return {"error": "Query required"}
                
                results = self.scraper.search_duckduckgo(
                    query, 
                    max_results=params.get("max_results", 5)
                )
                return {
                    "results": [
                        {"title": r.title, "url": r.url, "snippet": r.snippet}
                        for r in results
                    ]
                }
            
            elif action == "news":
                query = params.get("query", "")
                results = self.scraper.get_news(
                    query,
                    max_results=params.get("max_results", 5)
                )
                return {"news": results}
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}


# Convenience functions for direct use
def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Quick web search"""
    scraper = WebScraperMCP()
    results = scraper.search_duckduckgo(query, max_results)
    return [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]


def get_webpage_text(url: str) -> str:
    """Get text content from a URL"""
    scraper = WebScraperMCP()
    return scraper.extract_text_from_url(url)


def get_news_headlines(topic: str = "", max_results: int = 5) -> List[Dict[str, str]]:
    """Get news headlines"""
    scraper = WebScraperMCP()
    return scraper.get_news(topic, max_results)


# Test
if __name__ == "__main__":
    # Test search
    print("=== Web Search ===")
    results = search_web("artificial intelligence trends 2024")
    for r in results:
        print(f"- {r['title']}")
    
    # Test news
    print("\n=== News ===")
    news = get_news_headlines("technology")
    for n in news:
        print(f"- {n['title']} ({n['source']})")
    
    # Test scrape
    print("\n=== Scrape ===")
    text = get_webpage_text("https://example.com")
    print(text[:500])
