from pathlib import Path

SKILL_NAME = "auditar-prompts"
SKILL_DIR = Path(__file__).resolve().parents[1] / ".github" / "skills" / SKILL_NAME
POLICY_PATH = SKILL_DIR / "references" / "criterios.json"
