# django-watch

Lightweight Django middleware for real-time request logging during development.

Prints the resolved view's source file, function name, line number, HTTP status,
SQL stats, memory usage, and wall-clock timing straight to your terminal —
no extra configuration required.

## Installation

```bash
pip install django-watch
```

## Quick start

Add the middleware at the end of your `settings.py`:

```python
if DEBUG:
    INSTALLED_APPS += ("django_watch",)
    MIDDLEWARE += ("django_watch.middleware.WatchMiddleware",)
```

Open your development console and you will see output like this:

```
░░ GET main/views.py • profile • Line 191
░░░░ kwargs: {'username': 'sobolev'}
░░░░ headers: Content-Type: application/json | Accept: */*

░░ GET main/views.py • profile [  OK  ]
░░░░ response headers: Content-Type: text/html | Cache-Control: max-age=0
░░ ... • STATUS 200 • 0.12s • SQL 5q/0.03s • 1 dupes • 2.4KB text/html • mem Δ+128KB
```

## What it logs

| Phase                | Information                                                                  |
| -------------------- | ---------------------------------------------------------------------------- |
| **Before view**      | HTTP method, source file, view function, line number                         |
| **Request data**     | `args`, `kwargs`, `GET`, `POST`, raw `body` (truncated)                      |
| **Request headers**  | `Authorization` (masked), `Content-Type`, `Accept`, `X-Requested-With`       |
| **Response headers** | `Content-Type`, `Location`, `Cache-Control`, `Set-Cookie`, `X-Frame-Options` |
| **After view**       | Status code, total time, response size                                       |
| **SQL**              | Query count, total query time, duplicate query count (N+1 detection)         |
| **Memory**           | RSS delta before/after view                                                  |
| **On exception**     | Full Python traceback highlighted in red                                     |

## Running tests

```bash
uv sync
uv run pytest -v
```

The test suite uses an in-memory SQLite database and covers the full middleware
chain: view resolution logging, SQL query counting with duplicate detection,
request header output, response metadata, and exception tracebacks.

## Requirements

- Python 3.8+
- Django 3.2+

## License

MIT