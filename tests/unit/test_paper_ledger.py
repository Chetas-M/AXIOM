import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "packages" / "node-beta" / "scheduler" / "paper_ledger.py"


def load_paper_ledger():
    sqlalchemy_orm = types.ModuleType("sqlalchemy.orm")
    sqlalchemy_orm.sessionmaker = lambda **kwargs: (lambda: None)

    yfinance_mod = types.ModuleType("yfinance")
    yfinance_mod.Ticker = lambda symbol: None

    storage_db = types.ModuleType("storage.db")
    storage_db.engine = object()

    storage_models = types.ModuleType("storage.models")

    class Signal:
        date = object()
        is_tradeable = object()

    class PaperPosition:
        ticker = object()
        status = object()

    class PortfolioSnapshot:
        pass

    class SignalRun:
        date = object()

    storage_models.Signal = Signal
    storage_models.PaperPosition = PaperPosition
    storage_models.PortfolioSnapshot = PortfolioSnapshot
    storage_models.SignalRun = SignalRun

    sys.modules["sqlalchemy.orm"] = sqlalchemy_orm
    sys.modules["yfinance"] = yfinance_mod
    sys.modules["storage.db"] = storage_db
    sys.modules["storage.models"] = storage_models

    spec = importlib.util.spec_from_file_location("test_paper_ledger_module", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, storage_models


class FakeQuery:
    def __init__(self, first_result=None, all_result=None):
        self.first_result = first_result
        self.all_result = all_result or []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.first_result

    def all(self):
        return self.all_result


class PaperLedgerTests(unittest.TestCase):
    def test_skipped_regime_returns_before_signal_processing(self):
        module, models = load_paper_ledger()

        class RunStatus:
            status = "SKIPPED_REGIME"
            reason = "VIX > 25"

        class FakeSession:
            def query(self, model):
                if model is models.SignalRun:
                    return FakeQuery(first_result=RunStatus())
                if model is models.Signal:
                    raise AssertionError("Signal query should not run for skipped regime days")
                raise AssertionError(f"Unexpected query for {model}")

            def close(self):
                pass

        module.SessionLocal = lambda: FakeSession()

        module.execute_daily_paper_trades_and_snapshot()


if __name__ == "__main__":
    unittest.main()
