import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "packages" / "node-alpha" / "morning_brief.py"
RAG_MODULE_PATH = REPO_ROOT / "packages" / "node-alpha" / "rag" / "rag_enrichment.py"


def load_morning_brief(requests_module):
    prompts_mod = types.ModuleType("llm.prompts")
    prompts_mod.MORNING_BRIEF_PROMPT = "Signals:\n{signals_block}\n\nContext:\n{context_block}"

    rag_mod = types.ModuleType("rag.rag_enrichment")
    rag_mod.build_context_block = lambda tickers: "context for " + ",".join(tickers)

    loader_mod = types.ModuleType("llm.loader")
    loader_mod.get_llm_client = lambda: None

    sys.modules["requests"] = requests_module
    sys.modules["llm.prompts"] = prompts_mod
    sys.modules["rag.rag_enrichment"] = rag_mod
    sys.modules["llm.loader"] = loader_mod

    spec = importlib.util.spec_from_file_location("test_morning_brief_module", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MorningBriefTests(unittest.TestCase):
    def test_generate_brief_returns_model_response(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return {"response": "Brief ready"}

        requests_mod = types.ModuleType("requests")
        requests_mod.post = lambda *args, **kwargs: Response()

        module = load_morning_brief(requests_mod)

        result = module.generate_brief(["RELIANCE"])

        self.assertEqual(result, "Brief ready")


class RagEnrichmentTests(unittest.TestCase):
    def test_build_context_block_uses_configured_beta_api_url(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return [
                    {
                        "published_at": 1710000000,
                        "source": "et",
                        "headline": "Headline",
                    }
                ]

        requests_mod = types.ModuleType("requests")
        captured = {}

        def fake_get(url, **kwargs):
            captured["url"] = url
            return Response()

        requests_mod.get = fake_get
        requests_mod.RequestException = Exception
        sys.modules["requests"] = requests_mod

        spec = importlib.util.spec_from_file_location("test_rag_module", RAG_MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None

        old_url = os.environ.get("BETA_API_URL")
        os.environ["BETA_API_URL"] = "http://beta.internal:9000/"
        try:
            spec.loader.exec_module(module)
            result = module.build_context_block(["RELIANCE"])
        finally:
            if old_url is None:
                os.environ.pop("BETA_API_URL", None)
            else:
                os.environ["BETA_API_URL"] = old_url

        self.assertEqual(captured["url"], "http://beta.internal:9000/rag/RELIANCE")
        self.assertIn("et - Headline", result)


if __name__ == "__main__":
    unittest.main()
