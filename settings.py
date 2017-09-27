# -*- coding: utf-8 -*-
import os
import emailer
import djcelery
import sys
from datetime import timedelta
djcelery.setup_loader()

DJANGO_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/'


DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_SENTRY = False

# 'DEV' - for developer's machine;
#         Users won't receive emails or other data,
#         even if the database has been cloned from production server.
# 
# 'PROD' - for production deployment.
# 
# 'STAGE' - for testing deployment; mail will be sent to users, with [STAGE] prefix.
# 
# 'TEST' - means that code run from automated testing environment;
#          will be set automatically, if you run `./manage.py test` or `make test`
# 
PROFILE = 'DEV'
DEV_EMAIL = 'highcat.ru@gmail.com'
DEV_APNS_DEVICE_TOKEN = 'e0f5a18842cf536c7868f06385f880f200e8625fb3f55da00a91b69cb7497489'
DEV_APNS_USE_CELERY = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'
import pytz
TZ = pytz.timezone(TIME_ZONE)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
SITE_URL = '***'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = DJANGO_ROOT + '../media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = DJANGO_ROOT + '../static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/s/'

# Additional locations of static files
STATICFILES_DIRS = (
    DJANGO_ROOT + 'static/',
    os.path.abspath(DJANGO_ROOT + '../bower_components/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'django_assets.finders.AssetsFinder',
    'djangobower.finders.BowerFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '0!fiihi9354rkud4%d%a-ay$(cz8h8*t*woqd_-t*e)m_s$o8!'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'streamer.middleware.EnsureSessionMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.google.GoogleOAuth2',
    'social.backends.twitter.TwitterOAuth',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.linkedin.LinkedinOAuth',
    #
    'django.contrib.auth.backends.ModelBackend',
    )

# for debug request context
INTERNAL_IPS = ('127.0.0.1', )

ALLOWED_HOSTS = []

ROOT_URLCONF = 'streamer.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'streamer.wsgi.application'

# django-hijack
# where you want to be redirected to, after hijacking the user.
HIJACK_LOGIN_REDIRECT_URL = "/"
# where you want to be redirected to, after releasing the user.
HIJACK_LOGOUT_REDIRECT_URL = "/admin/auth/user/"
SHOW_HIJACKUSER_IN_ADMIN = True
HIJACK_ALLOW_GET_REQUESTS = True # XXX disallow, change to POST


TEMPLATE_DIRS = (
    DJANGO_ROOT + 'templates/',
)


# XXX currently not testing things with database.
#TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
TEST_RUNNER = 'streamer.utils.nose_runner.NoDatabaseRunner'

# Reasonable defaults for Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'streamer.api.permissions.SuperuserPermission',
    ),
    'DEFAULT_PARSER_CLASSES': (
        # Automated CamelCase names: `myField` (js) => `my_field` (python)
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'streamer.utils.rest.CommonPagination',
    'DEFAULT_RENDERER_CLASSES': (
        # Automated CamelCase names: `myField` (js) <= `my_field` (python)
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'PAGINATE_BY': 20,
    'PAGINATE_BY_PARAM': 'pageSize', # Allow client to override, using `?pageSize=xxx`.
    'MAX_PAGINATE_BY': 100, # Maximum limit allowed when using `?pageSize=xxx`.
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_assets',
    'djcelery',
    'django_nose',
    # 'celerytest',
    'rest_framework',
    'debug_toolbar',
    'ajax_select',
    'colorful',
    'captcha', # reCaptcha
    'crispy_forms',
    # 
    'streams', # New streamer's functions
    'streamer.api',
    'streamer.main',
    'streamer.financial', # OBSOLETE
    'streamer.common',
    'streamer.utils',
    'social.apps.django_app.default',
    'djangobower',
    # Superuser tools
    'hijack',
    'compat',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Django default:
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    # social-auth
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    #
    "streamer.main.context.site_prefs",
    "streamer.main.context.global_menu_items",
    "streamer.main.context.user_likes",
    "streamer.main.context.user_personal_stuff",
    "streamer.main.context.utils",
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# ReCaptcha settings:
NOCAPTCHA = True
RECAPTCHA_USE_SSL = False

SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is were emails and domains whitelists are applied (if
    # defined).
    'social.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    # 'social.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social.pipeline.user.user_details',

    # Streamer: send validation email, if any
    'streamer.main.social_auth.send_validation_email',
)


# This workaround is for dustjs filter only.
# Described here: http://stackoverflow.com/questions/19757137/dustjs-webassets-results-to-empty-compiled-file
# Check the bug: https://github.com/miracle2k/webassets/issues/276
ASSETS_CACHE = False
ASSETS_MANIFEST = "file:gen/dusty.manifest"
ASSETS_MODULES = ['streamer.assets']


# This is only for site preferences
SITE_ID = 1

# User profile, via Django 1.4 functionality
AUTH_PROFILE_MODULE = "main.UserProfile"

# email account for sending
EMAIL_ACCOUNT = emailer.Account(
    email='no-reply@streamer.ai',
    fromname=u'Streamer',
    server='localhost',
    )

EMAIL_MAILGUN_ACCOUNT = emailer.Account(
    email='no-reply@streamer.ai',
    fromname=u'Streamer',
    server='smtp.mailgun.org',
    login='***',
    password='***',
)


TWITTER_CONSUMER_KEY = "YOUR_CONSUMER_KEY"
TWITTER_CONSUMER_SECRET = "YOUR CONSUMER_SECRET"

TWITTER_OAUTH_TOKEN = "***"
TWITTER_OAUTH_TOKEN_SECRET = "***"


SIGN_UP_START_URL = '/account/profile/?need-complete=1'

##### Social auth app integration settings #####
# SOCIAL_AUTH_USER_MODEL = 'streamer.common.models'

# Used to redirect the user once the auth process ended successfully.
# The value of ?next=/foo is used if it was present
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
# URL where the user will be redirected in case of an error
SOCIAL_AUTH_LOGIN_ERROR_URL = '/account/login/?error=cant-login'
# Is used as a fallback for LOGIN_ERROR_URL
SOCIAL_AUTH_LOGIN_URL = '/account/login/'
# Used to redirect new registered users, will be used in place of SOCIAL_AUTH_LOGIN_REDIRECT_URL if defined.
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = SIGN_UP_START_URL
# Like SOCIAL_AUTH_NEW_USER_REDIRECT_URL but for new associated accounts (user is already logged in).
# Used in place of SOCIAL_AUTH_LOGIN_REDIRECT_URL
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = '/'
# The user will be redirected to this URL when a social account is disconnected
SOCIAL_AUTH_DISCONNECT_REDIRECT_URL = '/'
# Inactive users can be redirected to this URL when trying to authenticate.
SOCIAL_AUTH_INACTIVE_USER_URL = '/account/login/?error=inactive-user'


##### Always request email, this need to be set by hand #####
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
# Add email to requested authorizations.
SOCIAL_AUTH_LINKEDIN_SCOPE = ['r_basicprofile', 'r_emailaddress']
# Add the fields so they will be requested from linkedin.
SOCIAL_AUTH_LINKEDIN_FIELD_SELECTORS = ['email-address']
# Arrange to add the fields to UserSocialAuth.extra_data
SOCIAL_AUTH_LINKEDIN_EXTRA_DATA = [
    ('id', 'id'),
    ('firstName', 'first_name'),
    ('lastName', 'last_name'),
    ('emailAddress', 'email_address'),
]


# Celery settings.
# See http://docs.celeryproject.org/en/2.5/getting-started/brokers/redis.html#broker-redis
BROKER_URL = 'redis://localhost:6379/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_IGNORE_RESULT = False  # do this on per-task level
CELERY_SEND_EVENTS = True
CELERY_TASK_RESULT_EXPIRES = timedelta(days=1)

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Social auth keys -- put to localsettings.py
# SOCIAL_AUTH_TWITTER_KEY = "***"
# SOCIAL_AUTH_TWITTER_SECRET = "***"

APNS_CERTIFICATE_PASSWORD = '***'


from localsettings import *

ASSETS_DEBUG = DEBUG
if PROFILE in ('PROD', 'STAGE'):
    ASSETS_AUTO_BUILD = False # somehow it builds .less every time; FIXME update Django and other libs first.
else:
    ASSETS_AUTO_BUILD = True

# switch to testing database
if len(sys.argv) > 1:
    if sys.argv[1] in ('test', 'migrate-tests'):
        PROFILE = 'TEST'
        DATABASES['default']['PORT'] = '5433' # use Postgres cluster in RAM ( /dev/shm )
        DATABASES['default']['OPTIONS'] = {
            # 'autocommit': True, # a fix for bug with psycopg+Django 1.3 & tests
        }
    if sys.argv[1] == 'migrate-tests':
        # Do what django tests do, to get in the same environment
        DATABASES['default']['NAME'] = 'test_' + DATABASES['default']['NAME']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'user_emails': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': DJANGO_ROOT + '/../var/log/user_emails.log',
            'formatter': 'verbose',
        },
        'misc_scripts': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': DJANGO_ROOT + '/../var/log/misc_scripts.log',
            'formatter': 'verbose',
        },
        'apns': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': DJANGO_ROOT + '/../var/log/apns.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': [],
        'level': 'ERROR',
        },
    'loggers': {
        'django.request': {
            'handlers': [],
            'level': 'ERROR',
            'propagate': False,
        },
        'import': {
            'level': 'WARNING',
            'handlers': [],
            'propagate': False,
        },
        'user_emails': {
            'level': 'INFO',
            'handlers': ['user_emails'],
            'propagate': False,
        },
        'misc_scripts': {
            'level': 'INFO',
            'handlers': ['misc_scripts'],
            'propagate': False,
        },
        'apns': {
            'level': 'INFO',
            'handlers': ['apns'],
            'propagate': False,
        },

        # Logs for automated tests (factory boy), make it less verbose
        'factory.generate': {
            'level': 'INFO',
        },
        'factory.containers': {
            'level': 'INFO',
        },
    },
}

