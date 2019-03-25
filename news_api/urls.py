# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include
from streamer.api.views import (
    NewsViewSet,
    SimilarNewsGroupViewSet,
)
from rest_framework import routers

router = routers.SimpleRouter(trailing_slash=True)
routerSlashless = routers.SimpleRouter(trailing_slash=False)

router.register(r'news', NewsViewSet)
router.register(r'similarity/groups', SimilarNewsGroupViewSet)
# slashless for simple routers
routerSlashless.registry = router.registry[:]


urlpatterns = patterns(
    '',
    # Tells API version, and API version upgrades.
    url(r'^status/', 'streamer.api.views.api_status'),

    url(r'^v1/', include(router.urls)),
    url(r'^v1/', include(routerSlashless.urls)),
    url(r'^v1/subscriptions/ios/(?P<token>[\d\w]+)/?$', 'streamer.api.views.subscription_ios'),
    url(r'^v1/subscriptions/ios/(?P<token>[\d\w]+)/badges/?$', 'streamer.api.views.subscription_ios_clear_badges'),
    url(r'^v1/stat-candidate/(?P<id>\d+)/?$', 'streamer.api.views.news_candidate'),

    url(r'^v1/users/(?P<user_id>\d+)/legal/accept-policies/', 'streamer.api.views.accept_policies'),
    
    # FIXME  old api (web UI only)
    url(r'^set-email-1st-time/?$', 'streamer.main.ajax.set_email_1st_time'),
    url(r'^invites/(?P<id>\d+)?/?$', 'streamer.main.ajax.invites'),
    url(r'^check-feed-url/?$', 'streamer.main.ajax.check_feed_url'),
    url(r'^subscribe/?$', 'streamer.main.ajax.subscribe'),

    url(r'^sources/(?P<id>\d+)/admin-note/?$', 'streamer.main.ajax.admin_note'),
    url(r'^send-custom-email/?$', 'streamer.main.ajax.send_custom_email'),
)
