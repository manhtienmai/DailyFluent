from django.contrib import admin
from django.urls import path, include
from core.views import home
from core.views import health

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('', include('core.urls', namespace='core')),
    path('vocab/', include('vocab.urls', namespace='vocab')),
    path('accounts/', include('allauth.urls')),
    path("kanji/", include("kanji.urls", namespace="kanji")),
    path("videos/", include("video.urls", namespace="video")),
    path("exam/", include("exam.urls", namespace="exam")),
    path("streak/", include("streak.urls", namespace="streak")),
    path("grammar/", include("grammar.urls", namespace="grammar")),
    path("todos/", include("todos.urls", namespace="todos")),
    path("payment/", include("payment.urls", namespace="payment")),
    path("feedback/", include("feedback.urls", namespace="feedback")),
    path("api/wallet/", include("wallet.urls", namespace="wallet")),
    path("health", health),
    path("", include("analytics.urls", namespace="analytics")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)