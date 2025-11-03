from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Citadel Markets Pro Administration"
admin.site.site_title = "Citadel Markets Pro Admin Portal"
admin.site.index_title = "Welcome to Citadel Markets Pro Admin Portal"

def home(request):
    return redirect("/admin")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home),
    path("api/", include("app.urls")),
]

# Add this for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)