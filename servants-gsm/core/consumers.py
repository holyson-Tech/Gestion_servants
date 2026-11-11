from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import AuditLog, Doc
from .protocol import AUDIT_PREFIXES, is_public, is_writable_id, valid_doc, valid_members


class SyncConsumer(AsyncJsonWebsocketConsumer):
    """Une connexion = un appareil.

    - Membre du bureau (connecté) : reçoit TOUTES les données et peut les modifier.
    - Visiteur : reçoit uniquement le programme, les annonces et le numéro WhatsApp (lecture seule).
    """

    async def connect(self):
        user = self.scope.get("user")
        self.authed = bool(user and user.is_authenticated and user.is_active)
        self.name = (user.get_full_name() or user.get_username()) if self.authed else ""
        self.group = "bureau" if self.authed else "public"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        docs = await self.load_docs()
        await self.send_json({"type": "snapshot", "docs": docs, "authed": self.authed})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    # ------------------------------------------------------------------ réception
    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            return
        kind = content.get("type")
        if kind == "ping":
            await self.send_json({"type": "pong"})
            return
        if kind not in ("set", "del", "mem"):
            return
        if not self.authed:
            await self.send_json({"type": "denied"})
            return

        doc_id = content.get("id")
        cid = str(content.get("cid", ""))[:20]
        if not is_writable_id(doc_id):
            await self.send_json({"type": "rejected", "id": str(doc_id)[:60]})
            return

        if kind == "set":
            data = content.get("data")
            if not valid_doc(doc_id, data):
                await self.send_json({"type": "rejected", "id": doc_id})
                return
            await self.db_set(doc_id, data)
            await self.broadcast(doc_id, data, cid, False)

        elif kind == "del":
            await self.db_del(doc_id)
            await self.broadcast(doc_id, None, cid, False)

        else:  # "mem" : ajout / retrait de membres dans une liste de présence, de façon atomique
            base = content.get("base")
            add, rem = content.get("add") or [], content.get("rem") or []
            if (
                not isinstance(base, dict)
                or base.get("t") not in ("p", "r")
                or not valid_members(add)
                or not valid_members(rem)
                or not valid_doc(doc_id, {**base, "p": []})
            ):
                await self.send_json({"type": "rejected", "id": doc_id})
                return
            data = await self.db_mem(doc_id, base, add, rem)
            await self.broadcast(doc_id, data, cid, True)

    # ------------------------------------------------------------------ diffusion
    async def broadcast(self, doc_id, data, cid, force):
        event = {"type": "doc.op", "id": doc_id, "data": data, "cid": cid, "force": force, "by": self.name}
        await self.channel_layer.group_send("bureau", event)
        if is_public(doc_id):
            await self.channel_layer.group_send("public", {**event, "by": ""})

    async def doc_op(self, event):
        await self.send_json(
            {
                "type": "op",
                "id": event["id"],
                "data": event["data"],
                "cid": event["cid"],
                "force": event["force"],
                "by": event["by"],
            }
        )

    # ------------------------------------------------------------------ base de données
    @database_sync_to_async
    def load_docs(self):
        qs = Doc.objects.exclude(pk__startswith="sys_")
        if not self.authed:
            qs = qs.filter(Q(pk__startswith="g_") | Q(pk__startswith="n_") | Q(pk="cfg"))
        return {d.pk: d.data for d in qs}

    @database_sync_to_async
    def db_set(self, doc_id, data):
        Doc.objects.update_or_create(pk=doc_id, defaults={"data": data, "updated_by": self.name})
        self._audit(doc_id, "set", data)

    @database_sync_to_async
    def db_del(self, doc_id):
        old = Doc.objects.filter(pk=doc_id).first()
        if old:
            self._audit(doc_id, "del", old.data)
            old.delete()

    @database_sync_to_async
    def db_mem(self, doc_id, base, add, rem):
        with transaction.atomic():
            doc = Doc.objects.select_for_update().filter(pk=doc_id).first()
            data = dict(doc.data) if doc else dict(base)
            members = (set(data.get("p", [])) | set(add)) - set(rem)
            data["p"] = sorted(members)
            if data.get("t") == "p" and not data["p"]:
                if doc:
                    doc.delete()
                return None
            Doc.objects.update_or_create(pk=doc_id, defaults={"data": data, "updated_by": self.name})
            return data

    def _audit(self, doc_id, action, data):
        if not doc_id.startswith(AUDIT_PREFIXES):
            return
        recent = timezone.now() - timedelta(seconds=20)
        last = AuditLog.objects.filter(doc_id=doc_id, user=self.name, action=action, at__gte=recent).first()
        if last and action == "set":  # regroupe la saisie chiffre par chiffre
            last.data = data
            last.save(update_fields=["data"])
        else:
            AuditLog.objects.create(user=self.name, action=action, doc_id=doc_id, data=data)
