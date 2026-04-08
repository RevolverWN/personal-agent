"""System and utility tools."""

import datetime
import platform
from typing import Dict, Any

from app.tools.base import BaseTool, ToolResult


class CurrentTimeTool(BaseTool):
    """Get current date and time."""
    
    name = "current_time"
    description = "Get the current date and time information including timezone, day of week, and formatted strings."
    parameters = {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Output format: 'iso', 'readable', or 'timestamp' (default: 'readable')",
                "enum": ["iso", "readable", "timestamp"],
                "default": "readable"
            }
        }
    }
    
    async def execute(self, format: str = "readable") -> ToolResult:
        """Get current time."""
        try:
            now = datetime.datetime.now()
            
            if format == "iso":
                time_str = now.isoformat()
            elif format == "timestamp":
                time_str = str(now.timestamp())
            else:
                time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            return ToolResult(
                success=True,
                data={
                    "datetime": time_str,
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "year": now.year,
                    "month": now.month,
                    "day": now.day,
                    "hour": now.hour,
                    "minute": now.minute,
                    "second": now.second,
                    "day_of_week": now.strftime("%A"),
                    "day_of_year": now.timetuple().tm_yday,
                    "week_of_year": now.isocalendar()[1],
                    "timezone": str(now.astimezone().tzinfo)
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get time: {str(e)}"
            )


class DateCalculatorTool(BaseTool):
    """Calculate dates and time differences."""
    
    name = "date_calculator"
    description = "Calculate dates, add/subtract days, or find time difference between two dates."
    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "Operation to perform: 'add_days', 'subtract_days', 'days_between', or 'weekday'",
                "enum": ["add_days", "subtract_days", "days_between", "weekday"]
            },
            "date": {
                "type": "string",
                "description": "Base date in YYYY-MM-DD format (default: today)"
            },
            "days": {
                "type": "integer",
                "description": "Number of days (for add/subtract operations)"
            },
            "date2": {
                "type": "string",
                "description": "Second date in YYYY-MM-DD format (for days_between)"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        date: str = None,
        days: int = 0,
        date2: str = None
    ) -> ToolResult:
        """Perform date calculations."""
        try:
            if date:
                base_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            else:
                base_date = datetime.date.today()
            
            if operation == "add_days":
                result = base_date + datetime.timedelta(days=days)
                return ToolResult(
                    success=True,
                    data={
                        "operation": f"Add {days} days",
                        "input_date": base_date.isoformat(),
                        "result_date": result.isoformat(),
                        "day_of_week": result.strftime("%A")
                    }
                )
            
            elif operation == "subtract_days":
                result = base_date - datetime.timedelta(days=days)
                return ToolResult(
                    success=True,
                    data={
                        "operation": f"Subtract {days} days",
                        "input_date": base_date.isoformat(),
                        "result_date": result.isoformat(),
                        "day_of_week": result.strftime("%A")
                    }
                )
            
            elif operation == "days_between":
                if not date2:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="date2 is required for days_between operation"
                    )
                
                date2_obj = datetime.datetime.strptime(date2, "%Y-%m-%d").date()
                diff = abs((date2_obj - base_date).days)
                
                return ToolResult(
                    success=True,
                    data={
                        "date1": base_date.isoformat(),
                        "date2": date2_obj.isoformat(),
                        "days_between": diff,
                        "weeks": diff // 7,
                        "remaining_days": diff % 7
                    }
                )
            
            elif operation == "weekday":
                return ToolResult(
                    success=True,
                    data={
                        "date": base_date.isoformat(),
                        "day_of_week": base_date.strftime("%A"),
                        "is_weekend": base_date.weekday() >= 5
                    }
                )
            
        except ValueError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Calculation error: {str(e)}"
            )


class SystemInfoTool(BaseTool):
    """Get system information (safe, non-sensitive)."""
    
    name = "system_info"
    description = "Get basic system information including Python version, platform, and current working directory. No sensitive information is exposed."
    parameters = {
        "type": "object",
        "properties": {}
    }
    
    async def execute(self) -> ToolResult:
        """Get system information."""
        try:
            import sys
            import os
            
            return ToolResult(
                success=True,
                data={
                    "platform": platform.system(),
                    "platform_release": platform.release(),
                    "python_version": sys.version.split()[0],
                    "python_implementation": platform.python_implementation(),
                    "current_directory": os.getcwd(),
                    "processor": platform.processor() or "Unknown",
                    "machine": platform.machine(),
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get system info: {str(e)}"
            )
