"""File analysis tools for reading various file formats."""

import os
from pathlib import Path
from typing import Optional

from app.tools.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    """Read contents of a text file."""
    
    name = "read_file"
    description = "Read the contents of a text file. Supports various text formats like .txt, .py, .js, .md, .json, .csv, etc. Has size limits for safety."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the file to read"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read (default: 100, max: 1000)",
                "default": 100,
                "minimum": 1,
                "maximum": 1000
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start reading from (0-indexed)",
                "default": 0,
                "minimum": 0
            }
        },
        "required": ["filepath"]
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    async def execute(self, filepath: str, limit: int = 100, offset: int = 0) -> ToolResult:
        """Read file contents."""
        try:
            path = Path(filepath)
            
            # Security checks
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {filepath}"
                )
            
            if not path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is not a file: {filepath}"
                )
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File too large ({file_size} bytes). Maximum allowed: {self.MAX_FILE_SIZE} bytes"
                )
            
            # Read file
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                # Try binary detection
                with open(path, 'rb') as f:
                    content = f.read()
                    # Check if it's likely binary
                    if b'\x00' in content[:1024]:
                        return ToolResult(
                            success=False,
                            data=None,
                            error="File appears to be binary and cannot be read as text"
                        )
                    # Try with different encoding
                    content = content.decode('utf-8', errors='replace')
                    lines = content.split('\n')
            
            total_lines = len(lines)
            
            # Apply offset and limit
            start = min(offset, total_lines)
            end = min(start + limit, total_lines)
            selected_lines = lines[start:end]
            
            return ToolResult(
                success=True,
                data={
                    "filepath": str(path.absolute()),
                    "filename": path.name,
                    "total_lines": total_lines,
                    "lines_read": len(selected_lines),
                    "start_line": start,
                    "end_line": end,
                    "content": ''.join(selected_lines),
                    "file_size": file_size
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to read file: {str(e)}"
            )


class FileListTool(BaseTool):
    """List files in a directory."""
    
    name = "list_files"
    description = "List files and directories at a given path. Shows file names, sizes, and types."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list (default: current directory)",
                "default": "."
            },
            "recursive": {
                "type": "boolean",
                "description": "Whether to list recursively (default: false)",
                "default": False
            }
        }
    }
    
    async def execute(self, path: str = ".", recursive: bool = False) -> ToolResult:
        """List directory contents."""
        try:
            target_path = Path(path)
            
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path not found: {path}"
                )
            
            if not target_path.is_dir():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is not a directory: {path}"
                )
            
            items = []
            
            if recursive:
                for item in target_path.rglob("*"):
                    try:
                        stat = item.stat()
                        items.append({
                            "name": item.name,
                            "path": str(item.relative_to(target_path)),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else None
                        })
                    except (OSError, PermissionError):
                        continue
            else:
                for item in target_path.iterdir():
                    try:
                        stat = item.stat()
                        items.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else None
                        })
                    except (OSError, PermissionError):
                        continue
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
            
            return ToolResult(
                success=True,
                data={
                    "path": str(target_path.absolute()),
                    "item_count": len(items),
                    "items": items
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to list files: {str(e)}"
            )


class FileInfoTool(BaseTool):
    """Get detailed information about a file."""
    
    name = "file_info"
    description = "Get detailed information about a file including size, modification time, permissions, and type."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the file"
            }
        },
        "required": ["filepath"]
    }
    
    async def execute(self, filepath: str) -> ToolResult:
        """Get file information."""
        try:
            path = Path(filepath)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path not found: {filepath}"
                )
            
            stat = path.stat()
            
            # Determine file type
            if path.is_dir():
                file_type = "directory"
            elif path.is_symlink():
                file_type = "symlink"
            else:
                # Try to determine by extension
                ext = path.suffix.lower()
                file_type = ext if ext else "unknown"
            
            import datetime
            
            return ToolResult(
                success=True,
                data={
                    "filepath": str(path.absolute()),
                    "filename": path.name,
                    "extension": path.suffix,
                    "type": file_type,
                    "size": stat.st_size,
                    "size_human": self._format_size(stat.st_size),
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "accessed": datetime.datetime.fromtimestamp(stat.st_atime).isoformat(),
                    "permissions": oct(stat.st_mode)[-3:],
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get file info: {str(e)}"
            )
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
