import os, asyncio
from temporalio import worker, workflow
from temporalio.client import Client
from orchestrator.playbook_exec import run_playbook

class TaskInput(workflow.TypedDict, total=False):
    goal: str
    playbook: str
    budget: float
    risk: int

@workflow.defn
class Orchestrate:
    @workflow.run
    async def run(self, task: TaskInput) -> dict:
        return await workflow.execute_activity(run_playbook, task['playbook'], task['goal'], task['budget'], task['risk'], start_to_close_timeout=timedelta(seconds=120))

async def main():
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))
    async with worker.Worker(client, task_queue="spooky-orchestrations", workflows=[Orchestrate], activities=[run_playbook]):
        print("Worker started. Listening on task_queue spooky-orchestrations")
        await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
