# LangChain Agent — AWS Bedrock + Tools

ReAct agent built with LangGraph + LangChain, running Claude Haiku via AWS Bedrock.

## Stack

| Layer | Tech |
|---|---|
| LLM | AWS Bedrock — Claude Haiku |
| Agent | LangGraph `create_react_agent` |
| Memory | LangGraph `MemorySaver` (per session) |
| Tools | Wikipedia · S3 reader · Python REPL |
| API | FastAPI |
| UI | Streamlit |

## Project structure

```
langchain-agent/
├── agent/
│   ├── __init__.py
│   ├── tools.py        # 3 tools
│   └── agent.py        # ReAct agent + session memory
├── api/
│   ├── __init__.py
│   └── main.py         # FastAPI endpoints
├── ui/
│   └── app.py          # Streamlit chat UI
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in your AWS credentials and S3 bucket name
```

## Run

Terminal 1 — FastAPI:
```bash
uvicorn api.main:app --reload --port 8000
```

Terminal 2 — Streamlit:
```bash
streamlit run ui/app.py
```

Open http://localhost:8501

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send message, get agent response |
| `GET` | `/history/{session_id}` | Get conversation history |
| `DELETE` | `/history/{session_id}` | Clear session memory |

### Example request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the history of the Silk Road?", "session_id": "demo"}'
```

## Demo queries

```
1. "What is the history of the Silk Road?"
   → uses wikipedia_search

2. "Calculate compound interest on $10,000 at 7% for 15 years"
   → uses python_repl

3. "Read the file reports/summary.txt and summarize it"
   → uses s3_file_reader
```

## AWS Bedrock setup

1. Go to AWS Console → Bedrock → Model access
2. Request access to **Claude Haiku** (anthropic.claude-haiku-20240307-v1:0)
3. Make sure your IAM user has `bedrock:InvokeModel` permission
