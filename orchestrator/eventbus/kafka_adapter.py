import json, os
from typing import Callable, Optional
try:
    from confluent_kafka import Producer, Consumer
except Exception:
    Producer = Consumer = None

class KafkaAdapter:
    """An adapter for interacting with Kafka.

    This class provides a simple interface for publishing and subscribing to
    Kafka topics. It requires the `confluent-kafka` library to be installed.
    """

    def __init__(self, brokers: str = None, topic: str = "spooky.events"):
        """Initializes the KafkaAdapter.

        Args:
            brokers: The Kafka brokers to connect to. If not provided, it
                defaults to the value of the KAFKA_BROKERS environment
                variable, or "localhost:9092" if that is not set.
            topic: The topic to publish to and subscribe from.

        Raises:
            RuntimeError: If the `confluent-kafka` library is not installed.
        """
        self.brokers = brokers or os.getenv("KAFKA_BROKERS","localhost:9092")
        self.topic = topic
        if not Producer or not Consumer:
            raise RuntimeError("confluent-kafka not installed")
        self.producer = Producer({"bootstrap.servers": self.brokers})
        self.consumer = None

    def publish(self, event: dict):
        """Publishes an event to Kafka.

        Args:
            event: The event to publish.
        """
        self.producer.produce(self.topic, json.dumps(event).encode("utf-8"))
        self.producer.poll(0)

    def subscribe(self, group_id: str, handler: Callable[[dict], None]):
        """Subscribes to a Kafka topic and handles messages.

        This method blocks and continuously polls for messages from the Kafka
        topic. When a message is received, it is passed to the provided
        handler function.

        Args:
            group_id: The consumer group ID.
            handler: The handler function for incoming messages.
        """
        self.consumer = Consumer({
            "bootstrap.servers": self.brokers,
            "group.id": group_id,
            "auto.offset.reset": "earliest"
        })
        self.consumer.subscribe([self.topic])
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None: 
                continue
            if msg.error():
                continue
            payload = json.loads(msg.value().decode("utf-8"))
            handler(payload)
