import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from api.routes import router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 環境變數未設定")
    app.state.genai_client = genai.Client(api_key=api_key)
    yield
    # cleanup (nothing needed for genai client)


app = FastAPI(title="DigiFlow API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
