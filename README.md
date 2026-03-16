# django-watch

Lightweight Django middleware for real-time request logging during development.

Prints the resolved view's source file, function name, line number, HTTP status,
SQL stats, memory usage, and wall-clock timing straight to your terminal —
no extra configuration required.

Each request/response pair is colour-coded with a matching emoji so nested
or interleaved requests are easy to follow at a glance.

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
🟢 GET main/views.py • profile • Line 191
  🟢 kwargs: {'username': 'sobolev'}
  🟢 headers: Content-Type: text/html | Accept: */*
🟢 GET main/views.py • profile [  OK  ] • STATUS 200 • 0.12s • SQL 5q/0.03s • 1 dupes • 2.4KB text/html • mem Δ+128KB
  🟢 response headers: Content-Type: text/html | Cache-Control: max-age=0

🔵 POST main/views.py • login • Line 42
  🔵 request.POST: <QueryDict: {'email': ['user@example.com']}>
  🔵 headers: Content-Type: application/x-www-form-urlencoded
🔵 POST main/views.py • login [  OK  ] • STATUS 302 • 0.05s • SQL 2q/0.01s • 0B text/html
  🔵 response headers: Location: /dashboard/

🟣 GET main/views.py • dashboard • Line 80
🟣 GET main/views.py • dashboard [  OK  ] • STATUS 200 • 0.31s • SQL 8q/0.09s • 3 dupes • 12.1KB text/html
  🟣 response headers: Content-Type: text/html; charset=utf-8
```

Colours and emoji rotate automatically: 🟢 🔵 🟣 🩵 ⚪ 💚 💙 💜 — red is
reserved for exceptions.

## What it logs

| Phase                | Information                                                                  |
| -------------------- | ---------------------------------------------------------------------------- |
| **Before view**      | HTTP method, source file, view function, line number                         |
| **Request data**     | `args`, `kwargs`, `GET`, `POST`, raw `body` (truncated)                      |
| **Request headers**  | `Authorization` (masked), `Content-Type`, `Accept`, `X-Requested-With`       |
| **After view**       | Status code, total time, response size and `Content-Type`                    |
| **Response headers** | `Content-Type`, `Location`, `Cache-Control`, `Set-Cookie`, `X-Frame-Options` |
| **SQL**              | Query count, total query time, duplicate query count (N+1 detection)         |
| **Memory**           | RSS delta before/after view                                                  |
| **On exception**     | Full Python traceback with ❌ marker                                         |

## Running tests

```bash
uv sync
uv run pytest
```

The test suite uses an in-memory SQLite database and covers the full middleware
chain: view resolution logging, SQL query counting with duplicate detection,
request header output, response metadata, emoji rotation, and exception tracebacks.

## Requirements

- Python 3.8+
- Django 3.2+

## License

MIT