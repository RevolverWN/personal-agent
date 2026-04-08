"""News skill for getting latest news."""

from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup

from app.skills.base import BaseSkill, SkillResult, SkillMetadata


class NewsSkill(BaseSkill):
    """Skill for getting news and headlines."""
    
    def _get_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="news",
            description="Get latest news and headlines",
            version="1.0.0",
            author="system",
            tags=["news", "headlines", "current_events"],
            icon="📰",
            category="information",
            requirements=["httpx", "beautifulsoup4"]
        )
    
    def get_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_headlines",
                "description": "Get latest news headlines",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["general", "technology", "business", "science", "health"],
                            "default": "general",
                            "description": "News category"
                        },
                        "count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5,
                            "description": "Number of headlines"
                        }
                    }
                }
            },
            {
                "name": "search_news",
                "description": "Search for news on a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5,
                            "description": "Number of results"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> SkillResult:
        """Execute news actions."""
        if action == "get_headlines":
            return await self._get_headlines(params)
        elif action == "search_news":
            return await self._search_news(params)
        else:
            return SkillResult(
                success=False,
                data=None,
                error=f"Unknown action: {action}"
            )
    
    async def _get_headlines(self, params: Dict[str, Any]) -> SkillResult:
        """Get latest headlines."""
        category = params.get("category", "general")
        count = params.get("count", 5)
        
        try:
            # Use RSS feeds or news APIs
            # For demo, return structured mock data
            headlines = self._get_mock_headlines(category, count)
            
            return SkillResult(
                success=True,
                data={
                    "category": category,
                    "headlines": headlines,
                    "source": "Demo News Feed"
                },
                message=f"Retrieved {len(headlines)} {category} headlines"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Failed to get headlines: {str(e)}"
            )
    
    async def _search_news(self, params: Dict[str, Any]) -> SkillResult:
        """Search for news."""
        query = params.get("query", "")
        count = params.get("count", 5)
        
        try:
            # Search using web search then extract news
            # For demo, return mock results
            results = self._get_mock_search_results(query, count)
            
            return SkillResult(
                success=True,
                data={
                    "query": query,
                    "results": results
                },
                message=f"Found {len(results)} news items for '{query}'"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Failed to search news: {str(e)}"
            )
    
    def _get_mock_headlines(self, category: str, count: int) -> List[Dict[str, str]]:
        """Get mock headlines for demo."""
        headlines_db = {
            "general": [
                {"title": "Global Climate Summit Reaches New Agreement", "source": "World News"},
                {"title": "Major Tech Company Announces Breakthrough AI Model", "source": "Tech Daily"},
                {"title": "Space Mission Successfully Launches to Mars", "source": "Space Today"},
                {"title": "New Economic Policies Aim to Boost Growth", "source": "Business Weekly"},
                {"title": "Scientists Discover New Species in Deep Ocean", "source": "Science Mag"},
            ],
            "technology": [
                {"title": "Revolutionary Quantum Computer Achieves New Milestone", "source": "Tech Daily"},
                {"title": "AI Assistant Passes Medical Licensing Exam", "source": "AI Weekly"},
                {"title": "New Battery Technology Promises Week-Long Charge", "source": "Tech Review"},
                {"title": "5G Networks Expand to Rural Areas", "source": "Telecom News"},
                {"title": "Open Source Community Releases Major Update", "source": "Developer Hub"},
            ],
            "business": [
                {"title": "Stock Markets Reach Record Highs", "source": "Financial Times"},
                {"title": "Startup Unicorn Announces IPO Plans", "source": "Business Weekly"},
                {"title": "Global Trade Agreements Under Review", "source": "Econ Today"},
                {"title": "New Investment Fund Focuses on Green Energy", "source": "Invest Daily"},
                {"title": "Retail Sector Shows Strong Recovery", "source": "Commerce News"},
            ],
            "science": [
                {"title": "Cancer Research Breakthrough Announced", "source": "Medical Science"},
                {"title": "New Particle Discovered at CERN", "source": "Physics Today"},
                {"title": "Gene Therapy Shows Promise for Rare Diseases", "source": "BioTech"},
                {"title": "Climate Scientists Release New Climate Model", "source": "Earth Science"},
                {"title": "Astronomers Find Potentially Habitable Exoplanet", "source": "Space Science"},
            ],
            "health": [
                {"title": "New Study Links Exercise to Longevity", "source": "Health Weekly"},
                {"title": "Mental Health Apps Show Positive Results", "source": "Psychology Today"},
                {"title": "Nutrition Guidelines Updated for 2024", "source": "Health Org"},
                {"title": "Sleep Research Reveals New Insights", "source": "Sleep Science"},
                {"title": "Vaccine Development Accelerates", "source": "Medical News"},
            ]
        }
        
        return headlines_db.get(category, headlines_db["general"])[:count]
    
    def _get_mock_search_results(self, query: str, count: int) -> List[Dict[str, str]]:
        """Get mock search results."""
        return [
            {
                "title": f"Breaking: Major Development in {query.title()}",
                "source": "News Network",
                "summary": f"Latest updates on {query} show significant progress..."
            },
            {
                "title": f"Analysis: The Impact of {query.title()} on Industry",
                "source": "Business Insider",
                "summary": f"Experts weigh in on how {query} is changing the landscape..."
            },
            {
                "title": f"{query.title()}: What You Need to Know",
                "source": "Daily Report",
                "summary": f"A comprehensive guide to understanding {query}..."
            },
        ][:count]
