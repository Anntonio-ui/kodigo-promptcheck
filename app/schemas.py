from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Prompt = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=3000)
]


class PromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: Prompt = Field(
        description="Texto que se inspeccionará como datos.",
        examples=["Resume el capítulo 2."],
    )
    modo: Literal["analisis", "revision"] = Field(
        default="revision",
        description="La revisión aplica la skill. El análisis solo calcula métricas.",
    )


class Hallazgo(BaseModel):
    criterio: str
    detectado: bool
    sugerencia: str | None


class PromptResponse(BaseModel):
    caracteres: int
    palabras: int
    skill_aplicada: str | None
    estado: Literal["analizado", "listo", "requiere_revision"]
    hallazgos: list[Hallazgo]
