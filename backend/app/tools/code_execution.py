"""Code execution tool with safety restrictions."""

import ast
import os
import subprocess
import tempfile

from app.tools.base import BaseTool, ToolResult


class CodeExecutionTool(BaseTool):
    """Execute Python code in a sandboxed environment."""

    name = "execute_python"
    description = "Execute Python code and return the output. Supports print statements and returns the last expression. Has safety restrictions - cannot access files, network, or system commands."
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "The Python code to execute"},
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds (default: 10, max: 60)",
                "default": 10,
                "minimum": 1,
                "maximum": 60,
            },
        },
        "required": ["code"],
    }

    # Dangerous imports and functions to block
    BLOCKED_IMPORTS = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "ftplib",
        "telnetlib",
        "smtplib",
        "poplib",
        "imaplib",
        "nntplib",
        "sqlite3",
        "dbm",
        "gdbm",
        "webbrowser",
        "ctypes",
        "mmap",
        "resource",
        "signal",
        "pty",
        "tty",
        "pickle",
        "marshal",
        "shelve",
        "multiprocessing",
        "threading",
        "concurrent",
        "asyncio.subprocess",
    }

    BLOCKED_BUILTINS = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "input",
        "exit",
        "quit",
        "help",
        "reload",
    }

    def _is_code_safe(self, code: str) -> tuple[bool, str]:
        """Check if code is safe to execute."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        for node in ast.walk(tree):
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module in self.BLOCKED_IMPORTS:
                        return False, f"Import of '{module}' is not allowed"

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    if module in self.BLOCKED_IMPORTS:
                        return False, f"Import from '{module}' is not allowed"

            # Check for blocked builtins
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_BUILTINS:
                        return False, f"Use of '{node.func.id}()' is not allowed"

            # Check for file operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["read", "write", "open"]:
                        return False, "File operations are not allowed"

        return True, ""

    async def execute(self, code: str, timeout: int = 10) -> ToolResult:
        """Execute Python code safely."""
        # Safety check
        is_safe, error_msg = self._is_code_safe(code)
        if not is_safe:
            return ToolResult(
                success=False, data=None, error=f"Code safety check failed: {error_msg}"
            )

        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                # Wrap code to capture output
                wrapped_code = f"""
import sys
from io import StringIO

# Redirect stdout
old_stdout = sys.stdout
sys.stdout = StringIO()

# Execute user code
{code}

# Get output
output = sys.stdout.getvalue()
sys.stdout = old_stdout

# Print output for capture
print(output, end='')
"""
                f.write(wrapped_code)
                temp_file = f.name

            try:
                # Execute with timeout
                result = subprocess.run(
                    ["python", temp_file], capture_output=True, text=True, timeout=min(timeout, 60)
                )

                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"output": result.stdout, "execution_time": f"{timeout}s limit"},
                    )
                else:
                    return ToolResult(
                        success=False, data={"output": result.stdout}, error=result.stderr
                    )
            finally:
                # Clean up temp file
                os.unlink(temp_file)

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False, data=None, error=f"Code execution timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Execution error: {str(e)}")


class CalculateTool(BaseTool):
    """Perform mathematical calculations."""

    name = "calculate"
    description = "Perform mathematical calculations. Supports basic arithmetic, powers, square roots, trigonometric functions, and more."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')",
            }
        },
        "required": ["expression"],
    }

    async def execute(self, expression: str) -> ToolResult:
        """Execute mathematical calculation."""
        import math

        # Create safe namespace with math functions
        safe_dict = {
            "abs": abs,
            "round": round,
            "max": max,
            "min": min,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "atan2": math.atan2,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "exp": math.exp,
            "log": math.log,
            "log10": math.log10,
            "log2": math.log2,
            "pi": math.pi,
            "e": math.e,
            "ceil": math.ceil,
            "floor": math.floor,
            "factorial": math.factorial,
            "gcd": math.gcd,
            "degrees": math.degrees,
            "radians": math.radians,
        }

        try:
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)

            return ToolResult(
                success=True,
                data={"expression": expression, "result": result, "type": type(result).__name__},
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Calculation error: {str(e)}")
