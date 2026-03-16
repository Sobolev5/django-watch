import time
import threading
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

    Each request/response pair is printed in a matching ANSI colour so that
    nested or interleaved requests are easy to follow visually.  Colours
    rotate automatically across a palette of six.

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

    BOLD = "\033[1m"
    FAINT = "\033[2m"
    END = "\033[0m"

    LIGHT_RED = "\033[1;31m"

    # Colour palette for request/response pair rotation.
    _PALETTE = (
        ("\033[0;32m",  "🟢"),  # green
        ("\033[0;36m",  "🔵"),  # cyan
        ("\033[0;34m",  "🟣"),  # blue
        ("\033[0;35m",  "🩵"),  # purple
        ("\033[1;36m",  "⚪"),  # light cyan
        ("\033[1;32m",  "💚"),  # light green
        ("\033[1;34m",  "💙"),  # light blue
        ("\033[1;35m",  "💜"),  # light purple
    )

    _MAX_PRINT_LEN = 200
    _LOGGED_HEADERS = ("Authorization", "Content-Type", "Accept", "X-Requested-With")
    _LOGGED_RESPONSE_HEADERS = ("Content-Type", "Location", "Cache-Control", "Set-Cookie", "X-Frame-Options")

    _color_lock = threading.Lock()
    _color_index = 0

    def __init__(self, get_response=None):
        self.get_response = get_response

    @classmethod
    def _next_color(cls):
        """Return the next colour and emoji from the rotating palette (thread-safe).

        Returns:
            A tuple of (ANSI escape string, emoji string) for this pair.
        """
        with cls._color_lock:
            pair = cls._PALETTE[cls._color_index % len(cls._PALETTE)]
            cls._color_index += 1
            return pair

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
            and getattr(request, "_watch_color", None)
        ):
            return response

        c = request._watch_color
        emoji = request._watch_emoji
        elapsed = round(time.monotonic() - time_start, 2)
        mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_delta_kb = mem_after - mem_before

        # --- SQL stats ---------------------------------------------------
        queries_after = connection.queries[queries_before:]
        sql_count = len(queries_after)
        sql_time = round(sum(float(q.get("time", 0)) for q in queries_after), 3)
        sql_dupes = self._count_duplicate_queries(queries_after)

        # --- Response size -----------------------------------------------
        content_type = response.get("Content-Type", "?")
        content_length = response.get("Content-Length") or self._guess_length(response)

        # --- Summary line ------------------------------------------------
        status = response.status_code
        parts = [
            f"STATUS {status}",
            f"{elapsed}s",
            f"SQL {sql_count}q/{sql_time}s",
        ]
        if sql_dupes:
            parts.append(f"{self.LIGHT_RED}{sql_dupes} dupes{c}")
        parts.append(f"{self._fmt_bytes(content_length)} {content_type}")
        if mem_delta_kb:
            parts.append(f"mem Δ{mem_delta_kb:+d}KB")

        summary = " • ".join(parts)
        print(
            f"{c}{emoji} {self.BOLD}{request.method} "
            f"{request._watch_filename}{self.END}{c} • "
            f"{request._watch_funcname} [  OK  ] • {summary}{self.END}"
        )

        # --- Response headers --------------------------------------------
        resp_header_pairs = []
        for name in self._LOGGED_RESPONSE_HEADERS:
            value = response.get(name)
            if value:
                display = f"{value[:60]}…" if len(str(value)) > 60 else value
                resp_header_pairs.append(f"{name}: {display}")
        if resp_header_pairs:
            self._print_colored(c, f"  {emoji} response headers", " | ".join(resp_header_pairs))

        return response

    def process_view(self, request, func, args, kwargs):
        """Called just before Django invokes the view.

        Assigns a colour to this request and logs the source location,
        input data, and selected request headers in that colour.

        Args:
            request: The incoming ``HttpRequest``.
            func: The view function Django is about to call.
            args: Positional arguments that will be passed to the view.
            kwargs: Keyword arguments that will be passed to the view.

        Returns:
            ``None`` — processing continues normally.
        """
        # For class-based views, extract the class name before unwrapping.
        view_class = getattr(func, "view_class", None) or getattr(func, "cls", None)
        func = unwrap(func)

        if not hasattr(func, "__code__"):
            return None

        c, emoji = self._next_color()

        if view_class:
            # Resolve the actual handler (get, post, etc.) from the user's class.
            handler_name = request.method.lower()
            handler = getattr(view_class, handler_name, None)
            if handler and hasattr(handler, "__code__"):
                code = handler.__code__
            else:
                code = func.__code__
            display_name = f"{view_class.__name__}.{handler_name}"
        elif "." in getattr(func, "__qualname__", ""):
            code = func.__code__
            display_name = func.__qualname__
        else:
            code = func.__code__
            display_name = func.__name__

        request._watch_color = c
        request._watch_emoji = emoji
        request._watch_filename = code.co_filename
        request._watch_funcname = display_name

        print(
            f"\n{c}{emoji} {self.BOLD}{request.method} "
            f"{code.co_filename}{self.END}{c} • "
            f"{display_name} • Line {code.co_firstlineno}{self.END}"
        )

        self._print_colored(c, f"  {emoji} args", args)
        self._print_colored(c, f"  {emoji} kwargs", kwargs)
        self._print_colored(c, f"  {emoji} request.GET", request.GET)
        self._print_colored(c, f"  {emoji} request.POST", request.POST)

        try:
            if not request.POST and request.body:
                self._print_colored(c, f"  {emoji} request.body", request.body)
        except Exception:
            pass

        # --- Selected request headers ------------------------------------
        header_pairs = []
        for name in self._LOGGED_HEADERS:
            value = request.META.get(f"HTTP_{name.upper().replace('-', '_')}")
            if not value and name == "Content-Type":
                value = request.META.get("CONTENT_TYPE")
            if value:
                display = f"{value[:12]}…" if name == "Authorization" else value
                header_pairs.append(f"{name}: {display}")
        if header_pairs:
            self._print_colored(c, f"  {emoji} headers", " | ".join(header_pairs))

        return None

    def process_exception(self, request, exception):
        """Called when a view raises an unhandled exception.

        Prints a full traceback using the same colour assigned to this request.

        Args:
            request: The incoming ``HttpRequest``.
            exception: The exception raised by the view.

        Returns:
            ``None`` — Django's default exception handling continues.
        """
        print(f"{self.LIGHT_RED}{self.BOLD}❌ Exception{self.END}")
        tb_text = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__,
            )
        )
        print(f"{self.LIGHT_RED}  ❌ TRACEBACK:\n{tb_text}{self.END}")
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _print_colored(self, color, label, value):
        """Print a labelled value in the given ANSI colour, truncated.

        Args:
            color: ANSI escape sequence for the pair colour.
            label: A short description shown before the value.
            value: Any object whose string form should be printed.
        """
        if value:
            line = f"{color}{label}: {value}{self.END}"
            print(line[: self._MAX_PRINT_LEN + len(color) + len(self.END)])

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