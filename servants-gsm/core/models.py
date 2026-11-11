from django.db import models


class Doc(models.Model):
    """Un « document » de données (servant, paiement, présence, activité, annonce…).

    L'identifiant est de la forme  <type>_<clé>  (ex. s_AS01, yv_2026-2027_AS01, g_p12).
    """

    id = models.CharField(max_length=160, primary_key=True)
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.id


class AuditLog(models.Model):
    """Journal des modifications de paiements (qui, quand, quoi)."""

    at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.CharField(max_length=150)
    action = models.CharField(max_length=8)
    doc_id = models.CharField(max_length=160, db_index=True)
    data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-at"]

    def __str__(self):
        return f"{self.at:%d/%m/%Y %H:%M} {self.user} {self.action} {self.doc_id}"
