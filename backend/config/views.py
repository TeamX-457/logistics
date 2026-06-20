from django.http import Http404
from django.shortcuts import render
from django.template import TemplateDoesNotExist


def page(request, page="index"):
    """Serve a static frontend page from templates/ by filename, e.g. /wallet.html -> templates/wallet.html."""
    try:
        return render(request, f"{page}.html")
    except TemplateDoesNotExist:
        raise Http404(f"No such page: {page}.html")
