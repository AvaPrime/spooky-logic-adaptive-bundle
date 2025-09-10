import json, os
from typing import Callable, Optional
try:
    from confluent_kafka import Producer, Consumer
except Exception:
    Producer = Consumer = None

class KafkaAdapter:
    def __init__(self, brokers: str = None, topic: str = "spooky.events"):
        self.brokers = brokers or os.getenv("KAFKA_BROKERS","localhost:9092")
        self.topic = topic
        if not Producer or not Consumer:
            raise RuntimeError("confluent-kafka not installed")
        self.producer = Producer({"bootstrap.servers": self.brokers})
        self.consumer = None

    def publish(self, event: dict):
        self.producer.produce(self.topic, json.dumps(event).encode("utf-8"))
        self.producer.poll(0)

    def subscribe(self, group_id: str, handler: Callable[[dict], None]):
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
