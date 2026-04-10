"""Web search skill using DuckDuckGo."""

import httpx
from typing import Dict, Any, List
from duckduckgo_search import DDGS

from app.skills.base import BaseSkill, SkillMetadata, SkillResult


class SearchSkill(BaseSkill):
    """Web search skill using DuckDuckGo (no API key required)."""
    
    def _get_metadata(self) -> SkillMetadata:
        """Get skill metadata."""
        return SkillMetadata(
            name="search",
            description="Search the web for information",
            version="1.0.0",
            author="system",
            icon="🔍",
            category="information",
            tags=["search", "web", "duckduckgo", "query"],
            requirements=["duckduckgo-search", "httpx"]
        )
    
    def get_actions(self) -> List[Dict[str, Any]]:
        """Get available actions."""
        return [
            {
                "name": "search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)",
                            "default": 5
                        },
                        "region": {
                            "type": "string",
                            "description": "Region code (e.g., 'cn', 'us', 'uk')",
                            "default": "wt-wt"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "instant_answer",
                "description": "Get an instant answer for a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> SkillResult:
        """Execute search skill."""
        if action not in ["search", "instant_answer"]:
            return SkillResult(
                success=False,
                data=None,
                error=f"Unknown action: {action}. Available: search, instant_answer"
            )
        
        query = params.get("query")
        if not query:
            return SkillResult(
                success=False,
                data=None,
                error="Missing required parameter: query"
            )
        
        try:
            if action == "search":
                return await self._search_web(
                    query,
                    params.get("max_results", 5),
                    params.get("region", "wt-wt")
                )
            else:
                return await self._instant_answer(query)
                
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Search failed: {str(e)}"
            )
    
    async def _search_web(self, query: str, max_results: int, region: str) -> SkillResult:
        """Perform web search using DuckDuckGo."""
        try:
            # DDGS is synchronous, but we run it in a thread-pool friendly way
            results = []
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results, region=region))
            
            for r in search_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "source": r.get("engine", "duckduckgo")
                })
            
            message = f"Found {len(results)} results for '{query}'"
            if results:
                message += ":\n"
                for i, r in enumerate(results[:3], 1):
                    message += f"\n{i}. {r['title']}\n   {r['url']}"
            
            return SkillResult(
                success=True,
                data={"query": query, "results": results, "count": len(results)},
                message=message
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Search error: {str(e)}"
            )
    
    async def _instant_answer(self, query: str) -> SkillResult:
        """Get instant answer from DuckDuckGo."""
        try:
            # Use DuckDuckGo Instant Answer API directly
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Extract relevant information
            abstract = data.get("Abstract", "")
            abstract_source = data.get("AbstractSource", "")
            abstract_url = data.get("AbstractURL", "")
            image = data.get("Image", "")
            heading = data.get("Heading", "")
            
            if not abstract:
                # Try related topics
                related = data.get("RelatedTopics", [])
                if related and len(related) > 0:
                    first_topic = related[0]
                    if isinstance(first_topic, dict):
                        abstract = first_topic.get("Text", "")
                        abstract_url = first_topic.get("FirstURL", "")
            
            if not abstract:
                return SkillResult(
                    success=True,
                    data={"query": query, "answer": None},
                    message=f"No instant answer found for '{query}'"
                )
            
            result_data = {
                "query": query,
                "answer": abstract,
                "source": abstract_source,
                "url": abstract_url,
                "heading": heading,
                "image": f"https://duckduckgo.com{image}" if image else None
            }
            
            message = f"Answer: {abstract}"
            if abstract_url:
                message += f"\nSource: {abstract_url}"
            
            return SkillResult(
                success=True,
                data=result_data,
                message=message
            )
        except httpx.HTTPStatusError as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"API error: {e.response.status_code}"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Instant answer error: {str(e)}"
            )
