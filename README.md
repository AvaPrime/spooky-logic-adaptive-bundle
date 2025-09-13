# Spooky Logic — Codessian Adaptive Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Become the board. Absorb the game. Rewrite the rules.

The Codessian Adaptive Orchestrator is a sophisticated, AI-driven framework designed for building, managing, and dynamically adapting complex workflows. It moves beyond static, predefined processes by continuously observing its own performance and making intelligent, real-time adjustments. By leveraging a powerful policy engine and a flexible playbook system, the orchestrator can swap agents, modify strategies, and evolve its behavior to meet specific goals related to cost, risk, and accuracy.

This project is built to be highly modular, observable, and resilient, providing a robust platform for developing and deploying advanced, self-adapting AI systems.

## Core Concepts

*   **Playbooks**: YAML-based plans that define the high-level steps required to achieve a goal. They are not rigid scripts but flexible strategies that can be adapted by the orchestrator.
*   **Adaptive Policy Engine**: A dynamic, learning-based rule engine that monitors system metrics. When conditions are met (e.g., performance degradation or budget thresholds), it triggers adaptation actions, such as swapping an AI agent or enabling a different operational mode.
*   **Orchestration**: The process of executing a playbook. The orchestrator uses Temporal workflows to ensure that these, often long-running, processes are executed reliably.
*   **Federation & Marketplace**: The system can be extended with new capabilities, agents, and playbooks from a federated marketplace, allowing for dynamic updates and a growing ecosystem of tools.

## Project Structure

Here is a high-level overview of the repository's structure:

```
.
├── api/                  # FastAPI application providing the main REST API.
├── cli/                  # Command-line interfaces for interacting with the system.
├── codessian/            # Core adaptive orchestrator logic.
├── marketplace/          # Client for fetching and verifying marketplace assets.
├── orchestrator/         # Temporal workflows, activities, and the core policy engine.
├── playbooks/            # Example YAML playbooks.
├── policies/             # Example YAML policies for the adaptive engine.
├── tests/                # Unit and integration tests.
├── .env.example          # Example environment file.
├── docker-compose.yml    # Docker Compose for local development.
└── README.md             # This file.
```

## Architecture Components

The orchestrator is composed of several key components that work together to provide a powerful and flexible platform.

*   **FastAPI Service (`api/`)**: The primary entry point for the orchestrator. It exposes a RESTful API for initiating tasks, managing resources, and querying the system's state. It is documented using OpenAPI and can be accessed at `/docs`.

*   **Temporal Worker & Workflows (`orchestrator/`)**: The heart of the execution engine. It uses the [Temporal](https://temporal.io/) workflow engine to reliably execute playbooks as long-running, fault-tolerant processes. This directory also contains the core activities that workflows can schedule.

*   **Adaptive Policy Engine (`orchestrator/policy_engine.py`)**: A sophisticated, learning-based rule engine that drives the "adaptive" nature of the orchestrator. Unlike static rule engines, it monitors performance metrics against YAML-defined policies and can trigger a variety of adaptations, such as swapping agents, enabling debate modes, or adjusting routing logic.

*   **CLI (`cli/`)**: Provides command-line tools (`spookyctl` and `spookyfed`) for developers and administrators to interact with the orchestrator, manage federation, and perform administrative tasks directly from the terminal.

*   **Playbooks (`playbooks/`)**: User-defined YAML files that outline a strategy for achieving a goal. They define a sequence of steps, which can include calling LLMs, running external tools, and making decisions.

*   **Marketplace Client (`marketplace/`)**: A client for interacting with a marketplace of community-contributed assets. It includes functions for securely downloading and cryptographically verifying the integrity of manifests for new playbooks, agents, and capabilities.

*   **Metrics and Telemetry (`orchestrator/telemetry/`)**: The orchestrator is fully instrumented with [Prometheus](https://prometheus.io/) metrics and [OpenTelemetry](https://opentelemetry.io/) tracing, providing deep visibility into the system's performance and behavior.

*   **Docker Compose (`docker-compose.yml`)**: The entire system, including the Temporal cluster, Grafana, and Prometheus, can be run locally using Docker Compose, making it easy to get started with development.

## Quickstart

1.  **Copy the environment file.** This file contains environment variables for connecting to services like Temporal and OpenAI. Edit it to your needs.

    ```bash
    cp .env.example .env
    ```

2.  **Bring up the infrastructure and application.** This command will build the Docker images and start all services in the background.

    ```bash
    docker compose up --build -d
    ```

3.  **Orchestrate a new goal via the API.** Use `curl` to send a request to the orchestrator. This example asks the system to write a Fibonacci function, with a budget of $0.05 and a medium risk tolerance.

    ```bash
    curl -X POST http://localhost:8080/orchestrate \
      -H "Content-Type: application/json" \
      -d '{"goal":"Write a Python function to calculate fibonacci(n) with tests","budget_usd":0.05,"risk":2}'
    ```

## Configuration

The orchestrator's behavior is primarily configured through two sets of YAML files:

*   **Orchestrator Configuration (`config/adaptive_orchestrator.yaml`)**: This file contains the master configuration for the system, including settings for the policy engine, absorption API, and metrics clients.
*   **Policy Files (`policies/`)**: These YAML files define the rules for the adaptive policy engine. Each policy specifies a trigger (e.g., `performance_degradation`), one or more conditions (e.g., `agent.accuracy < 0.8`), and an action to take (e.g., `swap_agent`).

## Contributing

We welcome contributions! If you would like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a descriptive commit message.
4.  Add or update tests for your changes.
5.  Ensure your code follows the existing style.
6.  Push your changes to your fork.
7.  Open a pull request to the main repository.

## API Reference

The API is documented using OpenAPI. Once the application is running, the interactive documentation can be accessed at [http://localhost:8080/docs](http://localhost:8080/docs).

## License

The Codessian Adaptive Orchestrator is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
