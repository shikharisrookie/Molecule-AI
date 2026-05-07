"""Run the FastAPI application with Uvicorn."""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT", "development") == "development",
        log_level="info",
    )
