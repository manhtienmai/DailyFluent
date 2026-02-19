from django.contrib import admin
from django.urls import path, include
from core.views import home
from core.views import health

from django.conf import settings
from django.conf.urls.static import static
from exam.views import choukai_tool_instance # <-- Import instance này
urlpatterns = [
    # Analytics dashboard must come before admin to avoid catch-all
    path("", include("analytics.urls", namespace="analytics")),
    path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),
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
    path("shop/", include("shop.urls", namespace="shop")),
    path("placement/", include("placement.urls", namespace="placement")),
    path("health", health),
    
    
    path('api/tool/choukai/analyze/', choukai_tool_instance.choukai_analyze_api, name='choukai_analyze'),
    path('api/tool/choukai/translate/', choukai_tool_instance.choukai_translate_api, name='choukai_translate'),
    path('api/tool/choukai/ghibli/', choukai_tool_instance.choukai_ghibli_api, name='choukai_ghibli'),
    path('api/tool/choukai/upload-audio/', choukai_tool_instance.choukai_upload_audio_api, name='choukai_upload_audio'),
    path('api/tool/choukai/save/', choukai_tool_instance.choukai_save_question_api, name='choukai_save_question'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)