"""Skill manager for loading and managing skills."""

import importlib
import pkgutil
from typing import Dict, List, Optional, Any, Type
from pathlib import Path

from app.skills.base import BaseSkill, SkillMetadata, SkillResult


class SkillManager:
    """Manager for skills."""
    
    def __init__(self):
        """Initialize skill manager."""
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_classes: Dict[str, Type[BaseSkill]] = {}
        self._load_builtin_skills()
    
    def _load_builtin_skills(self):
        """Load all built-in skills."""
        builtin_package = "app.skills.builtin"
        
        try:
            # Import all modules in builtin package
            import app.skills.builtin as builtin_module
            
            for importer, modname, ispkg in pkgutil.iter_modules(
                builtin_module.__path__, builtin_package + "."
            ):
                try:
                    module = importlib.import_module(modname)
                    
                    # Find skill classes in module
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (
                            isinstance(obj, type) and
                            issubclass(obj, BaseSkill) and
                            obj != BaseSkill
                        ):
                            # Instantiate to get metadata
                            skill_instance = obj()
                            skill_name = skill_instance.metadata.name
                            
                            self._skill_classes[skill_name] = obj
                            self._skills[skill_name] = skill_instance
                            
                except Exception as e:
                    print(f"Failed to load skill from {modname}: {e}")
                    
        except Exception as e:
            print(f"Failed to load builtin skills: {e}")
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all skills."""
        results = {}
        for name, skill in self._skills.items():
            try:
                results[name] = await skill.initialize()
            except Exception as e:
                print(f"Failed to initialize skill {name}: {e}")
                results[name] = False
        return results
    
    async def cleanup_all(self):
        """Cleanup all skills."""
        for skill in self._skills.values():
            try:
                await skill.cleanup()
            except Exception as e:
                print(f"Error cleaning up skill: {e}")
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def list_skills(self) -> List[str]:
        """List all available skill names."""
        return list(self._skills.keys())
    
    def get_all_metadata(self) -> List[SkillMetadata]:
        """Get metadata for all skills."""
        return [skill.metadata for skill in self._skills.values()]
    
    def get_skill_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a skill."""
        skill = self._skills.get(name)
        if not skill:
            return None
        
        return {
            "metadata": skill.metadata.model_dump(),
            "actions": skill.get_actions(),
            "initialized": skill.is_initialized(),
            "schemas": skill.get_schema()
        }
    
    async def execute_skill(
        self,
        skill_name: str,
        action: str,
        params: Dict[str, Any]
    ) -> SkillResult:
        """Execute a skill action."""
        skill = self._skills.get(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                data=None,
                error=f"Skill '{skill_name}' not found"
            )
        
        if not skill.is_initialized():
            success = await skill.initialize()
            if not success:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Failed to initialize skill '{skill_name}'"
                )
        
        try:
            return await skill.execute(action, params)
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Skill execution error: {str(e)}"
            )
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get all skill action schemas for OpenAI."""
        schemas = []
        for skill in self._skills.values():
            schemas.extend(skill.get_schema())
        return schemas
    
    def find_skill_for_action(self, action_name: str) -> Optional[BaseSkill]:
        """Find which skill handles a given action."""
        # Action format: "skill_name.action_name"
        if "." in action_name:
            skill_name = action_name.split(".")[0]
            return self._skills.get(skill_name)
        return None
    
    def get_skills_by_category(self, category: str) -> List[BaseSkill]:
        """Get skills filtered by category."""
        return [
            skill for skill in self._skills.values()
            if skill.metadata.category == category
        ]
    
    def search_skills(self, query: str) -> List[BaseSkill]:
        """Search skills by name, description, or tags."""
        query = query.lower()
        results = []
        
        for skill in self._skills.values():
            metadata = skill.metadata
            if (
                query in metadata.name.lower() or
                query in metadata.description.lower() or
                any(query in tag.lower() for tag in metadata.tags)
            ):
                results.append(skill)
        
        return results


# Global skill manager instance
skill_manager = SkillManager()
