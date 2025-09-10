# Spooky Logic — Codessian Adaptive Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Become the board. Absorb the game. Rewrite the rules.

The Codessian Adaptive Orchestrator is a sophisticated framework for building and managing complex, AI-driven workflows. It is designed to be highly modular, adaptable, and observable, allowing you to create, test, and deploy new strategies with ease.

## Architecture

The orchestrator is composed of several key components that work together to provide a powerful and flexible platform for AI orchestration.

*   **FastAPI Service (`api/`)**: The main entry point for the orchestrator. It provides a set of RESTful endpoints for interacting with the system, including orchestrating new goals, managing playbooks, and registering external agents.

*   **Temporal Worker (`orchestrator/`)**: The heart of the orchestrator. It uses the [Temporal](https://temporal.io/) workflow engine to execute playbooks, which are YAML files that define a sequence of steps for achieving a goal.

*   **Playbooks (`playbooks/`)**: YAML files that define the steps for achieving a goal. They can be composed of multiple steps, including calling LLMs, running external tools, and making decisions based on the results of previous steps.

*   **Policy Engine (`orchestrator/policy_engine.py`)**: A dynamic rule engine that evaluates performance metrics and triggers orchestration adaptations. It uses [OPA/Rego](https://www.openpolicyagent.org/) to enforce policies and make decisions about how to adapt the system.

*   **Metrics and Telemetry (`orchestrator/metrics.py`, `telemetry/`)**: The orchestrator is fully instrumented with [Prometheus](https://prometheus.io/) metrics and [OpenTelemetry](https://opentelemetry.io/) tracing. It also includes a [Grafana](https://grafana.com/) dashboard for visualizing the system's performance.

*   **Docker Compose (`docker-compose.yml`)**: The entire system can be run locally using Docker Compose, making it easy to get started with development.

## Quickstart

1.  **Copy the environment file and edit it to your needs:**

    ```bash
    cp .env.example .env
    ```

2.  **Bring up the infrastructure and application:**

    ```bash
    docker compose up --build -d
    ```

3.  **Hit the API to orchestrate a new goal:**

    ```bash
    curl -X POST http://localhost:8080/orchestrate \
      -H "Content-Type: application/json" \
      -d '{"goal":"Write a Python function to calculate fibonacci(n) with tests","budget_usd":0.05,"risk":2}'
    ```

## Configuration

The orchestrator is configured using a YAML file located at `config/adaptive_orchestrator.yaml`. This file contains the configuration for all the major components of the system, including the policy engine, the absorption API, and the metrics client.

The policies themselves are written in Rego and are located in the `policies/` directory.

## Contributing

We welcome contributions to the Codessian Adaptive Orchestrator! If you would like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a descriptive commit message.
4.  Push your changes to your fork.
5.  Open a pull request to the main repository.

Please make sure to add tests for your changes and to follow the existing coding style.

## API Reference

The API is documented using OpenAPI and can be accessed at `http://localhost:8080/docs` when the application is running.

## License

The Codessian Adaptive Orchestrator is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
