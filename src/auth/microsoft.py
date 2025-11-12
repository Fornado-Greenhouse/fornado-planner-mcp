from msal import ConfidentialClientApplication
from typing import Optional, Dict, Any
import time
import structlog

logger = structlog.get_logger()


class MicrosoftAuthManager:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        authority: Optional[str] = None
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.authority = authority or f"https://login.microsoftonline.com/{tenant_id}"
        
        self._app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
        
        self._token_cache: Dict[str, Any] = {}
        
    def get_app_token(self, scopes: Optional[list] = None) -> str:
        scopes = scopes or ["https://graph.microsoft.com/.default"]
        cache_key = "|".join(sorted(scopes))
        
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if cached["expires_at"] > time.time() + 300:
                return cached["access_token"]
        
        result = self._app.acquire_token_for_client(scopes=scopes)
        
        if result and "access_token" in result:
            expires_in = result.get("expires_in")
            if isinstance(expires_in, (int, float)):
                expires_at = time.time() + expires_in
            else:
                expires_at = time.time() + 3600
                
            self._token_cache[cache_key] = {
                "access_token": result["access_token"],
                "expires_at": expires_at
            }
            logger.info("acquired_new_token", scopes=scopes)
            return result["access_token"]
        
        error_msg = f"Failed to acquire token: {result.get('error_description', 'Unknown error') if result else 'No result'}"
        logger.error("token_acquisition_failed", error=result.get("error") if result else "unknown")
        raise Exception(error_msg)
    
    def get_delegated_token(self, scopes: Optional[list] = None) -> str:
        scopes = scopes or ["Tasks.ReadWrite", "User.Read"]
        logger.info("delegated_auth_not_implemented")
        raise NotImplementedError("Delegated authentication not implemented in this version")
    
    def validate_token(self, token: str) -> bool:
        return True
