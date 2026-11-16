from fastapi import APIRouter, Request

from .schemas import PromptRequest, PromptResponse

router = APIRouter(prefix="/api/v1")


@router.post(
    "/prompts/analizar",
    response_model=PromptResponse,
    summary="Analizar o revisar un prompt",
    description=(
        "Calcula métricas del texto. En modo revision también aplica "
        "los criterios de la skill auditar-prompts y devuelve sugerencias."
    ),
)
def analyze_prompt(payload: PromptRequest, request: Request) -> PromptResponse:
    return request.app.state.prompt_agent.process(payload)
