# -*- coding: utf-8 -*-
import dateutil.parser

import re
import json
import pytz
from time import sleep
from pprint import pprint
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import connection
from django.http import Http404
from django.core.files.base import ContentFile
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

from streamer.api.notifications import on_put_to_editorial, on_delete_from_editorial
from streamer.utils.redis_connection import get_redis
from streamer.main.utils import GET_SITE_PREFS
from streamer.api import exceptions
from streamer.api.filters import NewsFilter, AnnotateNewsForUserFilter, NewsPermission
from streamer.api.exceptions import PermissionDenied, NotAuthenticated
from streamer.api.permissions import SuperuserPermission
from streamer.api.fields import TagsField

from .serializers import StreamSerializer
from .models import Stream, Subscription, Person, Company, Product, Region, Movie, Topic
from .filters import StreamsFilter
from streamer.main import emails

from django.core.validators import validate_email, URLValidator
from django.core.exceptions import ValidationError


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def stream(request, name):
    s = get_object_or_404(Stream, name__iexact=name)
    current_user_subscribed = False
    if request.user.is_authenticated():
        current_user_subscribed = Subscription.objects.filter(user=request.user, stream=s).exists()
    return Response({
        "id": s.id,
        "name": s.name,
        "current_user_subscribed": current_user_subscribed,
        "has_news": s.news.exists() or s.news_by_body.exists(),
        "image": s.image.url if s.image else '',
        "url": s.url,
        "explanation": s.explanation,
    })


@transaction.atomic()
@api_view(['POST', 'PUT'])
@permission_classes([permissions.AllowAny])
def stream_edit(request, id=None):
    if request.method == 'PUT':
        s = get_object_or_404(Stream, id=id)
        created = False
    else:
        s = Stream()
        created = True
        
    d = request.data
    # FIXME use form:    
    if not re.match(ur'^[\w]+$', d['name'], flags=re.U):
        return Response({
            'name': u"Please enter a valid stream name, letters only",
        }, status=status.HTTP_400_BAD_REQUEST)
    if len(d['name']) < 3 or len(d['name']) > 30:
        return Response({
            'name': u"Stream name too short or too long",
        }, status=status.HTTP_400_BAD_REQUEST)
    # validate URL
    url = d.get('url', '')
    if url:
        try:
            URLValidator()(url)
        except ValidationError:
            return Response({'url': 'Please enter valid URL'}, status=status.HTTP_400_BAD_REQUEST)
    

    qs_check = Stream.objects.filter(name__iexact=d['name'])
    if s.id:
        qs_check = qs_check.exclude(id=s.id)
    if qs_check.exists():
        return Response({
            'name': u"Stream with this name already exists",
        }, status=status.HTTP_400_BAD_REQUEST)

    s.name = d['name']
    s.url = url
    s.detect_by = d['detect_by']
    s.explanation = d['explanation']
    s.search_body_too = d.get('search_body_too', False)
    s.keywords = u', '.join(map(lambda kw: kw.strip(), d['keywords']))
    s.save()

    if request.user.is_superuser and d.get('no_creator'):
        s.creator = None
    else:
        s.creator = request.user
        subs, created = Subscription.objects.get_or_create(
            user=request.user,
            stream=s,
        )

    if d.get('img_data'):
        m = re.search("data:image/(?P<extension>[^;]+);base64,(?P<data>.+)", d['img_data'])
        s.image.save(
            "{}.{}".format(s.name, m.group('extension')),
            ContentFile(str(m.group('data').decode('base64')))
        )

    s.people = _create_tags(Person, d['people'], s.creator)
    s.companies = _create_tags(Company, d['companies'], s.creator)
    s.products = _create_tags(Product, d['products'], s.creator)
    s.regions = _create_tags(Region, d['regions'], s.creator)
    s.movies = _create_tags(Movie, d['movies'], s.creator)
    s.topics = _create_tags(Topic, d['topics'], s.creator)    
    s.save()

    if created and not request.user.is_superuser:
        print "sending emails"
        for u in User.objects.filter(is_superuser=True).exclude(email=""):
            emails.send_new_stream_added_by_user(s, u.email)

    return Response({
        "id": s.id,
        "name": s.name,
    })


def _create_tags(Model, raw_tags, creator):
    tags = filter(lambda t: t, map(lambda t: re.sub(ur'\s+', ' ', t).strip(), raw_tags))
    tags_to_rem = set(tags)
    for t in Model.objects.filter(name__in=tags): # FIXME case-insensitive
        tags_to_rem.remove(t.name)
    for new_t in tags_to_rem:
        m = Model(name=new_t, creator=creator)
        m.save()
    return Model.objects.filter(name__in=tags)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def tags(request, type):
    query = request.QUERY_PARAMS.get('query') or ''
    if type == 'people':
        qs = Person.objects.all()
    elif type == 'companies':
        qs = Company.objects.all()
    elif type == 'products':
        qs = Product.objects.all()
    elif type == 'regions':
        qs = Region.objects.all()
    elif type == 'movies':
        qs = Movie.objects.all()
    elif type == 'topics':
        qs = Topic.objects.all()
    else:
        raise Http404()
    qs = qs.filter(name__icontains=query)
    qs = qs.order_by('name')
    # return Response([{'id': i.id, 'name': i.name} for i in qs[:100]])
    return Response([i.name for i in qs[:100]])

    
class StreamsViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """Streams API endpoint"""    
    queryset = (
        Stream.objects
        .filter(is_active=True)
        .select_related('people', 'companies', 'products', 'regions', 'movies', 'topics')
    )

    serializer_class = StreamSerializer
    filter_backends = [StreamsFilter,]    
    permission_classes = [permissions.AllowAny]

    @detail_route(methods=['get', 'put', 'delete'], url_path="subscription", permission_classes=[])
    def subscription(self, request, pk=None):
        try:
            int(pk)
        except ValueError:
            raise Http404()
        stream = get_object_or_404(Stream, pk=pk)
        if request.method == 'PUT':
            frequency = request.data.get('frequency')
            if frequency not in ['weekly', 'daily', 'mon-thu-sat']:
                return Response({'error': 'frequency'})
        
        if not request.user.is_authenticated():
            if request.method == 'PUT':
                email = request.data.get('email').strip()
                try:
                    validate_email(email)
                except ValidationError:
                    return Response({'error': 'email'})
                s, created = Subscription.objects.get_or_create(
                    email=email,
                    stream=stream,
                )
                if created:
                    s.session_key = request.session.session_key
                s.frequency = frequency
                s.save()
            elif request.method == 'DELETE':
                if request.session.session_key:
                    Subscription.objects.filter(
                        session_key=request.session.session_key,
                        stream=stream,
                    ).delete()
                s = None
            elif request.method == 'GET':
                s = get_object_or_404(
                    Subscription,
                    session_key=request.session.session_key,
                    stream=stream,
                )
        else:
            if request.method == 'PUT':
                s, created = Subscription.objects.get_or_create(
                    user=request.user,
                    stream=stream,
                )
                s.frequency = frequency
                s.save()
            elif request.method == 'DELETE':
                Subscription.objects.filter(user=request.user, stream=stream).delete()
                s = None
            elif request.method == 'GET':
                s = get_object_or_404(Subscription, user=request.user, stream=stream)
                
        return Response({'id': s.id if s else None})
