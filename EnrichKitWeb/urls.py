"""EnrichKitWeb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
# import debug_toolbar

from django.urls import include, path
from webapp import views
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

admin.site.site_header = 'EnrichKit Admin'
admin.site.site_title = 'Admin'
admin.site.index_title = 'EnrichKit'

urlpatterns = [
    # admin
    path('admin/', admin.site.urls),

    # debug
    # path('__debug__', include(debug_toolbar.urls)),

    # info
    path('', views.show_info),
    path('index/', views.show_info),
    path('info/', views.show_info),

    # main service
    # path('loci/', views.loci_match_fetch),
    path('loci/', views.loci_match),
    path('ora/', views.run_ora),
    path('idmap/', views.id_map),

    # contacts
    path('contacts/', views.show_contacts),

    path('results/', views.show_results),

    path(
        'favicon.ico',
        RedirectView.as_view(url=staticfiles_storage.url('favicon.ico')),
    ),
]
