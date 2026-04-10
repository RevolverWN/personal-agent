"""Web search tool using DuckDuckGo."""

from duckduckgo_search import DDGS

from app.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo."""

    name = "web_search"
    description = "Search the web for information on a given topic. Returns search results with titles, URLs, and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query to look up"},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5, max: 10)",
                "default": 5,
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    }

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """Execute web search."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=min(max_results, 10)))

                formatted_results = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ]

                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "results_count": len(formatted_results),
                        "results": formatted_results,
                    },
                )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Search failed: {str(e)}")


class WebFetchTool(BaseTool):
    """Fetch and extract content from a webpage."""

    name = "web_fetch"
    description = "Fetch and extract the main content from a webpage URL. Useful for reading articles or documentation."
    parameters = {
        "type": "object",
        "properties": {"url": {"type": "string", "description": "The URL of the webpage to fetch"}},
        "required": ["url"],
    }

    async def execute(self, url: str) -> ToolResult:
        """Fetch webpage content."""
        import httpx
        from bs4 import BeautifulSoup

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer"]):
                    script.decompose()

                # Extract title
                title = soup.find("title")
                title_text = title.get_text(strip=True) if title else ""

                # Extract main content
                # Try to find main content area
                main_content = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find("div", class_="content")
                    or soup.find("div", id="content")
                )

                if main_content:
                    text = main_content.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)

                # Clean up text
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                cleaned_text = "\n".join(lines[:100])  # Limit to 100 lines

                return ToolResult(
                    success=True,
                    data={
                        "url": url,
                        "title": title_text,
                        "content": cleaned_text,
                        "content_length": len(cleaned_text),
                    },
                )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Failed to fetch webpage: {str(e)}")
