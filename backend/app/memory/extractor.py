"""Memory extraction from conversations using LLM."""

import json
from typing import List, Optional
from datetime import datetime
import litellm
from litellm import acompletion

from app.config import settings
from app.memory.models import ExtractedMemory


class MemoryExtractor:
    """Extract memories from conversation using LLM."""
    
    EXTRACTION_PROMPT = """You are a memory extraction system. Analyze the following conversation and identify important information about the user that should be remembered for future conversations.

Extract facts, preferences, and important details. Only extract information that:
1. Is explicitly stated or strongly implied
2. Would be useful in future conversations
3. Is personal to the user (name, preferences, goals, etc.)
4. Is factual and unlikely to change quickly

Do NOT extract:
- Temporary information
- Questions the user asked
- General knowledge
- Information about other people unless relevant

Return a JSON array of memories. Each memory should have:
- content: The factual statement to remember (clear, concise)
- category: One of [preference, fact, goal, task, general]
- importance: 1-5 (5 being most important)
- confidence: 0.0-1.0 (how confident you are this is accurate)

If nothing memorable is found, return an empty array [].

Categories:
- preference: User likes/dislikes, choices
- fact: Personal information (name, job, location)
- goal: Things user wants to achieve
- task: Actions user needs to take
- general: Other important information

Conversation:
{conversation}

Return ONLY valid JSON array, no other text."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.model = settings.DEFAULT_MODEL
        self.api_key = settings.OPENAI_API_KEY
    
    def _format_conversation(self, messages: List[dict]) -> str:
        """Format conversation for extraction."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
        
        return "\n\n".join(formatted[-10:])  # Last 10 messages
    
    async def extract_memories(
        self,
        messages: List[dict],
        min_confidence: float = 0.7
    ) -> List[ExtractedMemory]:
        """Extract memories from conversation."""
        if not messages:
            return []
        
        conversation = self._format_conversation(messages)
        
        try:
            response = await acompletion(
                model=self._get_model_name(),
                messages=[
                    {
                        "role": "system",
                        "content": self.EXTRACTION_PROMPT.format(conversation=conversation)
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000,
                api_key=self.api_key
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                # Clean up common JSON issues
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                content = content.strip()
                memories_data = json.loads(content)
                
                if not isinstance(memories_data, list):
                    return []
                
                # Filter by confidence and create objects
                memories = []
                for mem_data in memories_data:
                    confidence = mem_data.get("confidence", 0)
                    if confidence >= min_confidence:
                        memories.append(ExtractedMemory(
                            content=mem_data.get("content", ""),
                            category=mem_data.get("category", "general"),
                            importance=mem_data.get("importance", 3),
                            confidence=confidence
                        ))
                
                return memories
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse extraction result: {e}")
                return []
                
        except Exception as e:
            print(f"Memory extraction error: {e}")
            return []
    
    def _get_model_name(self) -> str:
        """Get LiteLLM model name."""
        model_map = {
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "claude-3-opus-20240229": "claude-3-opus-20240229",
            "deepseek-chat": "deepseek/deepseek-chat",
        }
        return model_map.get(self.model, self.model)
    
    async def should_extract(
        self,
        messages: List[dict],
        last_extraction_time: Optional[datetime] = None
    ) -> bool:
        """Determine if extraction should run."""
        # Minimum messages required
        if len(messages) < 3:
            return False
        
        # Check if last message is from user (natural extraction point)
        if messages[-1].get("role") != "user":
            return False
        
        # Time-based throttling (min 5 minutes between extractions)
        if last_extraction_time:
            from datetime import timedelta
            if datetime.utcnow() - last_extraction_time < timedelta(minutes=5):
                return False
        
        return True
