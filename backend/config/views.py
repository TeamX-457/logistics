from django.http import JsonResponse
from django.shortcuts import render
from django.template import TemplateDoesNotExist


def health(request):
    """Liveness probe for the host's health check (Render, etc.). No auth, no DB hit."""
    return JsonResponse({"status": "ok"})


def page(request, page="index"):
    """Serve a static frontend page from templates/ by filename, e.g. /wallet -> templates/wallet.html."""
    if page.endswith(".html"):
        page = page[:-5]
    try:
        return render(request, f"{page}.html")
    except TemplateDoesNotExist:
        # Render the branded 404 directly rather than raising Http404 — with
        # DEBUG=True (dev default), Django swaps any raised Http404 for its
        # own technical debug page and never even looks at 404.html.
        return render(request, "404.html", status=404)
