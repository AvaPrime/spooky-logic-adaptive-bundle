from prometheus_client import Counter, Histogram

submissions = Counter("spooky_submissions_total", "Tasks submitted")
accuracy = Histogram("spooky_task_accuracy", "Outcome score", buckets=[0.5, 0.7, 0.8, 0.9, 0.95, 1.0])
latency = Histogram("spooky_latency_ms", "End-to-end latency (ms)", buckets=[200, 500, 1000, 2000, 5000, 10000])
cost = Histogram("spooky_cost_usd", "Estimated cost (USD)", buckets=[0.005,0.01,0.025,0.05,0.1,0.25,0.5,1.0])
