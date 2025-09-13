import asyncio, json
from typing import Callable, Awaitable, Optional
try:
    from nats.aio.client import Client as NATS
except Exception:
    NATS = None

class NATSAdapter:
    """An adapter for interacting with NATS.

    This class provides a simple interface for connecting to, publishing to, and
    subscribing to NATS subjects. It requires the `nats-py` library to be
    installed.
    """
    def __init__(self, servers: str = "nats://localhost:4222", subject: str = "spooky.events"):
        """Initializes the NATSAdapter.

        Args:
            servers: The NATS servers to connect to.
            subject: The subject to publish to and subscribe from.
        """
        self.servers = servers
        self.subject = subject
        self.nc = NATS() if NATS else None

    async def connect(self):
        """Connects to the NATS server.

        Raises:
            RuntimeError: If the `nats-py` library is not installed.
        """
        if not self.nc:
            raise RuntimeError("pynats not installed. pip install nats-py")
        await self.nc.connect(servers=[self.servers])

    async def publish(self, event: dict):
        """Publishes an event to NATS.

        Args:
            event: The event to publish.
        """
        data = json.dumps(event).encode("utf-8")
        await self.nc.publish(self.subject, data)

    async def subscribe(self, handler: Callable[[dict], Awaitable[None]], queue: Optional[str] = None):
        """Subscribes to a NATS subject and handles messages.

        This method subscribes to the NATS subject and registers a callback
        function to handle incoming messages.

        Args:
            handler: The handler function for incoming messages.
            queue: The queue to subscribe to.
        """
        async def _cb(msg):
            try:
                payload = json.loads(msg.data.decode("utf-8"))
            except Exception:
                payload = {"raw": msg.data}
            await handler(payload)
        await self.nc.subscribe(self.subject, queue=queue, cb=_cb)

    async def close(self):
        """Closes the NATS connection."""
        if self.nc:
            await self.nc.drain()
