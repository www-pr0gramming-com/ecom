from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import TemplateView

from app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("staff/", include("staff.urls", namespace="staff")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
