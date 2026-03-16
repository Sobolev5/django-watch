import time
import traceback
import resource
from collections import Counter

from django.db import connection


def unwrap(func):
    """Unwrap a decorated function to retrieve the original callable.

    Follows the ``__wrapped__`` chain set by :func:`functools.wraps` until
    the innermost function is reached.

    Args:
        func: A callable, possibly wrapped by one or more decorators.

    Returns:
        The original unwrapped callable.
    """
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


class WatchMiddleware:
    """Django middleware that logs view dispatch details and timing to stdout.

    For every request that reaches a view, the middleware prints the resolved
    view's source file, function name, line number, arguments, query / POST /
    body payloads, SQL query stats, selected request headers, response size,
    and memory delta.

    Intended for **local development only** — the output uses ANSI escape
    codes and is not suitable for production log aggregators.

    Args:
        get_response: The next middleware or view in the Django call chain.

    Example:
        Add to ``MIDDLEWARE`` in your Django settings::

            MIDDLEWARE = [
                "myproject.middleware.WatchMiddleware",
                # ...
            ]
    """

    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"

    _GUTTER = "░░"
    _GUTTER_DEEP = "░░░░"
    _MAX_PRINT_LEN = 200
    _LOGGED_HEADERS = ("Authorization", "Content-Type", "Accept", "X-Requested-With")

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        """Process the request/response cycle and print timing, SQL, memory,
        and response metadata.

        Args:
            request: The incoming ``HttpRequest``.

        Returns:
            The ``HttpResponse`` produced by the view (or downstream middleware).
        """
        time_start = time.monotonic()
        mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        queries_before = len(connection.queries)

        response = self.get_response(request)

        if not (
            hasattr(response, "status_code")
            and getattr(request, "process_stdout_end", None)
        ):
            return response

        elapsed = round(time.monotonic() - time_start, 2)
        mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_delta_kb = mem_after - mem_before

        queries_after = connection.queries[queries_before:]
        sql_count = len(queries_after)
        sql_time = round(sum(float(q.get("time", 0)) for q in queries_after), 3)
        sql_dupes = self._count_duplicate_queries(queries_after)

        content_type = response.get("Content-Type", "?")
        content_length = response.get("Content-Length") or self._guess_length(response)

        parts = [
            f"{self.YELLOW}STATUS {response.status_code}{self.END}",
            f"{elapsed}s",
            f"{self.CYAN}SQL {sql_count}q/{sql_time}s{self.END}",
        ]
        if sql_dupes:
            parts.append(f"{self.LIGHT_RED}{sql_dupes} dupes{self.END}")
        parts.append(f"{self.PURPLE}{self._fmt_bytes(content_length)} {content_type}{self.END}")
        if mem_delta_kb:
            parts.append(f"{self.BLUE}mem Δ{mem_delta_kb:+d}KB{self.END}")

        summary = " • ".join(parts)
        print(f"{request.process_stdout_end} • {summary}")

        return response

    def process_view(self, request, func, args, kwargs):
        """Called just before Django invokes the view.

        Logs the source location, input data, and selected request headers.

        Args:
            request: The incoming ``HttpRequest``.
            func: The view function Django is about to call.
            args: Positional arguments that will be passed to the view.
            kwargs: Keyword arguments that will be passed to the view.

        Returns:
            ``None`` — processing continues normally.
        """
        func = unwrap(func)

        if not hasattr(func, "__code__"):
            return None

        code = func.__code__
        header = (
            f"\n{self._GUTTER} {self.BOLD}{request.method} "
            f"{code.co_filename}{self.END} • "
            f"{self.GREEN}{func.__name__}{self.END} • "
            f"{self.YELLOW}Line {code.co_firstlineno}{self.END}"
        )
        request.process_stdout_end = (
            f"\n{self._GUTTER} {self.BOLD}{request.method} "
            f"{code.co_filename}{self.END} • "
            f"{self.GREEN}{func.__name__} [  OK  ]{self.END}"
        )

        print(header)
        self._print_truncated("args", args)
        self._print_truncated("kwargs", kwargs)
        self._print_truncated("request.GET", request.GET)
        self._print_truncated("request.POST", request.POST)

        try:
            if not request.POST and request.body:
                self._print_truncated("request.body", request.body)
        except Exception:
            pass

        header_pairs = []
        for name in self._LOGGED_HEADERS:
            value = request.META.get(f"HTTP_{name.upper().replace('-', '_')}")
            if not value and name == "Content-Type":
                value = request.META.get("CONTENT_TYPE")
            if value:
                display = f"{value[:12]}…" if name == "Authorization" else value
                header_pairs.append(f"{name}: {display}")
        if header_pairs:
            self._print_truncated("headers", " | ".join(header_pairs))

        return None

    def process_exception(self, request, exception):
        """Called when a view raises an unhandled exception.

        Prints a full traceback coloured in red.

        Args:
            request: The incoming ``HttpRequest``.
            exception: The exception raised by the view.

        Returns:
            ``None`` — Django's default exception handling continues.
        """
        print(f"{self.RED}{self.BOLD}{self._GUTTER} Exception{self.END}")
        tb_text = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__,
            )
        )
        print(f"{self._GUTTER_DEEP} TRACEBACK:\n{tb_text}")
        return None

    def _print_truncated(self, label, value):
        """Print a labelled value, truncating long representations.

        Args:
            label: A short description shown before the value.
            value: Any object whose ``repr`` should be printed.
        """
        if value:
            line = f"{self._GUTTER_DEEP} {label}: {value}"
            print(line[: self._MAX_PRINT_LEN])

    @staticmethod
    def _count_duplicate_queries(queries):
        """Return the number of duplicate SQL statements in a query log.

        Args:
            queries: A list of query dicts from ``connection.queries``.

        Returns:
            Total count of extra (non-first) executions across all duplicated
            statements, or ``0`` if there are no duplicates.
        """
        counts = Counter(q.get("sql", "") for q in queries)
        return sum(v - 1 for v in counts.values() if v > 1)

    @staticmethod
    def _guess_length(response):
        """Try to determine the response body size in bytes.

        Args:
            response: The ``HttpResponse`` object.

        Returns:
            Body length as an ``int``, or ``0`` if it cannot be determined.
        """
        try:
            return len(response.content)
        except Exception:
            return 0

    @staticmethod
    def _fmt_bytes(size):
        """Format a byte count as a compact, human-readable string.

        Args:
            size: Number of bytes (``int`` or ``str``).

        Returns:
            A string like ``"1.2KB"`` or ``"3.4MB"``.
        """
        try:
            size = int(size)
        except (TypeError, ValueError):
            return "?B"
        if size < 1024:
            return f"{size}B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        return f"{size / (1024 * 1024):.1f}MB"