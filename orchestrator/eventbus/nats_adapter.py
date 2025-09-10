import asyncio, json
from typing import Callable, Awaitable, Optional
try:
    from nats.aio.client import Client as NATS
except Exception:
    NATS = None

class NATSAdapter:
    def __init__(self, servers: str = "nats://localhost:4222", subject: str = "spooky.events"):
        self.servers = servers
        self.subject = subject
        self.nc = NATS() if NATS else None

    async def connect(self):
        if not self.nc:
            raise RuntimeError("pynats not installed. pip install nats-py")
        await self.nc.connect(servers=[self.servers])

    async def publish(self, event: dict):
        data = json.dumps(event).encode("utf-8")
        await self.nc.publish(self.subject, data)

    async def subscribe(self, handler: Callable[[dict], Awaitable[None]], queue: Optional[str] = None):
        async def _cb(msg):
            try:
                payload = json.loads(msg.data.decode("utf-8"))
            except Exception:
                payload = {"raw": msg.data}
            await handler(payload)
        await self.nc.subscribe(self.subject, queue=queue, cb=_cb)

    async def close(self):
        if self.nc:
            await self.nc.drain()
