import json
from pathlib import Path

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

_HTML = (Path(__file__).resolve().parent.parent / "templates" / "app.html").read_text(encoding="utf-8")


def index(request):
    u = request.user
    data = {
        "user": {"name": u.get_full_name() or u.get_username(), "admin": u.is_superuser} if u.is_authenticated else None,
        "csrf": get_token(request),
    }
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    resp = HttpResponse(_HTML.replace("<!--GSM-->", "<script>window.GSM=" + blob + "</script>"))
    resp["Cache-Control"] = "no-store"
    return resp


def _client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return fwd.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")


@require_POST
@csrf_protect
def api_login(request):
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        return JsonResponse({"error": "Requête invalide."}, status=400)
    username = str(body.get("username", "")).strip()[:150]
    password = str(body.get("password", ""))[:256]

    key = "login:%s:%s" % (_client_ip(request), username.lower())
    tries = cache.get(key, 0)
    if tries >= 5:
        return JsonResponse({"error": "Trop d’essais. Réessayez dans 10 minutes."}, status=429)

    # « Jean » et « jean » sont acceptés (clavier de téléphone)
    found = get_user_model().objects.filter(username__iexact=username).first()
    user = authenticate(request, username=found.get_username() if found else username, password=password)
    if user is None:
        cache.set(key, tries + 1, 600)
        return JsonResponse({"error": "Identifiants incorrects."}, status=400)

    cache.delete(key)
    login(request, user)
    return JsonResponse({"ok": True})


@require_POST
@csrf_protect
def api_logout(request):
    logout(request)
    return JsonResponse({"ok": True})


def health(request):
    return HttpResponse("ok")
