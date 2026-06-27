import os
import subprocess
import boto3
import wikipediaapi
from langchain_core.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun

# Tool 1: Wikipedia search


def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a summary."""
    try:
        wiki = wikipediaapi.Wikipedia(
            language="en",
            user_agent="langchain-agent-demo/1.0"
        )
        page = wiki.page(query)
        if not page.exists():
            return f"No Wikipedia page found for: '{query}'. Try a different search term."
        summary = page.summary
        # Cap at 1500 chars to avoid flooding the context window
        return summary[:1500] + ("..." if len(summary) > 1500 else "")
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"


wikipedia_tool = Tool(
    name="wikipedia_search",
    func=search_wikipedia,
    description=(
        "Search Wikipedia for factual information about a topic. "
        "Input: a plain search query string (e.g. 'Silk Road history'). "
        "Use for: historical facts, scientific concepts, biographies, definitions. "
        "Do NOT use for real-time data like prices or current events."
    ),
)


# Tool 2: S3 file reader

def read_s3_file(key: str) -> str:
    """Read a text file from S3. Input: S3 object key like 'reports/summary.txt'."""
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        return "Error: S3_BUCKET_NAME environment variable is not set."
    try:
        s3 = boto3.client("s3")
        key = key.strip().strip("/")
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        # Cap at 3000 chars
        return content[:3000] + ("...[truncated]" if len(content) > 3000 else "")
    except s3.exceptions.NoSuchKey:
        return f"File not found in S3: '{key}'"
    except Exception as e:
        return f"S3 read failed: {str(e)}"


s3_tool = Tool(
    name="s3_file_reader",
    func=read_s3_file,
    description=(
        "Read the contents of a text file stored in S3. "
        "Input: the S3 object key (file path) like 'reports/q3.txt' or 'data/notes.md'. "
        "Use when the user asks about a specific file or document stored in the cloud."
    ),
)


# Tool 3: Python REPL (subprocess-sandboxed)

def run_python(code: str) -> str:
    """Execute Python code in a subprocess and return stdout or stderr."""
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return output if output else "Code executed successfully with no output."
        else:
            return f"Error:\n{result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Execution timed out after 10 seconds."
    except Exception as e:
        return f"Failed to run code: {str(e)}"


python_tool = Tool(
    name="python_repl",
    func=run_python,
    description=(
        "Execute Python 3 code and return the printed output. "
        "Input: valid Python code as a string. "
        "Use for: math calculations, date arithmetic, string processing, data analysis. "
        "Always use print() to show results. Example: 'print(2 ** 10)'"
    ),
)

# Tool 4: DuckDuckGo search
_ddg = DuckDuckGoSearchRun()


def search_web(query: str) -> str:
    """Search the web via DuckDuckGo and return top results."""

    try:
        result = _ddg.run(query)
        return result[:2000] + ("..." if len(result) > 2000 else "")
    except Exception as e:
        return f"Web search failed: {str(e)}"


duckduckgo_tool = Tool(
    name="web_search",
    func=search_web,
    description=(
        "Search the web for current information, news, prices, or recent events. "
        "Input: a search query string (e.g. 'Python 3.13 release date'). "
        "Use for: anything that changes over time, current events, prices, "
        "recent tech releases. Prefer wikipedia_search for stable factual topics."
    ),
)


# Export

tools = [
    wikipedia_tool,
    # s3_tool,
    duckduckgo_tool,
    python_tool,
]
