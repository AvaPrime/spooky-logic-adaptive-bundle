"""
Temporal Worker for Spooky Orchestrator
=======================================

This module defines the Temporal worker and workflow for executing playbooks.
The worker listens on a specific task queue for orchestration requests,
executes the corresponding playbook as a Temporal activity, and returns the
result.
"""
import os
import asyncio
from datetime import timedelta
from temporalio import worker, workflow
from temporalio.client import Client
from orchestrator.playbook_exec import run_playbook

class TaskInput(workflow.TypedDict, total=False):
    """
    Defines the input structure for the Orchestrate workflow.

    Attributes:
        goal (str): The high-level goal for the orchestration.
        playbook (str): The name of the playbook to execute.
        budget (float): The maximum budget allocated for the task.
        risk (int): The risk tolerance level for the task execution.
    """
    goal: str
    playbook: str
    budget: float
    risk: int

@workflow.defn
class Orchestrate:
    """
    Temporal workflow definition for orchestrating a playbook execution.

    This workflow is responsible for taking a task, executing the specified
    playbook as a Temporal activity, and ensuring its completion or failure
    is handled correctly.
    """
    @workflow.run
    async def run(self, task: TaskInput) -> dict:
        """
        Executes the playbook as a Temporal activity.

        This is the entry point for the workflow's execution. It schedules the
        `run_playbook` function as an activity with a timeout.

        Args:
            task (TaskInput): The input parameters for the workflow, including
                the playbook name, goal, budget, and risk level.

        Returns:
            dict: The result returned by the `run_playbook` activity.
        """
        return await workflow.execute_activity(
            run_playbook,
            task['playbook'],
            task['goal'],
            task['budget'],
            task['risk'],
            start_to_close_timeout=timedelta(seconds=120)
        )

async def main():
    """
    The main entry point for the Temporal worker process.

    This function connects to the Temporal server, initializes a worker,
    registers the `Orchestrate` workflow and `run_playbook` activity,
    and starts listening for tasks on the 'spooky-orchestrations' queue.
    """
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))
    w = worker.Worker(
        client,
        task_queue="spooky-orchestrations",
        workflows=[Orchestrate],
        activities=[run_playbook]
    )
    print("Worker started. Listening on task_queue spooky-orchestrations")
    await w.run()
