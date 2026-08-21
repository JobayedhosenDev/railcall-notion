"""Notion REST API Client with exponential backoff, rate limiting, and safe auth handling.

Uses standard Python urllib library for zero external dependencies.
Secret tokens never leak into logs or error messages.
"""

import json
import time
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


class NotionAPIError(Exception):
    """Custom exception for Notion API errors with HTTP status and Notion code."""
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"Notion API Error [{status_code} - {code}]: {message}")


class NotionClient:
    """Production-ready client for Notion REST API (v1)."""
    
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key from param or NOTION_API_KEY env var."""
        token = api_key or os.environ.get("NOTION_API_KEY", "")
        if not token:
            raise ValueError(
                "Missing Notion API Key. Provide NOTION_API_KEY environment variable "
                "or pass api_key to handler context."
            )
        self._token = token.strip()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "RailCall-Notion-Module/1.0.0"
        }

    def request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Execute HTTP request against Notion API with exponential backoff for 429 rate limits."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        data = json.dumps(payload).encode("utf-8") if payload else None

        for attempt in range(max_retries + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
            
            try:
                with urllib.request.urlopen(req) as resp:
                    resp_data = resp.read().decode("utf-8")
                    return json.loads(resp_data) if resp_data else {}
                    
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8") if e.fp else ""
                parsed_err = {}
                if err_body:
                    try:
                        parsed_err = json.loads(err_body)
                    except Exception:
                        pass
                
                code = parsed_err.get("code", "HTTP_ERROR")
                msg = parsed_err.get("message", e.reason or "An HTTP error occurred")

                # Handle Rate Limit (429) or Server Error (5xx) with retries
                if (e.code == 429 or e.code >= 500) and attempt < max_retries:
                    retry_after = int(e.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(retry_after)
                    continue

                raise NotionAPIError(status_code=e.code, code=code, message=msg) from e
                
            except urllib.error.URLError as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise NotionAPIError(status_code=500, code="NETWORK_ERROR", message=str(e.reason)) from e

        raise NotionAPIError(status_code=500, code="RETRY_EXHAUSTED", message="Max retries reached")
