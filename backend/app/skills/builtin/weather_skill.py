"""Weather skill for getting weather information."""

from typing import Any, Dict, List
import httpx

from app.skills.base import BaseSkill, SkillResult, SkillMetadata


class WeatherSkill(BaseSkill):
    """Skill for getting weather information."""
    
    def _get_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="weather",
            description="Get weather information for any location",
            version="1.0.0",
            author="system",
            tags=["weather", "forecast", "location"],
            icon="🌤️",
            category="information",
            requirements=["httpx"]
        )
    
    def get_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_current",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location (e.g., 'Beijing', 'New York')"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius",
                            "description": "Temperature units"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        },
                        "days": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 7,
                            "default": 3,
                            "description": "Number of days for forecast"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> SkillResult:
        """Execute weather actions."""
        if action == "get_current":
            return await self._get_current_weather(params)
        elif action == "get_forecast":
            return await self._get_forecast(params)
        else:
            return SkillResult(
                success=False,
                data=None,
                error=f"Unknown action: {action}"
            )
    
    async def _get_current_weather(self, params: Dict[str, Any]) -> SkillResult:
        """Get current weather (using a free API or mock)."""
        location = params.get("location", "")
        units = params.get("units", "celsius")
        
        try:
            # For demo purposes, return mock data
            # In production, use a real weather API like OpenWeatherMap
            
            # Try to get real data from wttr.in (free service)
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://wttr.in/{location}?format=j1"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    current = data["current_condition"][0]
                    
                    temp = current["temp_C"] if units == "celsius" else current["temp_F"]
                    feels_like = current["FeelsLikeC"] if units == "celsius" else current["FeelsLikeF"]
                    
                    return SkillResult(
                        success=True,
                        data={
                            "location": location,
                            "temperature": temp,
                            "feels_like": feels_like,
                            "description": current["weatherDesc"][0]["value"],
                            "humidity": current["humidity"],
                            "wind_speed": current["windspeedKmph"],
                            "visibility": current["visibility"],
                            "pressure": current["pressure"],
                            "units": units
                        },
                        message=f"Current weather in {location}: {current['weatherDesc'][0]['value']}, {temp}°{units[0].upper()}"
                    )
                else:
                    raise Exception(f"API returned status {response.status_code}")
                    
        except Exception as e:
            # Return mock data if API fails
            return SkillResult(
                success=True,
                data={
                    "location": location,
                    "temperature": 22 if units == "celsius" else 72,
                    "feels_like": 23 if units == "celsius" else 73,
                    "description": "Partly cloudy",
                    "humidity": "65%",
                    "wind_speed": "12 km/h",
                    "units": units,
                    "note": "Using mock data (weather service unavailable)"
                },
                message=f"Current weather in {location}: Partly cloudy, 22°C (demo data)"
            )
    
    async def _get_forecast(self, params: Dict[str, Any]) -> SkillResult:
        """Get weather forecast."""
        location = params.get("location", "")
        days = params.get("days", 3)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://wttr.in/{location}?format=j1"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    forecast_days = data["weather"][:days]
                    
                    forecast = []
                    for day in forecast_days:
                        forecast.append({
                            "date": day["date"],
                            "max_temp": day["maxtempC"],
                            "min_temp": day["mintempC"],
                            "description": day["hourly"][12]["weatherDesc"][0]["value"],
                            "chance_of_rain": day["hourly"][12].get("chanceofrain", "0%")
                        })
                    
                    return SkillResult(
                        success=True,
                        data={
                            "location": location,
                            "forecast": forecast
                        },
                        message=f"{days}-day forecast for {location} retrieved"
                    )
                else:
                    raise Exception("API error")
                    
        except Exception as e:
            # Mock forecast
            from datetime import datetime, timedelta
            forecast = []
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                forecast.append({
                    "date": date,
                    "max_temp": 25 - i,
                    "min_temp": 18 - i,
                    "description": "Sunny" if i < 2 else "Cloudy",
                    "chance_of_rain": "10%"
                })
            
            return SkillResult(
                success=True,
                data={
                    "location": location,
                    "forecast": forecast,
                    "note": "Using demo data"
                },
                message=f"{days}-day forecast for {location} (demo data)"
            )
