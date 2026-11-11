from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Servants d’autel · Administration"
admin.site.site_title = "Servants d’autel"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
