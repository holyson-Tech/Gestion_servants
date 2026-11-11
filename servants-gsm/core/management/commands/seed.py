import json
from pathlib import Path

from django.core.management.base import BaseCommand

from core.models import Doc


class Command(BaseCommand):
    help = "Charge une seule fois les données de départ (liste des servants, programme 2026-2027)."

    def handle(self, *args, **options):
        if Doc.objects.filter(pk="sys_seeded").exists():
            self.stdout.write("Données de départ déjà chargées.")
            return
        path = Path(__file__).resolve().parents[2] / "seed" / "seed.json"
        docs = json.loads(path.read_text(encoding="utf-8"))
        Doc.objects.bulk_create(
            [Doc(id=k, data=v, updated_by="initialisation") for k, v in docs.items()],
            ignore_conflicts=True,
        )
        Doc.objects.get_or_create(id="sys_seeded", defaults={"data": {"t": "sys"}})
        self.stdout.write("%d documents chargés." % len(docs))
