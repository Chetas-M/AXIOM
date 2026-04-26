import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "packages" / "node-alpha" / "morning_brief.py"


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


if __name__ == "__main__":
    unittest.main()
