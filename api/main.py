from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid

from agent.agent import run_agent, get_history, clear_history

app = FastAPI(
    title="LangChain Agent API",
    description="ReAct agent with Wikipedia, S3, and Python REPL tools",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message / question")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Session ID for conversation memory. Auto-generated if omitted.",
    )


class ChatResponse(BaseModel):
    session_id: str
    answer: str


class HistoryItem(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryItem]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "LangChain Agent API is running"}


@app.post("/chat", response_model=ChatResponse, tags=["agent"])
async def chat(req: ChatRequest):
    """
    Send a message to the agent and get a response.
    The agent will automatically decide which tools to use.
    """
    try:
        result = run_agent(message=req.message, session_id=req.session_id)
        return ChatResponse(session_id=result["session_id"], answer=result["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{session_id}", response_model=HistoryResponse, tags=["memory"])
async def history(session_id: str):
    """Return conversation history for a session."""
    try:
        messages = get_history(session_id)
        return HistoryResponse(
            session_id=session_id,
            messages=[HistoryItem(**m) for m in messages],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{session_id}", tags=["memory"])
async def delete_history(session_id: str):
    """Clear conversation memory for a session."""
    try:
        clear_history(session_id)
        return {"cleared": True, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
