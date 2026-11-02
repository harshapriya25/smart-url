import json
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app


def test_invalid_url_is_rejected():
    app.table = Mock()
    result = app.create_short_url({"body": json.dumps({"url": "not-a-url"})})
    assert result["statusCode"] == 400


def test_invalid_json_is_rejected():
    result = app.create_short_url({"body": "{"})
    assert result["statusCode"] == 400


def test_stats_returns_click_count():
    app.table = Mock()
    app.table.get_item.return_value = {
        "Item": {"code": "Ab12Cd", "original_url": "https://example.com", "clicks": 9}
    }
    result = app.get_stats("Ab12Cd")
    body = json.loads(result["body"])
    assert result["statusCode"] == 200
    assert body["clicks"] == 9


def test_stats_returns_404_for_unknown_code():
    app.table = Mock()
    app.table.get_item.return_value = {}
    result = app.get_stats("Ab12Cd")
    assert result["statusCode"] == 404
