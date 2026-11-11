"""Règles du protocole de synchronisation (sans dépendance Django, donc testable seul)."""
import json
import re

ID_RE = re.compile(r"^(?:[a-z]{1,3}_[A-Za-z0-9_.:+@~-]{1,120}|cfg)$")
PUBLIC_PREFIXES = ("g_", "n_")  # programme, annonces
PUBLIC_IDS = {"cfg"}  # réglages (numéro WhatsApp)
AUDIT_PREFIXES = ("yv_", "cv_", "y_", "c_")  # paiements et montants
MAX_SIZE = 6000


def is_public(doc_id):
    return doc_id in PUBLIC_IDS or doc_id.startswith(PUBLIC_PREFIXES)


def is_writable_id(doc_id):
    return isinstance(doc_id, str) and bool(ID_RE.match(doc_id)) and not doc_id.startswith("sys_")


def valid_doc(doc_id, data):
    if not is_writable_id(doc_id) or not isinstance(data, dict):
        return False
    kind = "cfg" if doc_id == "cfg" else doc_id.split("_", 1)[0]
    if data.get("t") != kind:
        return False
    return len(json.dumps(data, ensure_ascii=False)) <= MAX_SIZE


def valid_members(x):
    return isinstance(x, list) and len(x) <= 500 and all(isinstance(i, str) and 0 < len(i) <= 40 for i in x)
