"""Weather skill - Query current weather using wttr.in API."""

import httpx
from typing import Dict, Any

from app.skills.base import BaseSkill, SkillMetadata, SkillResult


class WeatherSkill(BaseSkill):
    """Weather query skill using wttr.in API (no API key required)."""
    
    def _get_metadata(self) -> SkillMetadata:
        """Get skill metadata."""
        return SkillMetadata(
            name="weather",
            description="Query current weather conditions for any city",
            version="1.0.0",
            author="system",
            icon="🌤️",
            category="information",
            tags=["weather", "forecast", "temperature", "humidity"],
            requirements=["httpx"]
        )
    
    def get_actions(self) -> list[Dict[str, Any]]:
        """Get available actions."""
        return [
            {
                "name": "current",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name (e.g., 'Beijing', 'New York')"
                        }
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "forecast",
                "description": "Get weather forecast for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days (1-3)",
                            "default": 1
                        }
                    },
                    "required": ["city"]
                }
            }
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> SkillResult:
        """Execute weather skill."""
        if action not in ["current", "forecast"]:
            return SkillResult(
                success=False,
                data=None,
                error=f"Unknown action: {action}. Available: current, forecast"
            )
        
        city = params.get("city")
        if not city:
            return SkillResult(
                success=False,
                data=None,
                error="Missing required parameter: city"
            )
        
        try:
            # Use wttr.in API with JSON format
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://wttr.in/{city}?format=j1"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if action == "current":
                return self._parse_current(data, city)
            else:
                return self._parse_forecast(data, city, params.get("days", 1))
                
        except httpx.TimeoutException:
            return SkillResult(
                success=False,
                data=None,
                error="Weather API request timed out"
            )
        except httpx.HTTPStatusError as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Weather API error: {e.response.status_code}"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Failed to get weather: {str(e)}"
            )
    
    def _parse_current(self, data: Dict[str, Any], city: str) -> SkillResult:
        """Parse current weather data."""
        try:
            current = data.get("current_condition", [{}])[0]
            location = data.get("nearest_area", [{}])[0]
            
            result_data = {
                "city": location.get("areaName", [{}])[0].get("value", city),
                "country": location.get("country", [{}])[0].get("value", ""),
                "temperature": f"{current.get('temp_C', 'N/A')}°C",
                "temperature_f": f"{current.get('temp_F', 'N/A')}°F",
                "description": current.get("weatherDesc", [{}])[0].get("value", "N/A"),
                "humidity": f"{current.get('humidity', 'N/A')}%",
                "wind": f"{current.get('windspeedKmph', 'N/A')} km/h",
                "wind_direction": current.get("winddir16Point", "N/A"),
                "feels_like": f"{current.get('FeelsLikeC', 'N/A')}°C",
                "visibility": f"{current.get('visibility', 'N/A')} km",
                "uv_index": current.get("uvIndex", "N/A"),
                "pressure": f"{current.get('pressure', 'N/A')} mb"
            }
            
            message = (
                f"Weather in {result_data['city']}: {result_data['description']}\n"
                f"Temperature: {result_data['temperature']} "
                f"(feels like {result_data['feels_like']})\n"
                f"Humidity: {result_data['humidity']}, "
                f"Wind: {result_data['wind']} {result_data['wind_direction']}"
            )
            
            return SkillResult(
                success=True,
                data=result_data,
                message=message
            )
        except (KeyError, IndexError) as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Failed to parse weather data: {str(e)}"
            )
    
    def _parse_forecast(self, data: Dict[str, Any], city: str, days: int) -> SkillResult:
        """Parse weather forecast data."""
        try:
            location = data.get("nearest_area", [{}])[0]
            forecasts = data.get("weather", [])[:days]
            
            forecast_list = []
            for day in forecasts:
                forecast_list.append({
                    "date": day.get("date", "N/A"),
                    "max_temp": f"{day.get('maxtempC', 'N/A')}°C",
                    "min_temp": f"{day.get('mintempC', 'N/A')}°C",
                    "avg_temp": f"{day.get('avgtempC', 'N/A')}°C",
                    "description": day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "N/A"),
                    "sunrise": day.get("astronomy", [{}])[0].get("sunrise", "N/A"),
                    "sunset": day.get("astronomy", [{}])[0].get("sunset", "N/A"),
                    "moonrise": day.get("astronomy", [{}])[0].get("moonrise", "N/A"),
                    "moonset": day.get("astronomy", [{}])[0].get("moonset", "N/A")
                })
            
            result_data = {
                "city": location.get("areaName", [{}])[0].get("value", city),
                "country": location.get("country", [{}])[0].get("value", ""),
                "forecasts": forecast_list
            }
            
            message_lines = [f"Weather forecast for {result_data['city']}:"]
            for f in forecast_list:
                message_lines.append(
                    f"  {f['date']}: {f['min_temp']} - {f['max_temp']}, {f['description']}"
                )
            
            return SkillResult(
                success=True,
                data=result_data,
                message="\n".join(message_lines)
            )
        except (KeyError, IndexError) as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Failed to parse forecast data: {str(e)}"
            )
