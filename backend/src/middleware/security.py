"""
Security middleware for the FastAPI application.
Includes security headers and rate limiting for production deployment.
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from collections import defaultdict, deque
from typing import Dict, Deque
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers for production
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (CSP)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # HTTPS enforcement headers (for production)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests per IP address."""
    
    def __init__(
        self, 
        app: ASGIApp, 
        requests_per_minute: int = 60,
        auth_requests_per_minute: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        # Dictionary to store request times for each IP
        self.request_times: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.auth_request_times: Dict[str, Deque[float]] = defaultdict(lambda: deque())
    
    def _cleanup_old_requests(self, request_times: Deque[float], window_seconds: int = 60):
        """Remove requests older than the time window."""
        current_time = time.time()
        while request_times and request_times[0] < current_time - window_seconds:
            request_times.popleft()
    
    def _is_rate_limited(self, ip: str, path: str) -> bool:
        """Check if the IP is rate limited for the given path."""
        current_time = time.time()
        
        # Different limits for auth endpoints
        if path.startswith('/auth/'):
            self._cleanup_old_requests(self.auth_request_times[ip])
            if len(self.auth_request_times[ip]) >= self.auth_requests_per_minute:
                return True
            self.auth_request_times[ip].append(current_time)
        else:
            self._cleanup_old_requests(self.request_times[ip])
            if len(self.request_times[ip]) >= self.requests_per_minute:
                return True
            self.request_times[ip].append(current_time)
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, request.url.path):
            logger.warning(f"Rate limit exceeded for IP {client_ip} on path {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later."
                    }
                },
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests for security monitoring."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request details
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request with security-relevant information
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} ({user_agent}) "
            f"-> {response.status_code} in {process_time:.3f}s"
        )
        
        # Log suspicious patterns
        if response.status_code == 401:
            logger.warning(f"Authentication failure from {client_ip} on {request.url.path}")
        elif response.status_code >= 500:
            logger.error(f"Server error {response.status_code} for {client_ip} on {request.url.path}")
        
        return response