"""Páginas públicas."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.catalog.selectors import public_catalog


def landing(request: HttpRequest) -> HttpResponse:
    products, categories = public_catalog()
    return render(
        request,
        "public/landing.html",
        {"products": products, "categories": categories},
    )


def privacy(request: HttpRequest) -> HttpResponse:
    return render(request, "public/privacy.html")
