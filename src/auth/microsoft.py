from msal import PublicClientApplication, ConfidentialClientApplication
from typing import Optional, Dict, Any
import time
import structlog
import json
import os

logger = structlog.get_logger()

TOKEN_CACHE_FILE = ".token_cache.json"


class MicrosoftAuthManager:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: Optional[str] = None,
        authority: Optional[str] = None,
        use_device_code: bool = False
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.authority = authority or f"https://login.microsoftonline.com/{tenant_id}"
        self.use_device_code = use_device_code
        
        if use_device_code or not client_secret:
            # Public client for device code flow (user authentication)
            self._app = PublicClientApplication(
                client_id=client_id,
                authority=self.authority
            )
            self._is_public = True
        else:
            # Confidential client for client credentials (app-only authentication)
            self._app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=self.authority
            )
            self._is_public = False
        
        self._token_cache: Dict[str, Any] = {}
        self._load_token_cache()
        
    def _load_token_cache(self):
        """Load cached tokens from file"""
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    self._token_cache = json.load(f)
                logger.info("loaded_token_cache")
            except Exception as e:
                logger.warning("failed_to_load_cache", error=str(e))
                self._token_cache = {}
    
    def _save_token_cache(self):
        """Save tokens to cache file"""
        try:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                json.dump(self._token_cache, f)
            logger.debug("saved_token_cache")
        except Exception as e:
            logger.warning("failed_to_save_cache", error=str(e))
    
    def get_token(self, scopes: Optional[list] = None) -> str:
        """
        Get an access token using the appropriate flow.
        For public clients, uses device code flow.
        For confidential clients, uses client credentials flow.
        """
        if self._is_public:
            return self.get_user_token(scopes)
        else:
            return self.get_app_token(scopes)
    
    def get_app_token(self, scopes: Optional[list] = None) -> str:
        """Get app-only token using client credentials"""
        if self._is_public:
            raise Exception("Cannot use app-only authentication with public client")
            
        scopes = scopes or ["https://graph.microsoft.com/.default"]
        cache_key = f"app:{':'.join(sorted(scopes))}"
        
        # Check cache
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if cached["expires_at"] > time.time() + 300:
                return cached["access_token"]
        
        # Acquire new token
        result = self._app.acquire_token_for_client(scopes=scopes)
        
        if result and "access_token" in result:
            expires_in = result.get("expires_in", 3600)
            expires_at = time.time() + expires_in
                
            self._token_cache[cache_key] = {
                "access_token": result["access_token"],
                "expires_at": expires_at
            }
            self._save_token_cache()
            logger.info("acquired_app_token", scopes=scopes)
            return result["access_token"]
        
        error_msg = f"Failed to acquire token: {result.get('error_description', 'Unknown error') if result else 'No result'}"
        logger.error("token_acquisition_failed", error=result.get("error") if result else "unknown")
        raise Exception(error_msg)
    
    def get_user_token(self, scopes: Optional[list] = None) -> str:
        """Get user token using device code flow"""
        if not self._is_public:
            raise Exception("Cannot use device code flow with confidential client")
        
        scopes = scopes or [
            "Tasks.ReadWrite",
            "Tasks.ReadWrite.Shared", 
            "Group.Read.All",
            "User.Read"
        ]
        cache_key = f"user:{':'.join(sorted(scopes))}"
        
        # Check cache first
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if cached.get("expires_at", 0) > time.time() + 300:
                logger.info("using_cached_user_token")
                return cached["access_token"]
        
        # Try silent token acquisition first (if we have an account)
        accounts = self._app.get_accounts()
        if accounts:
            logger.info("attempting_silent_token_acquisition", account=accounts[0].get("username"))
            result = self._app.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                self._cache_user_token(cache_key, result)
                logger.info("acquired_user_token_silently")
                return result["access_token"]
        
        # Need interactive authentication - use device code flow
        logger.info("starting_device_code_flow")
        flow = self._app.initiate_device_flow(scopes=scopes)
        
        if "user_code" not in flow:
            raise Exception(f"Failed to initiate device code flow: {flow.get('error_description')}")
        
        # Display instructions to user
        print("\n" + "="*60)
        print("MICROSOFT AUTHENTICATION REQUIRED")
        print("="*60)
        print(flow["message"])
        print("="*60 + "\n")
        
        # Wait for user to complete authentication
        result = self._app.acquire_token_by_device_flow(flow)
        
        if result and "access_token" in result:
            self._cache_user_token(cache_key, result)
            logger.info("acquired_user_token_via_device_code", account=result.get("account", {}).get("username"))
            print("\n✅ Authentication successful!\n")
            return result["access_token"]
        
        error_msg = f"Failed to acquire user token: {result.get('error_description', 'Unknown error') if result else 'No result'}"
        logger.error("user_token_acquisition_failed", error=result.get("error") if result else "unknown")
        raise Exception(error_msg)
    
    def _cache_user_token(self, cache_key: str, result: Dict[str, Any]):
        """Cache a user token"""
        expires_in = result.get("expires_in", 3600)
        expires_at = time.time() + expires_in
        
        self._token_cache[cache_key] = {
            "access_token": result["access_token"],
            "expires_at": expires_at,
            "account": result.get("account", {}).get("username")
        }
        self._save_token_cache()
    
    def clear_cache(self):
        """Clear all cached tokens"""
        self._token_cache = {}
        if os.path.exists(TOKEN_CACHE_FILE):
            os.remove(TOKEN_CACHE_FILE)
        logger.info("cleared_token_cache")
    
    def get_cached_account(self) -> Optional[str]:
        """Get the cached user account if any"""
        for key, value in self._token_cache.items():
            if key.startswith("user:") and "account" in value:
                return value["account"]
        return None
    
    def validate_token(self, token: str) -> bool:
        """Validate a token (basic check)"""
        return bool(token and len(token) > 10)
