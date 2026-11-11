from django.contrib import admin

from .models import AuditLog, Doc


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdmin):
    list_display = ("at", "user", "action", "doc_id", "data")
    list_filter = ("user", "action")
    search_fields = ("doc_id", "user")
    date_hierarchy = "at"


@admin.register(Doc)
class DocAdmin(ReadOnlyAdmin):
    list_display = ("id", "updated_by", "updated_at")
    search_fields = ("id",)
