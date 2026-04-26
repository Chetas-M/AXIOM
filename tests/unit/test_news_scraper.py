import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "packages" / "node-beta" / "scrapers" / "news_scraper.py"


def load_news_scraper(feed):
    feedparser_mod = types.ModuleType("feedparser")
    feedparser_mod.parse = lambda url: feed

    base_mod = types.ModuleType("base")
    base_mod.get_conn = lambda: None

    sys.modules["feedparser"] = feedparser_mod
    sys.modules["base"] = base_mod

    spec = importlib.util.spec_from_file_location("test_news_scraper_module", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class NewsScraperTests(unittest.TestCase):
    def test_scrape_feed_skips_entries_without_title_or_url(self):
        feed = types.SimpleNamespace(
            feed={"title": "Feed Source"},
            entries=[
                {"title": "Valid headline", "link": "https://example.com/1", "summary": "ok"},
                {"title": "", "link": "https://example.com/2", "summary": "missing title"},
                {"title": "Missing URL", "link": "   ", "summary": "missing url"},
            ],
        )
        module = load_news_scraper(feed)

        articles = module.scrape_feed("https://feed.example.com")

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["headline"], "Valid headline")
        self.assertEqual(articles[0]["url"], "https://example.com/1")


if __name__ == "__main__":
    unittest.main()
