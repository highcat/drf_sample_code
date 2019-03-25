# -*- coding: utf-8 -*-
from django.db import models
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver


class Stream(models.Model):
    name = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    hide_from_front_page = models.BooleanField(default=False)

    need_update_last_30_days = models.BooleanField(default=True)

    creator = models.ForeignKey(User, null=True, blank=True)
    image = models.ImageField(blank=True)
    url = models.URLField(blank=True)
    explanation = models.TextField(blank=True)

    detect_by = models.CharField(max_length=20, default='', blank=False, choices=(
        ('keywords', 'keywords'),
        ('people', 'people'),
        ('companies', 'companies'),
        ('products', 'products'),
        ('regions', 'regions'),
        ('movies', 'movies and TV shows'),
    ))
    search_body_too = models.BooleanField(default=False)

    keywords = models.TextField(blank=True, help_text=u"Comma-separated list")
    people = models.ManyToManyField('Person', blank=True)
    companies = models.ManyToManyField('Company', blank=True)
    products = models.ManyToManyField('Product', blank=True)
    regions = models.ManyToManyField('Region', blank=True)
    movies = models.ManyToManyField('Movie', blank=True)

    topics = models.ManyToManyField('Topic', blank=True)

    def __unicode__(self):
        return u'~{}'.format(self.name)

@receiver(pre_save, sender=Stream)
def pre_save_stream(sender, instance, *args, **kwargs):
    if not instance.is_active:
        instance.need_update_last_30_days = True


class Person(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, null=True, blank=True)
    def __unicode__(self):
        return u"{}".format(self.name)
    class Meta:
        verbose_name_plural = u'People'


class Company(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, null=True, blank=True)
    def __unicode__(self):
        return u"{}".format(self.name)
    class Meta:
        verbose_name_plural = u'Companies'


class Product(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, null=True, blank=True)
    def __unicode__(self):
        return u"{}".format(self.name)
    class Meta:
        verbose_name_plural = u'Products'


class Region(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, null=True, blank=True)
    def __unicode__(self):
        return u"{}".format(self.name)
    class Meta:
        verbose_name_plural = u'Regions'


class Movie(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, null=True, blank=True)
    def __unicode__(self):
        return u"{}".format(self.name)
    class Meta:
        verbose_name = u'Movie or TV Show'
        verbose_name_plural = u'Movies and TV Shows'



class Topic(models.Model):
    name = models.CharField(max_length=50, unique=True)
    rank = models.FloatField(default=10)
    creator = models.ForeignKey(User, null=True, blank=True)    
    def __unicode__(self):
        return self.name
    

class Subscription(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    stream = models.ForeignKey(Stream, related_name="subscriptions")

    frequency = models.CharField(
        max_length=20,
        choices=(
            ('weekly', 'weekly'),
            ('daily', 'daily'),
            ('mon-thu-sat', 'Monday, Thursday, Saturday'),
        ),
        default='daily',
    )

    # either user or email+session_key
    user = models.ForeignKey(User, null=True, related_name="stream_subscriptions", blank=True)
    email = models.EmailField(null=True, blank=True)
    session_key = models.CharField(null=True, blank=True, max_length=100)

    last_news_id = models.IntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)


@transaction.atomic
def merge_subscriptions(user):
    """Merge email-based subscriptions to user-based"""
    assert user.profile.email_verified
    qs_by_user = Subscription.objects.filter(user=user)
    qs_by_mail = Subscription.objects.filter(email=user.email)
    d_by_user = dict((sub.stream_id, sub) for sub in qs_by_user)
    d_by_mail = dict((sub.stream_id, sub) for sub in qs_by_mail)

    subs_to_delete = []
    subs_to_move = []
    for stream_id, sub in d_by_mail.iteritems():
        if stream_id in d_by_user:
            subs_to_delete.append(sub)
        else:
            subs_to_move.append(sub)
    for s in subs_to_delete:
        # print "    deleting subs for", s.stream
        s.delete()
    for s in subs_to_move:
        # print "    merging subs for", s.stream
        s.email = None
        s.user = user
        s.save()


class AccessCode(models.Model):
    user = models.OneToOneField(User, null=True)
    email = models.EmailField(null=True)

    # TODO renew the code every X weeks
    code = models.CharField(max_length=32)
