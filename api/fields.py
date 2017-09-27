# -*- coding: utf-8 -*-
from rest_framework import serializers
from streamer.main.models import Tag
from streamer.utils.text_utils import norm
from streams.models import Stream

class TagsField(serializers.Field):
    def to_representation(self, obj):
        out = {}
        for tag_type, description in Tag.TAG_TYPE_CHOICES:
            out[tag_type] = []
        for t in obj.order_by('name').all():
            out[t.type].append(t.name)
        return out

    def to_internal_value(self, data):
        tags_to_add = []
        for tt, description in Tag.TAG_TYPE_CHOICES:
            if not data.get(tt):
                continue
            tags_all = [norm(t) for t in data[tt]]
            tags_all = set([t for t in tags_all if t])
            tags_found = set(Tag.objects.filter(type=tt, name__in=tags_all).values_list('name', flat=True))
            tags_to_create = tags_all - tags_found
            # Create tags which do not exist yet
            for t in tags_to_create:
                Tag(name=t, type=tt).save()
            tags_to_add += list(Tag.objects.filter(type=tt, name__in=tags_all))

        return tags_to_add
