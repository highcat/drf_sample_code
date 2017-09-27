# -*- coding: utf-8 -*-
import dateutil.parser

import re
import json
import pytz
from time import sleep
from pprint import pprint
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import connection
from rest_framework import mixins
from rest_framework import filters
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from celery.task.control import revoke

from streamer.utils.redis_connection import get_redis
from streamer.main.utils import GET_SITE_PREFS
from streamer.api import exceptions
from streamer.api.filters import NewsFilter, NewsPermission
from streamer.api.exceptions import PermissionDenied, NotAuthenticated
from streamer.api.permissions import SuperuserPermission
from streamer.api.fields import TagsField
from streamer.main.models import (
    News, 
    Feed,
    IOSDeviceSubscription,
    SimilarNewsGroup,
    KnowledgeItem,
    Tag,
)
from streamer.main.templatetags.tweet_helpers import _news_source_display_name, _news_stat_source_display_name
from streamer.main import twitter
from streamer.main import tasks
from streamer.main import twitter_news_import, rss_news_import
from streamer.main import find_title, summarization, find_orig_source
from streams.serializers import StreamSerializer
from streamer.utils.url import url_add_ref
from streamer.main.models import UserProfile

def all_except(all_fields, read_write):
    out = list(set(all_fields) - set(read_write))
    return out


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = (
            # Native fields:
            'id',
            'is_headline',
            'is_in_digest',
            'is_knowledge_item',
            'news_image',
            'title',
            'ttrend_source_screen_name',
            'summary_text',
            'stat_text', # it's stat title, but we can't break the API
            'tweet_id',
            # FIXME fields readable by admin only
            'quality',
            'tcc_news',
            'tcc_stat',
            'tcc_source',
            'tcc_summary',
            'news_original_url', # write-only, use 'news_url' field for users
            'stat_final_url', # write-only, use 'stat_url' field for users
            # Annotation fields:
            'fav_by_me',
            # Special fields:
            'timestamp',
            'news_url',
            'stat_url',
            'source_url',
            'news_image_width',
            'news_image_height',
            'source_aggregator_url',
            'source_display_name',
            'stat_source_display_name',
            'news_type',
            'news_type_human',
            'source_twitter_name',
            'tweet_text', # tweet text, or just title if it's not a tweet
            # dict of news tags
            'tags',
            'streams',
            # temp/debug fields:
            'day',
            'is_stream_by_title',
            'is_stream_by_body',
        )
        read_only_fields = all_except(
            fields,
            read_write=[
                'is_headline',
                'is_in_digest',
                'title',
                # 'timestamp',
                'summary_text',
                'stat_final_url',
                'stat_text', # it's stat title, but we can't break the API
                'news_original_url',
                'tags',
            ])

    day = serializers.SerializerMethodField()
    def get_day(self, obj):
        if hasattr(obj, 'day'):
            return obj.day
        return None
    is_stream_by_title = serializers.SerializerMethodField()
    def get_is_stream_by_title(self, obj):
        if hasattr(obj, 'is_stream_by_title'):
            return obj.is_stream_by_title
        return None
    is_stream_by_body = serializers.SerializerMethodField()
    def get_is_stream_by_body(self, obj):
        if hasattr(obj, 'is_stream_by_body'):
            return obj.is_stream_by_body
        return None

    # custom field
    tags = TagsField()

    streams = serializers.SerializerMethodField()
    def get_streams(self, obj):
        all_streams = {}
        for s in obj.streams.all():
            all_streams[s.id] = s.name
        for s in obj.streams_by_body.all():
            all_streams[s.id] = s.name
        return sorted([{'id': k, 'name': v} for k, v in all_streams.iteritems()], key=lambda s: s['name'])
        
    # streams = StreamSerializer(many=True, read_only=True)        

    # Annotation fields,
    # ModelSerializer can't see them directly, so add method fields:

    news_image_width = serializers.SerializerMethodField()
    def get_news_image_width(self, obj):
        if not obj.news_image:
            return None
        try:
            return obj.news_image.width # FIXME this line tries to access file? Can be too slow
        except IOError:
            return None
    news_image_height = serializers.SerializerMethodField()
    def get_news_image_height(self, obj):
        if not obj.news_image:
            return None
        try:
            return obj.news_image.height # FIXME this line tries to access file? Can be too slow
        except IOError:
            return None

    fav_by_me = serializers.SerializerMethodField()
    def get_fav_by_me(self, obj):
        """Values: true, false, null;
        null means it's not calculated (e.g. user not authenticated)
        """
        # 'null' 
        return bool(obj.fav_by_me) if hasattr(obj, 'fav_by_me') else None

    # Special fields:
    timestamp = serializers.SerializerMethodField()
    def get_timestamp(self, obj):
        # if not obj.stat_timestamp:
        #     timestamp = obj.timestamp
        # else:
        #     timestamp = max(obj.stat_timestamp, obj.timestamp)
        timestamp = obj.timestamp
        timestamp = timestamp.astimezone(pytz.UTC)
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S')

    news_url = serializers.SerializerMethodField()
    def get_news_url(self, obj):
        return url_add_ref(obj.get_news_url_for_users(user=self.context['request'].user))

    stat_url = serializers.SerializerMethodField()
    def get_stat_url(self, obj):
        return obj.get_stat_url_for_users(user=self.context['request'].user)

    source_url = serializers.SerializerMethodField()
    def get_source_url(self, obj):
        return url_add_ref(obj.get_source_url_for_users(user=self.context['request'].user))

    source_aggregator_url = serializers.SerializerMethodField()
    def get_source_aggregator_url(self, obj):
        if obj.source.news_type == 'manual':
            return "http://streamer.ai"
        if obj.source.news_type == 'twitter':
            return 'http://twitter.com/%(src)s/' % {
                'src': obj.source.twitter_name,
            }
        if obj.source.news_type == 'rss':
            return obj.source.rss_url

    source_display_name = serializers.SerializerMethodField()
    def get_source_display_name(self, obj):
        return _news_source_display_name(obj)

    stat_source_display_name = serializers.SerializerMethodField()
    def get_stat_source_display_name(self, obj):
        return _news_stat_source_display_name(obj)

    source_twitter_name = serializers.SerializerMethodField()
    def get_source_twitter_name(self, obj):
        return obj.source.twitter_name

    news_type = serializers.SerializerMethodField()
    def get_news_type(self, obj):
        return obj.source.news_type

    news_type_human = serializers.SerializerMethodField()
    def get_news_type_human(self, obj):
        return obj.source.news_type_human()

    tweet_text = serializers.SerializerMethodField()
    def get_tweet_text(self, obj):
        from_item = (obj.title or '') + ' ' + (obj.news_original_url or '')
        if obj.json_orig:
            return obj.json_orig.get('text', from_item)
        return from_item



class NewsViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin, # post news by admin
                  mixins.UpdateModelMixin, # update news by admin
                  mixins.DestroyModelMixin, # delete news by admin
                  viewsets.GenericViewSet):
    """News API endpoint"""
    queryset = News.objects_good.select_related(
        'source',
        'orig_source',
    ).all()
    ordering = '-timestamp'
    ordering_fields = ['timestamp',]
    serializer_class = NewsSerializer
    filter_backends = [NewsFilter,]

    # Note that permissions for listing also determined in filters.NewsFilter class,
    permission_classes = [permissions.AllowAny, NewsPermission]


    #### Admin actions

    def perform_create(self, serializer):
        """
        POST /news/  - create custom news by admin
        """
        if not self.request.user.is_superuser:
            raise exceptions.PermissionDenied()
        instance = serializer.save(
            tweet_id='',
            source=Feed.objects.filter(news_type='manual', enabled=True)[0],
            json_orig='',
            timestamp=datetime.now(pytz.utc),
        )
        tasks.custom_news_prepare.apply_async(
            args=(instance.id,),
            # Delay, to start the task after current transaction finished.
            # FIXME finish transaction BEFORE starting the task
            countdown=3,
            queue='solo-boilerpipe-custom-news',
        )
            
    def perform_update(self, serializer):
        """
        PUT /news/<id>  - update news by admin
        """
        if not self.request.user.is_superuser:
            raise exceptions.PermissionDenied()
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        DELETE /news/<id> - delete news by admin
        """
        if self.request.user.is_superuser:
            raise exceptions.PermissionDenied()
        instance.delete()

    @detail_route(methods=['put', 'delete'], url_path="admin/trash", permission_classes=[])
    def do_admin_trash(self, request, pk=None):
        """
        PUT /news/<id>/admin/trash - move to trash
        DELETE /news/<id>/admin/trash - return from trash
        """
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied()
        qs = News.objects.filter(pk=pk)
        if not qs.exists():
            raise exceptions.NotFound()
        if request.method == 'PUT':
            qs.update(deleted=True)
        elif request.method == 'DELETE':
            qs.update(deleted=False)
        return Response({'ok': True})


    @detail_route(methods=['put'], url_path="admin/reset-text")
    def reset_text(self, request, pk):
        """
        PUT /news/<id>/reset-text - reset manually adjusted text to default
        """
        if not self.request.user.is_superuser:
            raise exceptions.PermissionDenied()

        obj = get_object_or_404(News.objects, pk=pk)

        if obj.source.news_type == 'manual':
            tasks.custom_news_prepare.apply_async(
                args=(obj.id,),
                # Delay, to start the task after current transaction finished.
                # FIXME finish transaction BEFORE starting the task
                countdown=3,
                queue='solo-boilerpipe-custom-news')
        else:
            if obj.source.news_type == 'twitter':
                twitter_news_import.parse_one_item(obj)
            elif obj.source.news_type == 'rss':
                rss_news_import.parse_one_item(obj)
            else:
                assert False
            find_title.process(obj)
            summarization.process(obj)
        return Response(NewsSerializer(obj).data)



@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def subscription_ios(request, token):
    """Create or remove device token"""
    if request.method == 'PUT':
        IOSDeviceSubscription.objects.get_or_create(device_token=token)
    if request.method == 'DELETE':
        try:
            s = IOSDeviceSubscription.objects.get(device_token=token)
            s.delete()
        except IOSDeviceSubscription.DoesNotExist:
            pass

    return Response({}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
@transaction.atomic
def subscription_ios_clear_badges(request, token):
    """Create or remove device token"""
    IOSDeviceSubscription.objects.filter(device_token=token).update(
        badge_counter=0,
        new_device=False,
    )
    # Delete daily notifications
    try:
        subs = IOSDeviceSubscription.objects.get(device_token=token)
        cursor = connection.cursor()
        cursor.execute("DELETE from main_kontextdailynewspendingnotification WHERE device_subscription_id=%(subs_id)s",
                       {'subs_id': subs.id})
    except IOSDeviceSubscription.DoesNotExist:
        # this may happen if subscription is deleted by maintenance script
        pass

    return Response({}, status=status.HTTP_200_OK)


class KnowledgeItemCandidateSerializer(serializers.ModelSerializer):
    """Candidate for semantic similarity groups, among knowledge items"""
    class Meta:
        model = KnowledgeItem
        fields = (
            # XXX mimic some of news serializer fields
            'id',
            'title',
            'timestamp',
            'news_url',
            'source_url',
            'source_display_name',
            'is_knowledge_item',
        )
    news_url = serializers.SerializerMethodField()
    def get_news_url(self, obj):
        return obj.link
    source_display_name = serializers.SerializerMethodField()
    def get_source_display_name(self, obj):
        return obj.source.name
    source_url = serializers.SerializerMethodField()
    def get_source_url(self, obj):
        return obj.source.url
    is_knowledge_item = serializers.SerializerMethodField()
    def get_is_knowledge_item(self, obj):
        return True

from streamer.main.models import SimilarNewsGroupKnowledgeCandidates

class SimilarNewsGroupSerializer(serializers.ModelSerializer):
    news = NewsSerializer(read_only=True)
    candidates = serializers.SerializerMethodField()
    def get_candidates(self, obj):
        # FIXME use separate NewsCandidateSerializer instead
        candidates = []
        for c in SimilarNewsGroupKnowledgeCandidates.objects.filter(similarnewsgroup=obj):
            b = KnowledgeItemCandidateSerializer(c.knowledgeitem).data
            candidates.append(b)
            b['is_candidate'] = True
            b['id'] = b['id']
            b['similarity_relevance'] = c.relevance
        candidates.sort(key=lambda b: (b['similarity_relevance'], b['timestamp']), reverse=True) # some trick here, as we can't do `-b['timestamp']`
        return candidates

    class Meta:
        model = SimilarNewsGroup
        fields = (
            'id',
            'news',
            'candidates',
        )


class SimilarNewsGroupViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet):
    queryset = SimilarNewsGroup.objects.select_related(
        'news',
        'candidates_from_news',
        'candidates_from_knowledge_items',
    )
    serializer_class = SimilarNewsGroupSerializer
    permission_classes = [SuperuserPermission]

    @list_route(methods=['put', 'get', 'delete'], url_path="build")
    def build(self, request):
        redis = get_redis()

        knowledge_recency_days = int(request.data.get('knowledge_recency_days') or 7)

        if request.method == 'PUT':
            task_id = redis.get('grouping_task_id')
            revoke(task_id, terminate=True)
            task_id = tasks.grouping.apply_async(
                kwargs={
                    "knowledge_recency_days": knowledge_recency_days,
                },
                queue='common',
            )
            redis.delete('grouping_task_status')
            redis.set('grouping_task_id', task_id)
        elif request.method == 'GET':
            pass
        elif request.method == 'DELETE':
            task_id = redis.get('grouping_task_id')
            revoke(task_id, terminate=True)
            redis.delete('grouping_task_id')
            redis.delete('grouping_task_status')

        status = redis.get('grouping_task_status')
        status = json.loads(status) if status else {'status': 'NEW', 'progress': 0.0}
        return Response(status)


    @detail_route(methods=['post'], url_path="candidate-delete")
    @transaction.atomic
    def candidate(self, request, pk=None):
        """FIXME not RESTful. Should use DELETE and nested candidate id. Now going faster way."""
        group = self.get_object()

        # FIXME
        id = request.data.get('id')
        if isinstance(id, (str, unicode)):
            m = re.match(r'(knowledge)-(\d+)', request.data.get('id'))
            c_type = 'knowledge'
            c_id = int(m.group(2))
        else:
            c_type = 'news'
            c_id = id

        if c_type == 'knowledge':
            c_knowledge = get_object_or_404(group.candidates_from_knowledge_items.all(), pk=c_id)
            SimilarNewsGroupKnowledgeCandidates.objects.filter(similarnewsgroup=group, knowledgeitem=c_knowledge).delete()
        else:
            assert False # FIXME return 400

        return Response({})



@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def news_candidate(request, id):
    """Save news candidate. Used for text editing.
    FIXME create normal ViewSet later, if needed.
    """
    title = request.data.get('title')
    url = request.data.get('news_url')
    
    ki = get_object_or_404(KnowledgeItem, pk=id)
    ki.title = title
    ki.link = url
    ki.save()
    
    return Response(KnowledgeItemCandidateSerializer(ki).data, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_policies(request, user_id):
    if int(user_id) != request.user.id:
        return Response({}, status=status.HTTP_403_FORBIDDEN)
    UserProfile.objects.filter(user_id=request.user.id).update(
        agreed_to_privacy_policy=True,
        agreed_to_tos=True,
    )
    return Response({})
