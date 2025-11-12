from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    use_device_code_auth: bool = True  # Use user authentication instead of app-only
    
    # Microsoft Graph Explorer client ID (public client, works for everyone)
    # Use this if your custom app isn't configured for device code flow
    use_graph_explorer_client: bool = False
    graph_explorer_client_id: str = "de8bc8b5-d9f9-48b1-a8ad-b748da725064"
    
    mcp_server_name: str = "Microsoft Planner MCP"
    mcp_server_version: str = "1.0.0"
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8080
    
    graph_api_version: str = "v1.0"
    graph_api_timeout: int = 30
    
    cache_type: str = "memory"
    cache_ttl_seconds: int = 300
    
    log_level: str = "INFO"
    log_format: str = "json"
