from contextlib import asynccontextmanager

from fastapi import FastAPI

from .agent import PromptAgent
from .config import POLICY_PATH
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.prompt_agent = PromptAgent(POLICY_PATH)
    yield


app = FastAPI(
    title="PromptCheck",
    version="1.0.0",
    description="API educativa para inspeccionar prompts y sugerir mejoras reproducibles.",
    lifespan=lifespan,
)
app.include_router(router)
