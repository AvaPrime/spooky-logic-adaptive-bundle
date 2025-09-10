from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, psycopg2

router = APIRouter(prefix="/expstore", tags=["experiments-store"])

def conn():
    """Establishes a connection to the PostgreSQL database."""
    dsn = os.getenv("POSTGRES_URL", "postgresql://spooky:spooky@postgres:5432/spooky")
    return psycopg2.connect(dsn)

class CreateExp(BaseModel):
    """Request model for the /create endpoint."""
    name: str

@router.post("/create")
def create_exp(req: CreateExp):
    """
    Creates a new experiment.

    Args:
        req (CreateExp): The request to create a new experiment.

    Returns:
        dict: A dictionary containing the ID and name of the new experiment.
    """
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO experiments(name) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id", (req.name,))
            if cur.rowcount == 0:
                cur.execute("SELECT id FROM experiments WHERE name=%s", (req.name,))
            exp_id = cur.fetchone()[0]
    return {"id": exp_id, "name": req.name}

class Record(BaseModel):
    """Request model for the /record endpoint."""
    experiment: str
    arm: str
    score: float
    cost: float
    latency_ms: float
    domain: str = "general"

@router.post("/record")
def record(r: Record):
    """
    Records an experiment result in the database.

    Args:
        r (Record): The experiment result to record.

    Returns:
        dict: A dictionary indicating success.

    Raises:
        HTTPException: If the experiment is not found.
    """
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT id FROM experiments WHERE name=%s", (r.experiment,))
            row = cur.fetchone()
            if not row: raise HTTPException(404, "experiment not found")
            exp_id = row[0]
            cur.execute("INSERT INTO experiment_arm(experiment_id, name) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING id", (exp_id, r.arm))
            if cur.rowcount == 0:
                cur.execute("SELECT id FROM experiment_arm WHERE experiment_id=%s AND name=%s", (exp_id, r.arm))
            arm_id = cur.fetchone()[0]
            cur.execute("INSERT INTO experiment_result(arm_id, score, cost, latency_ms, domain) VALUES (%s,%s,%s,%s,%s)", (arm_id, r.score, r.cost, r.latency_ms, r.domain))
    return {"ok": True}
