"""Request boundaries shared by gameplay and authentication."""

import asyncio
import logging
import time
from collections import OrderedDict

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse

logger = logging.getLogger("uvicorn.error.security")
MAX_BODY = 8192
WINDOW_SECONDS = 60
MAX_BUCKETS = 10_000


class RequestGuard:
    def __init__(self, app, production=False):
        self.app = app
        self.production = production
        self.buckets = OrderedDict()
        self.auth_slots = asyncio.Semaphore(4)

    def rate_limited(self, client, group, limit):
        now = time.monotonic()
        while self.buckets and next(iter(self.buckets.values()))[0] <= now:
            self.buckets.popitem(last=False)
        key = (client, group)
        entry = self.buckets.get(key)
        if entry is None:
            if len(self.buckets) >= MAX_BUCKETS:
                return True
            self.buckets[key] = (now + WINDOW_SECONDS, 1)
            return False
        expires, count = entry
        self.buckets[key] = (expires, count + 1)
        return count >= limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Referrer-Policy"] = "no-referrer"
                headers["X-Frame-Options"] = "DENY"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                if scope["path"].startswith("/api/"):
                    headers["Cache-Control"] = "no-store"
                    headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                if self.production:
                    headers["Strict-Transport-Security"] = "max-age=31536000"
            await send(message)

        async def reject(status, reason, group, headers=None):
            logger.warning("request_rejected group=%s status=%d", group, status)
            await JSONResponse({"detail": reason}, status, headers)(scope, receive, secure_send)

        if self.production and scope["scheme"] != "https":
            await reject(400, "HTTPS is required", "transport")
            return

        path = scope["path"]
        method = scope["method"]

        async def forward(receiver):
            if self.production and path.startswith("/api/auth/"):
                if self.auth_slots.locked():
                    await reject(429, "Authentication is busy. Try again shortly.", "authentication")
                    return
                async with self.auth_slots:
                    await self.app(scope, receiver, secure_send)
            else:
                await self.app(scope, receiver, secure_send)

        if self.production and (method == "POST" or path.startswith("/api/auth/google/")):
            group, limit = ("authentication", 20) if path.startswith("/api/auth/") else ("gameplay", 120)
            client = scope.get("client") or ("unknown", 0)
            if self.rate_limited(client[0], group, limit):
                await reject(429, "Too many requests. Try again shortly.", group, {"Retry-After": "60"})
                return

        if method != "POST":
            await forward(receive)
            return

        content_type = Headers(scope=scope).get("content-type", "").split(";")[0].strip().lower()
        body = bytearray()
        deadline = asyncio.get_running_loop().time() + 5
        while True:
            try:
                async with asyncio.timeout_at(deadline):
                    part = await receive()
            except TimeoutError:
                await reject(408, "Request body timed out", "body")
                return
            if part["type"] == "http.disconnect":
                return
            chunk = part.get("body", b"")
            if len(body) + len(chunk) > MAX_BODY:
                await reject(413, "Request body is too large", "body")
                return
            body.extend(chunk)
            if not part.get("more_body"):
                break

        if body and content_type != "application/json":
            await reject(415, "Use application/json", "body")
            return

        first_receive = True

        async def buffered_receive():
            nonlocal first_receive
            if first_receive:
                first_receive = False
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await forward(buffered_receive)