if DEBUG:
    # Log to conlsole only in DEBUG,
    # so cron scripts won't send exceptions to admin's email (see MAILTO=... in crontab)
    LOGGING['root']['handlers'].append('console')
    LOGGING['loggers']['user_emails']['handlers'].append('console')
    LOGGING['loggers']['misc_scripts']['handlers'].append('console')
    LOGGING['loggers']['apns']['handlers'].append('console')
    LOGGING['loggers']['import']['handlers'].append('console')
    LOGGING['loggers']['misc_scripts']['handlers'].append('console')
    LOGGING['loggers']['apns']['handlers'].append('console')


if USE_SENTRY:
    # Errors from Django
    INSTALLED_APPS += (
        'raven.contrib.django',
        'raven.contrib.django.celery',
    )

    # Errors from root logger, e.g. log.error()
    LOGGING['handlers']['sentry'] = {
       'level': 'WARNING',
       'class': 'raven.contrib.django.handlers.SentryHandler',
    }
    LOGGING['root']['handlers'].append('sentry')
    LOGGING['loggers']['user_emails']['handlers'].append('sentry')
    LOGGING['loggers']['misc_scripts']['handlers'].append('sentry')
    LOGGING['loggers']['apns']['handlers'].append('sentry')

    # Second Raven handler, for scraping
    LOGGING['handlers']['import'] = {
        'level': 'WARNING',
        'class': 'raven.handlers.logging.SentryHandler',
        'dsn': SENTRY_DSN_IMPORTS,
    }
    LOGGING['loggers']['import']['handlers'].append('import')


BOWER_COMPONENTS_ROOT = DJANGO_ROOT + '../'

BOWER_INSTALLED_APPS = (
    'bootstrap#~3.1.1',
    'masonry#~3.1.5',
    'imagesloaded#~3.1.8'
)
