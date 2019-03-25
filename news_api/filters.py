# -*- coding: utf-8 -*-
import re
import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Q, Count
from rest_framework import filters
from rest_framework import permissions
from streamer.api import exceptions
from streamer.utils.utils import has_group
from streamer.main.constants import QUALITY_CHOICES
from streamer.main import digest
from streams.models import Stream
from streams.utils import annotate__news_with_stream_rank

ALLOWED_NEWS_TYPES = set([
    'news',
    'digest',
    'personalized',
    'fav',
    # When adding to this list,
    # make sure you add permissions check below.
])


class NewsPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in ['GET', 'OPTIONS']:
            if user.is_authenticated():
                if user.is_superuser:
                    return True
                if obj.deleted == False:
                    return True
            else:
                if obj.deleted == False:
                    return True
        if request.method in ['PUT', 'POST', 'DELETE']:
            if not user.is_authenticated():
                return False
            if user.is_superuser:
                return True
        return False


class NewsFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        qs = queryset

        order = None
        news_type = request.QUERY_PARAMS.get('newsType', '')
        
        if not news_type:
            pass
        elif news_type not in ALLOWED_NEWS_TYPES:
            # Unknown news type.
            raise exceptions.NotFound()

        if news_type == 'news':
            # permissions
            # filtering
            stream_filter = request.QUERY_PARAMS.get('stream', '')
            if stream_filter:
                try:
                    stream = Stream.objects.get(name__iexact=stream_filter)
                except Stream.DoesNotExist:
                    qs = qs.filter(id=-1)
                else:
                    qs = qs.filter(Q(streams__id__in=[stream.id]) | Q(streams_by_body__id__in=[stream.id]))
                    qs = annotate__news_with_stream_rank(qs, stream)
                    qs = qs.order_by('-day', '-is_stream_by_title', '-timestamp')
                    qs = qs.distinct()

            qs = qs.filter(is_duplicate=False)
            order = 'skip'

        if news_type == 'digest':
            # permissions
            qs = qs.filter(deleted=False)
            # filtering
            qs = qs.filter(is_in_digest=True)
            digest_week_from = None
            digest_week_to = None
            dw = request.QUERY_PARAMS.get('digestWeek')
            if dw:
                m = re.match(r'(\d{4})-(\d{2})-(\d{2})_(\d{4})-(\d{2})-(\d{2})', dw)
                if m:
                    digest_week_from = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, 0)
                    digest_week_to = datetime(int(m.group(4)), int(m.group(5)), int(m.group(6)), 0, 0, 0)
            if not digest_week_from or not digest_week_to:
                digest_week_to = digest.last_week_end(datetime.now(pytz.timezone(settings.TIME_ZONE)))
                digest_week_from = digest_week_to - timedelta(days=7)

            qs = qs.filter(
                timestamp__gte=digest_week_from,
                timestamp__lt=digest_week_to,
            )
            order = 'asc'

        if news_type == 'trends':
            # permissions
            qs = qs.filter(
                source__news_type='ttrends',
            )
            # filtering
            qs = qs.filter(
                deleted=False,
                is_duplicate=False,
            )
            qs = qs.filter( ~Q(quality='PROCESSING') )

            trending_tag = request.GET.get('trendingTag')
            if trending_tag:
                qs = qs.filter(ttrend_tag=trending_tag)
            order = 'desc'

        if news_type == 'personalized':
            # permissions
            if not user.is_authenticated():
                raise exceptions.NotAuthenticated()
            raise exceptions.HttpNotImplemented()
            # filtering
            order = 'desc'

        if news_type == 'fav':
            # permissions
            if not user.is_authenticated():
                raise exceptions.NotAuthenticated()
            qs = qs.filter(fav_by_users=user)
            # filtering
            qs = qs.filter(deleted=False)
            qs = qs.filter( ~Q(quality='PROCESSING') )
            order = 'desc'

        #### Search
        search_type = request.QUERY_PARAMS.get('searchType', '')
        search_text = re.sub(r'\s', ' ', request.QUERY_PARAMS.get('searchText', '')).strip().lower()
        if search_type and search_text:
            if search_type == 'title':
                qs = qs.filter(title__icontains=search_text)
            elif search_type == 'text':
                qs = qs.filter(news_article_text__icontains=search_text)
            elif search_type == 'statistics':
                qs = qs.filter(stat_text__icontains=search_text)
            elif search_type == 'summary':
                qs = qs.filter(summary_text__icontains=search_text)
            else:
                search_type = 'unknown search type'

        #### Ordering, forced ordering
        forced_order = request.QUERY_PARAMS.get('order')
        if forced_order in ['asc', 'desc']:
            order = forced_order
        if not order:
            order = 'desc'

        # qs = qs.extra(select={'final_timestamp': 'GREATEST(timestamp, stat_timestamp)'})
        qs = qs.extra(select={'final_timestamp': 'timestamp'})
        if order == 'asc':
            qs = qs.order_by('final_timestamp')
        elif order == 'desc':
            qs = qs.order_by('-final_timestamp')
        else:
            pass # no ordering, or done above

        ## FIXME: we don't need it (?), delete???
        #### Since <some id> filter
        since_id = request.QUERY_PARAMS.get('since', '0')
        try:
            since_id = int(since_id)
        except ValueError:
            since_id = None
        if since_id:
            if order == 'asc':
                qs = qs.filter(pk__lt=since_id)
            elif order == 'desc':
                qs = qs.filter(pk__gt=since_id)

        return qs


class AnnotateNewsForUserFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        qs = queryset
        if user.is_authenticated():
            qs = qs.extra(select={
                'fav_by_me': """
                SELECT COUNT(*)
                FROM main_userprofile_news as t
                WHERE t.userprofile_id = %(user_id)s
                  AND t.news_id = main_news.id
                """ % {"user_id": user.id},
            })
        else:
            # fields are not collected, 'null' will be returned
            pass
        return qs
