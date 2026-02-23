from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),   # set_language
    path('rosetta/', include('rosetta.urls')),         # Rosetta UI for translations
    path('admin/', admin.site.urls),                   # admin without language prefix
]

urlpatterns += i18n_patterns(
    path('', include('common.urls')),
    path('accounts/', include('accounts.urls')),
    path('events/', include('events.urls')),
    path('photos/', include('photos.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
