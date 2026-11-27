"""Admission controls for bounded lesson requests."""

import logging
import os
import time
from collections import OrderedDict
from contextlib import contextmanager
from threading import Lock

from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error.security")
WINDOW = 60
REQUESTS_PER_USER = 30
MAX_USERS = 2048
MAX_ACTIVE = 4


class ConsoleGate:
    def __init__(self):
        self.lock = Lock()
        self.active = set()
        self.buckets = OrderedDict()
        self.policy_events = 0
        self.policy_window = 0

    @contextmanager
    def admit(self, user_id, *, execute):
        mode = os.getenv("CYBERHEIST_CONSOLE_MODE", "simulation")
        if mode not in {"simulation", "disabled"} or (execute and mode == "disabled"):
            raise HTTPException(503, "Console execution is temporarily disabled")
        with self.lock:
            now = time.monotonic()
            while self.buckets and next(iter(self.buckets.values()))[0] <= now:
                self.buckets.popitem(last=False)
            expires, count = self.buckets.get(user_id, (now + WINDOW, 0))
            if (count >= REQUESTS_PER_USER or user_id in self.active or len(self.active) >= MAX_ACTIVE
                    or (user_id not in self.buckets and len(self.buckets) >= MAX_USERS)):
                raise HTTPException(429, "Console request limit reached. Try again shortly.",
                                    headers={"Retry-After": str(WINDOW)})
            self.buckets[user_id] = (expires, count + 1)
            self.active.add(user_id)
        try:
            yield
        finally:
            with self.lock:
                self.active.remove(user_id)

    def policy_rejection(self):
        with self.lock:
            now = time.monotonic()
            if now >= self.policy_window:
                self.policy_window = now + WINDOW
                self.policy_events = 0
            self.policy_events += 1
            if self.policy_events == 10:
                logger.warning("console_policy_rejections threshold=10 window_seconds=60")


console_gate = ConsoleGate()
