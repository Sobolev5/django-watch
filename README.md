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

░░ GET main/views.py • profile [  OK  ] • STATUS 200 • 0.12s • SQL 5q/0.03s • 1 dupes • 2.4KB text/html • mem Δ+128KB
```

## What it logs

| Phase            | Information                                                                  |
| ---------------- | ---------------------------------------------------------------------------- |
| **Before view**  | HTTP method, source file, view function, line number                         |
| **Request data** | `args`, `kwargs`, `GET`, `POST`, raw `body` (truncated)                      |
| **Headers**      | `Authorization` (masked), `Content-Type`, `Accept`, `X-Requested-With`       |
| **After view**   | Status code, total time, response size and `Content-Type`                    |
| **SQL**          | Query count, total query time, duplicate query count (N+1 detection)         |
| **Memory**       | RSS delta before/after view                                                  |
| **On exception** | Full Python traceback highlighted in red                                     |

## Requirements

- Python 3.8+
- Django 3.2+

## License

MIT