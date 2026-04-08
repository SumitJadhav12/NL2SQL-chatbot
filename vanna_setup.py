import os
from dotenv import load_dotenv
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

load_dotenv()

# Simple User Resolver implementation
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="default_user",
            email="user@example.com",
            group_memberships=["user"]
        )

def get_agent(db_path="clinic.db"):
    """Initialize and return the Vanna 2.0 Agent"""
    
    print("Initializing Vanna 2.0 Agent...")
    
    # 1. Check for API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set in .env file. Please create a .env file with your API key.")
    
    # 2. Set up the LLM Service (Google Gemini)
    print("✓ Setting up Gemini LLM Service...")
    llm_service = GeminiLlmService(
        api_key=api_key,
        model="gemini-2.0-flash-exp"
    )
    
    # 3. Set up the SQLite Runner
    print(f"✓ Connecting to SQLite database: {db_path}...")
    sqlite_runner = SqliteRunner(db_path)
    
    # 4. Register the tools (VERSION-COMPATIBLE METHOD)
    print("✓ Registering tools...")
    tools = ToolRegistry()
    
    # Create a list of tools
    tool_list = [
        RunSqlTool(sql_runner=sqlite_runner),
        VisualizeDataTool(),
        SaveQuestionToolArgsTool(),
        SearchSavedCorrectToolUsesTool()
    ]
    
    # Try different methods to add tools (for compatibility with various Vanna versions)
    added = False
    for method_name in ['register', 'add', 'add_tool']:
        if hasattr(tools, method_name):
            for tool in tool_list:
                getattr(tools, method_name)(tool)
            print(f"  - Tools registered using '{method_name}' method")
            added = True
            break
    
    if not added:
        # If no standard method exists, try direct assignment
        if hasattr(tools, '_tools'):
            tools._tools = {tool.name: tool for tool in tool_list}
            print("  - Tools added via _tools dictionary")
        elif hasattr(tools, 'tools'):
            tools.tools = tool_list
            print("  - Tools added via tools list")
        else:
            raise AttributeError("Could not find a way to add tools to ToolRegistry")
    
    # 5. Set up the Agent's Memory
    print("✓ Setting up Agent Memory...")
    agent_memory = DemoAgentMemory(max_items=1000)
    
    # 6. Set up the User Resolver
    print("✓ Setting up User Resolver...")
    user_resolver = SimpleUserResolver()
    
    # 7. Create and return the Agent
    print("✓ Creating Agent instance...")
    agent = Agent(
        llm_service=llm_service,
        tool_registry=tools,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
        config=AgentConfig()
    )
    
    print("🎉 Vanna 2.0 Agent created successfully!")
    return agent