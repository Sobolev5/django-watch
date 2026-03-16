import sys
import pytest
from django.test import Client
from django.db import connection, reset_queries

from django_watch.middleware import WatchMiddleware, unwrap


@pytest.fixture(autouse=True)
def _reset_sql_log():
    reset_queries()
    yield
    reset_queries()


@pytest.fixture()
def debug_mode(settings):
    settings.DEBUG = True
    connection.close()
    reset_queries()
    yield
    connection.close()


@pytest.fixture()
def client():
    return Client()


def capture_and_show(capfd):
    out = capfd.readouterr().out
    sys.stderr.write(out)
    return out


class TestUnwrap:

    def test_no_wrapping(self):
        def plain():
            pass
        assert unwrap(plain) is plain

    def test_single_wrap(self):
        def original():
            pass
        def wrapper():
            pass
        wrapper.__wrapped__ = original
        assert unwrap(wrapper) is original

    def test_double_wrap(self):
        def original():
            pass
        def mid():
            pass
        def outer():
            pass
        mid.__wrapped__ = original
        outer.__wrapped__ = mid
        assert unwrap(outer) is original


class TestHelpers:

    def test_fmt_bytes_small(self):
        assert WatchMiddleware._fmt_bytes(512) == "512B"

    def test_fmt_bytes_kilobytes(self):
        assert WatchMiddleware._fmt_bytes(2048) == "2.0KB"

    def test_fmt_bytes_megabytes(self):
        assert WatchMiddleware._fmt_bytes(2 * 1024 * 1024) == "2.0MB"

    def test_fmt_bytes_invalid(self):
        assert WatchMiddleware._fmt_bytes(None) == "?B"

    def test_count_duplicate_queries_no_dupes(self):
        queries = [{"sql": "SELECT 1"}, {"sql": "SELECT 2"}]
        assert WatchMiddleware._count_duplicate_queries(queries) == 0

    def test_count_duplicate_queries_with_dupes(self):
        queries = [
            {"sql": "SELECT 1"},
            {"sql": "SELECT 1"},
            {"sql": "SELECT 1"},
            {"sql": "SELECT 2"},
        ]
        assert WatchMiddleware._count_duplicate_queries(queries) == 2

    def test_count_duplicate_queries_empty(self):
        assert WatchMiddleware._count_duplicate_queries([]) == 0

    def test_color_rotation(self):
        WatchMiddleware._color_index = 0
        pairs = [WatchMiddleware._next_color() for _ in range(10)]
        assert pairs[0] == pairs[8]
        assert pairs[0] != pairs[1]
        assert pairs[1] != pairs[2]
        assert pairs[0][1] == "🟢"
        assert pairs[1][1] == "🔵"


@pytest.mark.django_db
class TestMiddlewareCall:

    def test_simple_request_returns_200(self, client):
        resp = client.get("/simple/")
        assert resp.status_code == 200

    def test_json_response_returns_200(self, client):
        resp = client.get("/json/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_stdout_contains_view_name(self, client, capfd):
        client.get("/simple/")
        out = capture_and_show(capfd)
        assert "simple_view" in out

    def test_cbv_shows_class_name(self, client, capfd):
        client.get("/cbv/")
        out = capture_and_show(capfd)
        assert "ClassBasedView" in out

    def test_stdout_contains_status_code(self, client, capfd):
        client.get("/simple/")
        out = capture_and_show(capfd)
        assert "STATUS 200" in out

    def test_stdout_contains_http_method(self, client, capfd):
        client.get("/simple/")
        out = capture_and_show(capfd)
        assert "GET" in out

    def test_request_emoji_present(self, client, capfd):
        client.get("/simple/")
        out = capture_and_show(capfd)
        assert any(e in out for e in ("🟢", "🔵", "🟣", "🩵", "⚪", "💚", "💙", "💜"))

    def test_response_uses_same_emoji(self, client, capfd):
        client.get("/simple/")
        out = capture_and_show(capfd)
        lines = out.strip().split("\n")
        first_emoji = None
        for e in ("🟢", "🔵", "🟣", "🩵", "⚪", "💚", "💙", "💜"):
            if e in lines[0]:
                first_emoji = e
                break
        assert first_emoji is not None
        assert sum(1 for line in lines if first_emoji in line) >= 2

    def test_post_data_is_logged(self, client, capfd):
        client.post("/simple/", data={"username": "test"})
        out = capture_and_show(capfd)
        assert "request.POST" in out
        assert "username" in out


@pytest.mark.django_db
class TestSQLLogging:

    def test_sql_count_logged(self, client, capfd, debug_mode):
        client.get("/queries/")
        out = capture_and_show(capfd)
        assert "SQL 3q/" in out

    def test_duplicate_queries_detected(self, client, capfd, debug_mode):
        client.get("/dupes/")
        out = capture_and_show(capfd)
        assert "SQL 4q/" in out
        assert "2 dupes" in out

    def test_no_dupes_label_when_clean(self, client, capfd, debug_mode):
        client.get("/queries/")
        out = capture_and_show(capfd)
        assert "dupes" not in out


class TestHeaderLogging:

    def test_content_type_logged(self, client, capfd):
        client.post(
            "/simple/",
            data='{"key": "value"}',
            content_type="application/json",
        )
        out = capture_and_show(capfd)
        assert "Content-Type: application/json" in out

    def test_authorization_masked(self, client, capfd):
        client.get("/simple/", HTTP_AUTHORIZATION="Bearer super-secret-token-12345")
        out = capture_and_show(capfd)
        assert "super-secret-token-12345" not in out
        assert "Authorization:" in out


class TestResponseMetadata:

    def test_response_size_logged(self, client, capfd):
        client.get("/simple/")
        out = capture_and_show(capfd)
        assert "2B" in out

    def test_json_content_type_logged(self, client, capfd):
        client.get("/json/")
        out = capture_and_show(capfd)
        assert "application/json" in out

    def test_response_headers_content_type(self, client, capfd):
        client.get("/json/")
        out = capture_and_show(capfd)
        assert "response headers" in out
        assert "Content-Type: application/json" in out

    def test_response_headers_location_on_redirect(self, client, capfd):
        client.get("/redirect/")
        out = capture_and_show(capfd)
        assert "Location:" in out


class TestProcessException:

    def test_exception_traceback_printed(self, client, capfd):
        with pytest.raises(ValueError, match="boom"):
            client.get("/error/")
        out = capture_and_show(capfd)
        assert "Exception" in out
        assert "TRACEBACK" in out
        assert "boom" in out