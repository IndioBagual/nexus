from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from hub.repo import HubRepo

app = FastAPI(title="NEXUS Sync Hub")
repo = HubRepo()


class Operation(BaseModel):
    op_id: str
    actor_id: str
    entity_type: str
    entity_id: str
    action: str
    payload: dict[str, Any]
    timestamp: str


class PushRequest(BaseModel):
    operations: list[Operation]


@app.post("/sync/push")
def push(req: PushRequest):
    # Converte Pydantic para lista de dicts
    ops_dict = [op.dict() for op in req.operations]
    inserted = repo.push_ops(ops_dict)
    return {"status": "success", "inserted": inserted}


@app.get("/sync/pull")
def pull(cursor: int = 0):
    ops = repo.pull_ops(cursor)
    return {"status": "success", "operations": ops}
