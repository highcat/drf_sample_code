# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Stream
from .models import (Person, Product, Company, Region, Subscription, Movie, Topic)
from django import forms
import re
from ajax_select.fields import AutoCompleteSelectMultipleField

from streamer.main.tags import TagField

class StreamForm(forms.ModelForm):
    class Meta:
        model = Stream
        exclude = ['creator']

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(ur'^[\w]+$', name, flags=re.U):
            raise forms.ValidationError('Should not contain spaces and special characters')
        return name

    people = AutoCompleteSelectMultipleField('streams_people', label="People", help_text="Search by id or text", required=False)
    products = AutoCompleteSelectMultipleField('streams_products', label="Products", help_text="Search by id or text", required=False)
    companies = AutoCompleteSelectMultipleField('streams_companies', label="Companies", help_text="Search by id or text", required=False)
    regions = AutoCompleteSelectMultipleField('streams_regions', label="Regions", help_text="Search by id or text", required=False)
    movies = AutoCompleteSelectMultipleField('streams_movies', label="Movies and TV shows", help_text="Search by id or text", required=False)

    topics = TagField(tag_model=Topic, required=False)


class StreamAdmin(admin.ModelAdmin):
    model = Stream
    form = StreamForm
    ordering = ('name',)
    list_display = ['name', 'is_active', 'on_front_page', 'search_body_too', 'has_image', 'has_explanation', 'has_url']

    def on_front_page(self, obj):
        return mark_safe('<img src="/s/admin/img/icon-no.gif" alt="False">' if obj.hide_from_front_page else '<img src="/s/admin/img/icon-yes.gif" alt="True">')
    def has_image(self, obj):
        return mark_safe('<img src="/s/admin/img/icon-yes.gif" alt="True">' if obj.image else '<img src="/s/admin/img/icon-no.gif" alt="False">')
    def has_explanation(self, obj):
        return mark_safe('<img src="/s/admin/img/icon-yes.gif" alt="True">' if obj.explanation else '<img src="/s/admin/img/icon-no.gif" alt="False">')
    def has_url(self, obj):
        return mark_safe('<img src="/s/admin/img/icon-yes.gif" alt="True">' if obj.url else '<img src="/s/admin/img/icon-no.gif" alt="False">')
    
admin.site.register(Stream, StreamAdmin)


class PersonAdmin(admin.ModelAdmin):
    model = Person
    ordering = ('name',)

class ProductAdmin(admin.ModelAdmin):
    model = Product
    ordering = ('name',)

class CompanyAdmin(admin.ModelAdmin):
    model = Company
    ordering = ('name',)

class RegionAdmin(admin.ModelAdmin):
    model = Region
    ordering = ('name',)

class MovieAdmin(admin.ModelAdmin):
    model = Movie
    ordering = ('name',)
    
admin.site.register(Person, PersonAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Movie, MovieAdmin)


class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'rank')
admin.site.register(Topic, TopicAdmin)


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    ordering = ('-created_at',)
    list_display = ('subs', 'created_at', 'user', 'email', 'stream', 'frequency', 'last_sent_at')

    def subs(self, obj):
        return u"By User: {}".format(obj.user.email) if obj.user else u"By Email: {}".format(obj.email)

    def subscribed_to(self, obj):
        return mark_safe(', '.join(u'<a href="/~{name}">~{name}</a>'.format(name=n) for n in obj.stream_subscriptions.values_list('stream__name', flat=True)))
    
admin.site.register(Subscription, SubscriptionAdmin)
