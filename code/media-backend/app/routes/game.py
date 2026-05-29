from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from app.services import llm_proxy

router = APIRouter()

class DetectiveRequest(BaseModel):
    start: str
    end: str
    history: List[Dict] # [{text: str, status: str}, ...]
    config: Dict = {} # Optional runtime config: api_key, provider, base_url, model

@router.post("/detective")
def api_detective_turn(req: DetectiveRequest):
    """
    海龟汤侦探回合
    """
    try:
        response = llm_proxy.detective_turn(req.start, req.end, req.history, req.config)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reveal")
def api_reveal_turn(req: DetectiveRequest):
    """
    强制揭露真相
    """
    try:
        response = llm_proxy.reveal_truth(req.start, req.end, req.history, req.config)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
