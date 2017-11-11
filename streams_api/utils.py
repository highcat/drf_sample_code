# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import Q
from django.core.cache import caches
from django.utils import timezone
from datetime import timedelta
from streamer.main.models import News

def annotate__news_with_stream_rank(qs, stream):
    """FIXME not readable structure, need to rename/refactor """
    SQL_IS_STREAM_BY_TITLE = """
    (
      SELECT count(*)
        FROM main_news_streams
      WHERE
        main_news_streams.news_id = main_news.id
        AND main_news_streams.stream_id = {stream_id}
    )
    """.format(stream_id=stream.id)
    SQL_IS_STREAM_BY_BODY = """
    (
      SELECT count(*)
        FROM main_news_streams_by_body
      WHERE
        main_news_streams_by_body.news_id = main_news.id
        AND main_news_streams_by_body.stream_id = {stream_id}
    )
    """.format(stream_id=stream.id)
    
    qs = qs.extra(
        select={
            'day': """(timestamp AT TIME ZONE '{timezone}')::date""".format(
                timezone=settings.TIME_ZONE
            ),
            'is_stream_by_title': SQL_IS_STREAM_BY_TITLE,
            'is_stream_by_body': SQL_IS_STREAM_BY_BODY,
        },
    )
    # Intended for:
    # qs = qs.order_by('-day', '-is_stream_by_title', '-timestamp')
    return qs


def annotate__last24h_news_number(qs):
    # Annotate with count
    ANNOTATION_SQL_BY_TITLE = """
    SELECT count(*)
      FROM main_news
    JOIN main_news_streams
      ON main_news_streams.news_id = main_news.id
        AND main_news_streams.stream_id = streams_stream.id
    WHERE
      main_news.timestamp >= NOW() - '1 day'::INTERVAL
      AND main_news.deleted = FALSE
      AND main_news.is_duplicate = FALSE
    """
    ANNOTATION_SQL_BY_BODY = """
    SELECT count(*)
      FROM main_news
    JOIN main_news_streams_by_body
      ON main_news_streams_by_body.news_id = main_news.id
        AND main_news_streams_by_body.stream_id = streams_stream.id
    WHERE
      main_news.timestamp >= NOW() - '1 day'::INTERVAL
      AND main_news.deleted = FALSE
      AND main_news.is_duplicate = FALSE
    """
    qs = qs.extra(
        select={
            'last24h_news_number': ANNOTATION_SQL_BY_TITLE,
            'last24h_news_number_by_body': ANNOTATION_SQL_BY_BODY
        },
    )
    return qs



from .models import Stream

def get_trending_streams():
    cache = caches['default']
    if cache.get('streams-trending'):
        return cache.get('streams-trending')

    from .serializers import StreamSerializer
    
    qs = (
        Stream.objects
        .filter(is_active=True)
        .select_related('people', 'companies', 'products', 'regions', 'movies', 'topics')
    )
    
    qs = annotate__last24h_news_number(qs)
    qs = qs.order_by('-last24h_news_number')
    qs = qs.exclude(hide_from_front_page=True)

    def _serialize_streams(qs):
        data = [
            dict(s)
            for s in StreamSerializer(qs[:5], many=True).data
        ]
        data = filter(lambda s: s['last24h_news_number']>0, data)
        return data

    obj = [
        ('Streams', _serialize_streams(qs.filter(detect_by='keywords'))),
        ('Companies', _serialize_streams(qs.filter(detect_by='companies'))),
        ('Products', _serialize_streams(qs.filter(detect_by='products'))),
        ('People', _serialize_streams(qs.filter(detect_by='people'))),
        ('Regions', _serialize_streams(qs.filter(detect_by='regions'))),
    ]

    cache.set('streams-trending', obj, 300)
    return obj


def create_digest_data():
    data = get_trending_streams()
    for category, streams in data:
        for stream in streams:
            stream['trending_news'] = (
                News.objects_good
                .filter(
                    timestamp__gte=timezone.now() - timedelta(days=(7)),
                    streams__id__in=[stream['id']],
                )
                .order_by('-timestamp')
                .distinct()
                [:5]
            )
    filtered_data = []
    for category, streams in data:
        streams = filter(lambda d: len(d['trending_news'])>0, streams)
        if len(streams):
            filtered_data.append((category, streams))
    return filtered_data
