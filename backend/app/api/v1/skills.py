"""Skills API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.auth import get_current_user
from app.models.database import User
from app.skills.manager import skill_manager

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_skills(category: str | None = None, current_user: User = Depends(get_current_user)):
    """List all available skills."""
    if category:
        skills = skill_manager.get_skills_by_category(category)
    else:
        skills = [skill_manager.get_skill(name) for name in skill_manager.list_skills()]

    return [
        {
            "name": skill.metadata.name,
            "description": skill.metadata.description,
            "version": skill.metadata.version,
            "icon": skill.metadata.icon,
            "category": skill.metadata.category,
            "tags": skill.metadata.tags,
            "initialized": skill.is_initialized(),
            "actions_count": len(skill.get_actions()),
        }
        for skill in skills
        if skill
    ]


@router.get("/categories")
async def list_categories(current_user: User = Depends(get_current_user)):
    """List all skill categories."""
    categories = {}
    for name in skill_manager.list_skills():
        skill = skill_manager.get_skill(name)
        if skill:
            cat = skill.metadata.category
            categories[cat] = categories.get(cat, 0) + 1

    return {"categories": categories}


@router.get("/{skill_name}")
async def get_skill_info(skill_name: str, current_user: User = Depends(get_current_user)):
    """Get detailed information about a skill."""
    info = skill_manager.get_skill_info(skill_name)

    if not info:
        raise HTTPException(status_code=404, detail="Skill not found")

    return info


@router.post("/{skill_name}/execute")
async def execute_skill(
    skill_name: str, action: str, params: dict, current_user: User = Depends(get_current_user)
):
    """Execute a skill action."""
    result = await skill_manager.execute_skill(skill_name, action, params)

    return {
        "success": result.success,
        "data": result.data,
        "message": result.message,
        "error": result.error,
    }


@router.get("/{skill_name}/actions")
async def get_skill_actions(skill_name: str, current_user: User = Depends(get_current_user)):
    """Get available actions for a skill."""
    skill = skill_manager.get_skill(skill_name)

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return {"skill": skill_name, "actions": skill.get_actions()}


@router.post("/{skill_name}/initialize")
async def initialize_skill(skill_name: str, current_user: User = Depends(get_current_user)):
    """Manually initialize a skill."""
    skill = skill_manager.get_skill(skill_name)

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    success = await skill.initialize()

    return {"skill": skill_name, "initialized": success}


@router.get("/search")
async def search_skills(
    query: str = Query(..., min_length=1), current_user: User = Depends(get_current_user)
):
    """Search skills by query."""
    skills = skill_manager.search_skills(query)

    return {
        "query": query,
        "results": [
            {
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "icon": skill.metadata.icon,
                "category": skill.metadata.category,
            }
            for skill in skills
        ],
        "count": len(skills),
    }


@router.get("/schemas/all")
async def get_all_schemas(current_user: User = Depends(get_current_user)):
    """Get all skill schemas for OpenAI function calling."""
    schemas = skill_manager.get_all_schemas()
    return {"schemas": schemas, "count": len(schemas)}
