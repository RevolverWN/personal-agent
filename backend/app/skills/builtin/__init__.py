"""Built-in skills package."""

from app.skills.builtin.weather import WeatherSkill
from app.skills.builtin.search import SearchSkill
from app.skills.builtin.summarize import SummarizeSkill

__all__ = ["WeatherSkill", "SearchSkill", "SummarizeSkill"]
