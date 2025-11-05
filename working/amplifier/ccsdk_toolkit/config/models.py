"""Configuration models for CCSDK toolkit."""

from pathlib import Path

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class ToolPermissions(BaseModel):
    """Tool permission configuration.

    Attributes:
        allowed: List of allowed tool names/patterns
        disallowed: List of disallowed tool names/patterns
    """

    allowed: list[str] = Field(default_factory=lambda: ["*"])
    disallowed: list[str] = Field(default_factory=list)

    def is_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if the tool is allowed
        """
        # Check disallowed first
        if tool_name in self.disallowed:
            return False

        # Check allowed list
        if "*" in self.allowed:
            return True

        return tool_name in self.allowed


class ToolConfig(BaseModel):
    """Tool permission configuration.

    Attributes:
        allowed: List of allowed tool names/patterns
        disallowed: List of disallowed tool names/patterns
    """

    allowed: list[str] = Field(default_factory=lambda: ["*"])
    disallowed: list[str] = Field(default_factory=list)

    @field_validator("allowed", "disallowed")
    @classmethod
    def validate_tool_list(cls, v):
        """Ensure tool lists are properly formatted."""
        if not isinstance(v, list):
            return [v] if isinstance(v, str) else []
        return v

    class Config:
        json_schema_extra = {"example": {"allowed": ["read", "write", "grep"], "disallowed": ["bash", "execute"]}}


class MCPServerConfig(BaseModel):
    """MCP server configuration.

    Attributes:
        name: Server name
        command: Command to start the server
        args: Command arguments
        env: Environment variables
    """

    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env": {},
            }
        }


class AgentConfig(BaseModel):
    """Agent configuration.

    Attributes:
        name: Agent name/identifier
        system_prompt: System prompt text or path to file
        allowed_tools: List of allowed tools
        disallowed_tools: List of disallowed tools
        context_files: List of context file paths
        mcp_servers: List of MCP server configs
        max_turns: Maximum conversation turns
    """

    name: str
    system_prompt: str
    allowed_tools: list[str] = Field(default_factory=lambda: ["*"])
    disallowed_tools: list[str] = Field(default_factory=list)
    context_files: list[str] = Field(default_factory=list)
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list)
    max_turns: int = Field(default=1, gt=0)  # No upper limit for complex operations

    @field_validator("system_prompt")
    @classmethod
    def load_system_prompt(cls, v):
        """Load system prompt from file if it's a path."""
        if v and Path(v).exists():
            return Path(v).read_text()
        return v

    @field_validator("context_files")
    @classmethod
    def validate_context_files(cls, v):
        """Validate that context files exist."""
        valid_files = []
        for file_path in v:
            path = Path(file_path)
            if path.exists():
                valid_files.append(str(path.absolute()))
        return valid_files

    class Config:
        json_schema_extra = {
            "example": {
                "name": "code-reviewer",
                "system_prompt": "You are a code review assistant",
                "allowed_tools": ["read", "grep"],
                "disallowed_tools": ["write", "execute"],
                "context_files": ["README.md", "docs/guidelines.md"],
                "mcp_servers": [],
                "max_turns": 1,
            }
        }


class AgentDefinition(BaseModel):
    """Agent definition with complete configuration.

    Attributes:
        name: Agent identifier
        description: Agent description
        system_prompt: System prompt text
        tool_permissions: Tool permission configuration
        context_files: List of context file paths
        max_turns: Maximum conversation turns
        metadata: Additional metadata
    """

    name: str
    description: str = Field(default="")
    system_prompt: str
    tool_permissions: ToolPermissions = Field(default_factory=ToolPermissions)
    context_files: list[Path] = Field(default_factory=list)
    max_turns: int = Field(default=1, gt=0)  # No upper limit for complex operations
    metadata: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: str | Path) -> "AgentDefinition":
        """Load agent definition from file.

        Args:
            file_path: Path to YAML or JSON file

        Returns:
            AgentDefinition instance
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Agent definition file not found: {path}")

        content = path.read_text()

        # Load based on extension
        if path.suffix in [".yml", ".yaml"]:
            import yaml

            data = yaml.safe_load(content)
        else:  # Assume JSON
            import json

            data = json.loads(content)

        return cls(**data)

    @classmethod
    def from_string(cls, prompt: str, name: str = "custom") -> "AgentDefinition":
        """Create agent definition from system prompt string.

        Args:
            prompt: System prompt text
            name: Agent name

        Returns:
            AgentDefinition instance
        """
        return cls(name=name, system_prompt=prompt)


class EnvironmentConfig(BaseModel):
    """Environment configuration for the toolkit.

    Attributes:
        working_directory: Base working directory
        session_directory: Where to store session data
        log_directory: Where to store logs
        cache_directory: Where to store cache data
        debug: Enable debug mode
    """

    working_directory: Path = Field(default_factory=Path.cwd)
    session_directory: Path = Field(default_factory=lambda: Path.home() / ".ccsdk" / "sessions")
    log_directory: Path = Field(default_factory=lambda: Path.home() / ".ccsdk" / "logs")
    cache_directory: Path = Field(default_factory=lambda: Path.home() / ".ccsdk" / "cache")
    debug: bool = Field(default=False)

    @field_validator("working_directory", "session_directory", "log_directory", "cache_directory")
    @classmethod
    def ensure_directory(cls, v):
        """Ensure directories exist."""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "working_directory": "/home/user/project",
                "session_directory": "/home/user/.ccsdk/sessions",
                "log_directory": "/home/user/.ccsdk/logs",
                "cache_directory": "/home/user/.ccsdk/cache",
                "debug": False,
            }
        }


class ToolkitConfig(BaseModel):
    """Main configuration for CCSDK toolkit.

    Attributes:
        agents: List of agent definitions
        environment: Environment configuration
        default_agent: Name of default agent to use
        retry_attempts: Global retry attempts
    """

    agents: list[AgentDefinition] = Field(default_factory=list)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    default_agent: str | None = Field(default=None)
    retry_attempts: int = Field(default=3, gt=0, le=10)

    def get_agent(self, name: str) -> AgentDefinition | None:
        """Get agent definition by name.

        Args:
            name: Agent name to find

        Returns:
            AgentDefinition or None if not found
        """
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None

    @classmethod
    def from_file(cls, file_path: str | Path) -> "ToolkitConfig":
        """Load toolkit config from file.

        Args:
            file_path: Path to YAML or JSON file

        Returns:
            ToolkitConfig instance
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        content = path.read_text()

        # Load based on extension
        if path.suffix in [".yml", ".yaml"]:
            import yaml

            data = yaml.safe_load(content)
        else:  # Assume JSON
            import json

            data = json.loads(content)

        return cls(**data)
