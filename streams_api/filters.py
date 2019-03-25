# -*- coding: utf-8 -*-
from django.db.models import Q
from rest_framework import filters
from .utils import annotate__last24h_news_number


class StreamsFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        qs = queryset
        qs = qs.order_by('name')
        user = request.user

        search_text = request.QUERY_PARAMS.get('searchText', '')
        if search_text:
            qs = qs.filter(
                Q(name__icontains=search_text) |
                Q(explanation__icontains=search_text) |
                Q(keywords__icontains=search_text) |
                Q(people__name__icontains=search_text) |
                Q(companies__name__icontains=search_text) |
                Q(products__name__icontains=search_text) |
                Q(regions__name__icontains=search_text) |
                Q(movies__name__icontains=search_text)
            )
        qs = qs.filter(is_active=True)

        detect_by = request.QUERY_PARAMS.get('category', '')
        if detect_by:
            qs = qs.filter(detect_by=detect_by)

        qs = annotate__last24h_news_number(qs)

        if request.QUERY_PARAMS.get('frontPage', ''):
            qs = qs.exclude(hide_from_front_page=True)

        # Annotate for user
        if user.is_authenticated():
            USER_ANNOTATION_SQL = """
            SELECT count(id)
            FROM 
                streams_subscription
            WHERE
                streams_subscription.user_id = {user_id}
              AND
                streams_subscription.stream_id = streams_stream.id
            """
            qs = qs.extra(
                select={'current_user_subscribed': USER_ANNOTATION_SQL.format(user_id=user.id)},
            )
        else:
            USER_ANNOTATION_SQL = """
            SELECT count(id)
            FROM 
                streams_subscription
            WHERE
                streams_subscription.session_key = '{session_key}'
              AND
                streams_subscription.stream_id = streams_stream.id
            """
            qs = qs.extra(
                select={'current_user_subscribed': USER_ANNOTATION_SQL.format(session_key=request.session.session_key or '')},
            )
            
        qs = qs.order_by('-last24h_news_number')
        # news_type = request.QUERY_PARAMS.get('newsType', '')
        return qs
