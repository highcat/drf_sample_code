# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include
from .api import StreamsViewSet
from rest_framework import routers

router = routers.SimpleRouter(trailing_slash=True)
routerSlashless = routers.SimpleRouter(trailing_slash=False)

router.register(r'streams', StreamsViewSet)
# slashless for simple routers
routerSlashless.registry = router.registry[:]

urlpatterns = patterns(
    '',
    url(r'^v1/streams/edit/(?P<id>\d+)?/?', 'streams.api.stream_edit'),    
    url(r'^v1/', include(router.urls)),
    url(r'^v1/', include(routerSlashless.urls)),
    url(r'^v1/streams/by-name/(?P<name>[^/]+)/', 'streams.api.stream'),
    url(r'^v1/tags/(?P<type>[^/]+)/search/', 'streams.api.tags'),
)
