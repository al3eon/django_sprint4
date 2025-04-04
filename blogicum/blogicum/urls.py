from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from pages.views import RegistrationView

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'

auth_urls = [
    path('', include('django.contrib.auth.urls')),
    path('registration/', RegistrationView.as_view(), name='registration'),
]

urlpatterns = [
    path('', include('blog.urls', namespace='blog')),
    path('pages/', include('pages.urls', namespace='pages')),
    path('auth/', include(auth_urls)),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
