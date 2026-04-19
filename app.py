"""
Compatibility entrypoint for local runs.

This keeps `uvicorn app:app` working while delegating to the maintained
application in `src.main`, whose API routes match the frontend.
"""

from src.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=False)
