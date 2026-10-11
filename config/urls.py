from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.docs_auth import basic_auth_required
from core.views import api_not_found

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("service_requests.urls")),
    path("api/v1/", include("dashboard.urls")),
    path("api-docs.json", basic_auth_required(SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[])), name="schema"),
    path("api-docs/", basic_auth_required(SpectacularSwaggerView.as_view(url_name="schema", authentication_classes=[], permission_classes=[]))),
    re_path(r"^api/.*$", api_not_found),
]

handler404 = "core.views.api_not_found"
handler500 = "core.views.server_error"
