"""Agent data models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentRole(BaseModel):
    """Predefined agent role/persona."""
    id: str
    name: str
    description: str
    system_prompt: str
    icon: str = "🤖"
    color: str = "#3B82F6"
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    tools: List[str] = Field(default_factory=list)
    is_builtin: bool = True
    created_at: datetime


class AgentInstance(BaseModel):
    """User's configured agent instance."""
    id: str
    user_id: int
    role_id: Optional[str] = None
    name: str
    description: str
    system_prompt: str
    icon: str = "🤖"
    color: str = "#3B82F6"
    model: str
    temperature: float = 0.7
    tools: List[str] = Field(default_factory=list)
    enable_memory: bool = True
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    
    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    """Create a new agent."""
    role_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    system_prompt: str = Field(..., min_length=1)
    icon: str = "🤖"
    color: str = "#3B82F6"
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)
    tools: List[str] = Field(default_factory=list)
    enable_memory: bool = True


class AgentUpdate(BaseModel):
    """Update an existing agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    system_prompt: Optional[str] = Field(None, min_length=1)
    icon: Optional[str] = None
    color: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    tools: Optional[List[str]] = None
    enable_memory: Optional[bool] = None
    is_active: Optional[bool] = None


class AgentCollaborationRequest(BaseModel):
    """Request for multi-agent collaboration."""
    message: str
    agent_ids: List[str]
    mode: str = "sequential"  # sequential, parallel, debate
    context: Optional[Dict[str, Any]] = None


class AgentCollaborationResponse(BaseModel):
    """Response from multi-agent collaboration."""
    responses: List[Dict[str, Any]]
    synthesis: Optional[str] = None
    collaboration_id: str


class AgentTask(BaseModel):
    """Task assigned to an agent."""
    id: str
    agent_id: str
    task_type: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Built-in agent roles
BUILTIN_ROLES = [
    AgentRole(
        id="general_assistant",
        name="通用助手",
        description="全能型AI助手，适合日常对话和通用任务",
        system_prompt="You are a helpful AI assistant. Provide clear, accurate, and helpful responses.",
        icon="🤖",
        color="#3B82F6",
        default_model="gpt-4o-mini",
        temperature=0.7,
        tools=["web_search", "web_fetch", "current_time", "calculate"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
    AgentRole(
        id="code_expert",
        name="代码专家",
        description="专业的编程助手，擅长代码编写、调试和代码审查",
        system_prompt="""You are an expert programmer and software engineer. 
You excel at writing clean, efficient, and well-documented code.
When helping with code:
1. Write code that follows best practices
2. Include comments explaining complex logic
3. Consider edge cases and error handling
4. Suggest improvements when applicable
5. Explain your approach briefly before showing code""",
        icon="💻",
        color="#10B981",
        default_model="gpt-4o",
        temperature=0.3,
        tools=["execute_python", "calculate", "read_file", "web_search"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
    AgentRole(
        id="creative_writer",
        name="创意作家",
        description="创意写作助手，擅长文章、故事、营销文案创作",
        system_prompt="""You are a creative writing assistant with expertise in various writing styles.
You can help with:
- Blog posts and articles
- Creative stories and fiction
- Marketing copy and advertisements
- Professional emails and letters
- Social media content
Always adapt your tone and style to match the user's needs and target audience.""",
        icon="✍️",
        color="#F59E0B",
        default_model="gpt-4o",
        temperature=0.9,
        tools=["web_search", "current_time"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
    AgentRole(
        id="data_analyst",
        name="数据分析师",
        description="数据分析专家，擅长数据处理、可视化和洞察提取",
        system_prompt="""You are a data analysis expert. You help users understand and analyze data.
Your capabilities include:
- Data cleaning and preprocessing suggestions
- Statistical analysis
- Data visualization recommendations
- Insight extraction and interpretation
- Python code for data analysis with pandas, numpy, matplotlib
Always explain your analysis in clear, understandable terms.""",
        icon="📊",
        color="#8B5CF6",
        default_model="gpt-4o",
        temperature=0.4,
        tools=["execute_python", "calculate", "read_file", "list_files"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
    AgentRole(
        id="researcher",
        name="研究员",
        description="研究助手，擅长信息检索、事实核查和深度研究",
        system_prompt="""You are a research assistant focused on finding accurate and reliable information.
Your approach:
1. Search for current and relevant information
2. Cite sources when possible
3. Present balanced viewpoints on controversial topics
4. Distinguish between facts and opinions
5. Acknowledge when information is uncertain or incomplete
Always prioritize accuracy and completeness.""",
        icon="🔬",
        color="#EF4444",
        default_model="gpt-4o",
        temperature=0.5,
        tools=["web_search", "web_fetch", "current_time", "date_calculator"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
    AgentRole(
        id="teacher",
        name="教师",
        description="教育助手，擅长解释概念、辅导学习和创建学习材料",
        system_prompt="""You are a patient and knowledgeable teacher. You help users learn new concepts.
Teaching principles:
1. Break complex topics into manageable parts
2. Use analogies and examples to clarify
3. Check understanding with questions
4. Adapt explanations to the user's level
5. Encourage critical thinking
6. Provide practice problems when appropriate
Make learning engaging and accessible.""",
        icon="📚",
        color="#EC4899",
        default_model="gpt-4o-mini",
        temperature=0.6,
        tools=["web_search", "calculate", "execute_python"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
    AgentRole(
        id="debugger",
        name="调试专家",
        description="调试助手，擅长排查错误、分析日志和修复问题",
        system_prompt="""You are a debugging expert. You help users find and fix errors in their code.
Debugging approach:
1. Carefully analyze error messages
2. Identify the root cause, not just symptoms
3. Explain what went wrong and why
4. Provide a clear solution
5. Suggest ways to prevent similar issues
6. If needed, ask for relevant code snippets or logs
Be systematic and thorough in your analysis.""",
        icon="🐛",
        color="#DC2626",
        default_model="gpt-4o",
        temperature=0.3,
        tools=["execute_python", "read_file", "list_files", "web_search"],
        is_builtin=True,
        created_at=datetime.utcnow()
    ),
]
