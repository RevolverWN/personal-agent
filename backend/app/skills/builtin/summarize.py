"""Content summarization skill using LLM."""

from typing import Dict, Any

from litellm import acompletion

from app.skills.base import BaseSkill, SkillMetadata, SkillResult
from app.config import settings


class SummarizeSkill(BaseSkill):
    """Content summarization skill using LiteLLM."""
    
    def _get_metadata(self) -> SkillMetadata:
        """Get skill metadata."""
        return SkillMetadata(
            name="summarize",
            description="Summarize text content using AI",
            version="1.0.0",
            author="system",
            icon="📝",
            category="text",
            tags=["summarize", "text", "ai", "llm"],
            requirements=["litellm"]
        )
    
    def get_actions(self) -> list[Dict[str, Any]]:
        """Get available actions."""
        return [
            {
                "name": "summarize",
                "description": "Summarize text content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to summarize"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum summary length in words (default: 100)",
                            "default": 100
                        },
                        "style": {
                            "type": "string",
                            "description": "Summary style: 'brief', 'detailed', 'bullets'",
                            "enum": ["brief", "detailed", "bullets"],
                            "default": "brief"
                        },
                        "language": {
                            "type": "string",
                            "description": "Output language (default: same as input)",
                            "default": "auto"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "extract_key_points",
                "description": "Extract key points from text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze"
                        },
                        "max_points": {
                            "type": "integer",
                            "description": "Maximum number of key points (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["text"]
                }
            }
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> SkillResult:
        """Execute summarization skill."""
        if action not in ["summarize", "extract_key_points"]:
            return SkillResult(
                success=False,
                data=None,
                error=f"Unknown action: {action}. Available: summarize, extract_key_points"
            )
        
        text = params.get("text")
        if not text:
            return SkillResult(
                success=False,
                data=None,
                error="Missing required parameter: text"
            )
        
        try:
            if action == "summarize":
                return await self._summarize_text(
                    text,
                    params.get("max_length", 100),
                    params.get("style", "brief"),
                    params.get("language", "auto")
                )
            else:
                return await self._extract_key_points(
                    text,
                    params.get("max_points", 5)
                )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Summarization failed: {str(e)}"
            )
    
    async def _summarize_text(
        self,
        text: str,
        max_length: int,
        style: str,
        language: str
    ) -> SkillResult:
        """Summarize text using LLM."""
        # Build system prompt based on style
        style_prompts = {
            "brief": "Provide a concise summary in 2-3 sentences.",
            "detailed": "Provide a comprehensive summary that covers all main points.",
            "bullets": "Summarize as bullet points (•), each point should be concise."
        }
        
        style_instruction = style_prompts.get(style, style_prompts["brief"])
        
        language_instruction = ""
        if language != "auto":
            language_instruction = f"\nOutput the summary in {language}."
        
        system_prompt = (
            "You are an expert summarizer. "
            f"{style_instruction}"
            f"\nKeep the summary under {max_length} words."
            f"{language_instruction}"
        )
        
        user_prompt = f"Please summarize the following text:\n\n{text}"
        
        try:
            response = await acompletion(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=min(settings.DEFAULT_MAX_TOKENS, max_length * 2)
            )
            
            summary = response.choices[0].message.content.strip()
            
            result_data = {
                "original_length": len(text),
                "summary_length": len(summary),
                "style": style,
                "summary": summary
            }
            
            return SkillResult(
                success=True,
                data=result_data,
                message=f"Summary ({style}):\n{summary}"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"LLM error: {str(e)}"
            )
    
    async def _extract_key_points(self, text: str, max_points: int) -> SkillResult:
        """Extract key points from text using LLM."""
        system_prompt = (
            f"You are an expert at extracting key information. "
            f"Extract exactly {max_points} or fewer key points from the text. "
            "Format each point as a single sentence, numbered."
        )
        
        user_prompt = f"Extract key points from the following text:\n\n{text}"
        
        try:
            response = await acompletion(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse numbered points
            points = []
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                    # Remove number/bullet prefix
                    point = line.lstrip('0123456789.•- ')
                    if point:
                        points.append(point)
            
            if not points:
                # Fallback: split by newlines
                points = [line.strip() for line in content.split('\n') if line.strip()]
            
            points = points[:max_points]
            
            result_data = {
                "original_length": len(text),
                "key_points": points,
                "count": len(points)
            }
            
            message = f"Key points ({len(points)}):\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(points))
            
            return SkillResult(
                success=True,
                data=result_data,
                message=message
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"LLM error: {str(e)}"
            )
