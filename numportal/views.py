from django.shortcuts import render


def manifest_view(request):
    return render(request, "manifest.webmanifest", content_type="application/manifest+json")


def service_worker_view(request):
    response = render(request, "sw.js", content_type="application/javascript")
    # Belt-and-suspenders alongside serving from the root path: either alone
    # is enough to give the worker full-site scope, but this makes it explicit.
    response["Service-Worker-Allowed"] = "/"
    # Browsers already re-check /sw.js frequently per the Service Worker spec,
    # but this stops any intermediate cache/CDN from serving a stale copy.
    response["Cache-Control"] = "no-cache"
    return response


def offline_view(request):
    return render(request, "offline.html")
