# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Stream

class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = (
            'id',
            'name',
            'image',
            'explanation',
            'last24h_news_number',
            'last24h_news_number_by_body',            
            'current_user_subscribed',
        )

    # field done by annotation
    last24h_news_number = serializers.SerializerMethodField()
    def get_last24h_news_number(self, obj):
        if hasattr(obj, 'last24h_news_number'):
            return obj.last24h_news_number
        return None
    # field done by annotation
    last24h_news_number_by_body = serializers.SerializerMethodField()
    def get_last24h_news_number_by_body(self, obj):
        if hasattr(obj, 'last24h_news_number_by_body'):
            return obj.last24h_news_number_by_body
        return None

    current_user_subscribed = serializers.SerializerMethodField()
    def get_current_user_subscribed(self, obj):
        if hasattr(obj, 'current_user_subscribed'):
            return bool(obj.current_user_subscribed)
        return False
