# django-watch

Lightweight Django middleware for real-time request logging during development.

Prints the resolved view's source file, function name, line number, HTTP status,
and wall-clock timing straight to your terminal — no extra configuration required.

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

░░ GET main/views.py • profile [  OK  ] • STATUS 200 • Total time • 0.12s
```

## What it logs

| Phase             | Information                                                     |
| ----------------- | --------------------------------------------------------------- |
| **Before view**   | HTTP method, source file, view function, line number            |
| **Request data**  | `args`, `kwargs`, `GET`, `POST`, and raw `body` (truncated)     |
| **After view**    | Status code and total request time                              |
| **On exception**  | Full Python traceback highlighted in red                        |

## Requirements

- Python 3.8+
- Django 3.2+

## License

MIT