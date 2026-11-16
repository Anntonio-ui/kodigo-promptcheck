import re
from pathlib import Path

from pydantic import BaseModel, Field

from .config import SKILL_NAME
from .schemas import Hallazgo, PromptRequest, PromptResponse


class Criterio(BaseModel):
    id: str = Field(min_length=1)
    marcadores: list[str] = Field(min_length=1)
    sugerencia: str = Field(min_length=1)


class Politica(BaseModel):
    criterios: list[Criterio] = Field(min_length=1)


class PromptAgent:
    def __init__(self, policy_path: Path):
        policy = Politica.model_validate_json(policy_path.read_text(encoding="utf-8"))
        self.rules = [
            (
                rule,
                re.compile(
                    r"(?<!\w)(?:" + "|".join(re.escape(marker) for marker in rule.marcadores) + r")(?!\w)",
                    re.IGNORECASE,
                ),
            )
            for rule in policy.criterios
        ]

    def process(self, request: PromptRequest) -> PromptResponse:
        prompt = request.prompt
        metrics = {"caracteres": len(prompt), "palabras": len(prompt.split())}
        if request.modo == "analisis":
            return PromptResponse(
                **metrics, skill_aplicada=None, estado="analizado", hallazgos=[]
            )

        findings = []
        for rule, pattern in self.rules:
            detected = pattern.search(prompt) is not None
            findings.append(
                Hallazgo(
                    criterio=rule.id,
                    detectado=detected,
                    sugerencia=None if detected else rule.sugerencia,
                )
            )
        return PromptResponse(
            **metrics,
            skill_aplicada=SKILL_NAME,
            estado="listo" if all(item.detectado for item in findings) else "requiere_revision",
            hallazgos=findings,
        )
