from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import path
from django.db import connection


def simple_view(request):
    return HttpResponse("OK")


def view_with_queries(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.execute("SELECT 2")
        cursor.execute("SELECT 3")
    return HttpResponse("OK")


def view_with_duplicate_queries(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.execute("SELECT 1")
        cursor.execute("SELECT 1")
        cursor.execute("SELECT 2")
    return HttpResponse("OK")


def view_with_json(request):
    return JsonResponse({"status": "ok"})


def view_with_redirect(request):
    return HttpResponseRedirect("/simple/")


def view_that_raises(request):
    raise ValueError("boom")


urlpatterns = [
    path("simple/", simple_view, name="simple"),
    path("queries/", view_with_queries, name="queries"),
    path("dupes/", view_with_duplicate_queries, name="dupes"),
    path("json/", view_with_json, name="json"),
    path("redirect/", view_with_redirect, name="redirect"),
    path("error/", view_that_raises, name="error"),
]