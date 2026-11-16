import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agent import PromptAgent
from app.schemas import PromptRequest


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        cls.base_url = f"http://127.0.0.1:{port}"
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        cls.addClassCleanup(cls.stop_server, server)

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError("Uvicorn se cerró durante el arranque")
            try:
                with urlopen(cls.base_url + "/openapi.json", timeout=1) as response:
                    cls.openapi = json.load(response)
                return
            except URLError:
                time.sleep(0.1)
        raise RuntimeError("La API no respondió antes del tiempo límite")

    @staticmethod
    def stop_server(server):
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()

    def post(self, **payload):
        request = Request(
            self.base_url + "/api/v1/prompts/analizar",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_openapi_documents_endpoint(self):
        operation = self.openapi["paths"]["/api/v1/prompts/analizar"]["post"]
        self.assertIn("200", operation["responses"])
        self.assertIn("422", operation["responses"])

    def test_same_input_changes_with_skill(self):
        prompt = "Resume el capítulo 2."
        status, baseline = self.post(prompt=prompt, modo="analisis")
        self.assertEqual(status, 200)
        self.assertEqual(
            baseline,
            {
                "caracteres": 21,
                "palabras": 4,
                "skill_aplicada": None,
                "estado": "analizado",
                "hallazgos": [],
            },
        )
        status, reviewed = self.post(prompt=prompt, modo="revision")
        self.assertEqual(status, 200)
        self.assertEqual(reviewed["caracteres"], baseline["caracteres"])
        self.assertEqual(reviewed["palabras"], baseline["palabras"])
        self.assertEqual(reviewed["skill_aplicada"], "auditar-prompts")
        self.assertEqual(reviewed["estado"], "requiere_revision")
        self.assertEqual(
            {item["criterio"] for item in reviewed["hallazgos"] if not item["detectado"]},
            {"audiencia", "formato"},
        )
        self.assertTrue(
            all(item["sugerencia"] for item in reviewed["hallazgos"] if not item["detectado"])
        )

    def test_default_review_detects_all_criteria(self):
        status, body = self.post(
            prompt="EXPLICA la fotosíntesis para principiantes en una tabla."
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["estado"], "listo")
        self.assertTrue(all(item["detectado"] for item in body["hallazgos"]))
        self.assertTrue(all(item["sugerencia"] is None for item in body["hallazgos"]))

    def test_marker_inside_another_word_does_not_match(self):
        status, body = self.post(prompt="Una tableta y una impresora.")
        self.assertEqual(status, 200)
        self.assertFalse(any(item["detectado"] for item in body["hallazgos"]))

    def test_invalid_payloads_return_422(self):
        for payload in (
            {},
            {"prompt": "   "},
            {"prompt": 123},
            {"prompt": "a" * 3001},
            {"prompt": "Resume esto", "modo": "otro"},
        ):
            with self.subTest(payload=list(payload)):
                status, body = self.post(**payload)
                self.assertEqual(status, 422)
                self.assertIn("detail", body)


class SkillPolicyTests(unittest.TestCase):
    def test_policy_reference_controls_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "criterios.json"
            policy.write_text(
                json.dumps(
                    {"criterios": [{
                        "id": "idioma",
                        "marcadores": ["en español"],
                        "sugerencia": "Especifica el idioma.",
                    }]}
                ),
                encoding="utf-8",
            )
            agent = PromptAgent(policy)
            result = agent.process(PromptRequest(prompt="Explica el concepto en español."))
            self.assertEqual(result.estado, "listo")
            self.assertEqual([item.criterio for item in result.hallazgos], ["idioma"])
