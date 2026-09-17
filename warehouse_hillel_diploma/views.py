from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.shortcuts import redirect


def index(request):
    return redirect("/warehouse/")

def health_check(request):

    checks = {"database": "ok", "cache": "ok"}
    is_healthy = True

    try:
        connections["default"].cursor()
    except OperationalError:
        checks["database"] = "error"
        is_healthy = False

    try:
        cache.set("health_check_probe", "ok", timeout=5)
        if cache.get("health_check_probe") != "ok":
            raise ValueError("cache readback mismatch")
    except Exception:
        checks["cache"] = "error"
        is_healthy = False

    payload = {"status": "healthy" if is_healthy else "unhealthy", "checks": checks}
    return JsonResponse(payload, status=200 if is_healthy else 503)