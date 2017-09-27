# -*- coding: utf-8 -*-

from rest_framework.exceptions import APIException

class Conflict(APIException):
    status_code = 409
    default_detail = 'Unable to complete request, conflict occurred.'

class HttpNotImplemented(APIException):
    status_code = 501
    default_detail = 'This API endpoint, or an endpoint with such arguments, is not implemented yet.'

# import all exceptions from DRF, which we use in our project
from rest_framework.exceptions import (
    ParseError, # error 400
    NotAuthenticated, # 401
    PermissionDenied, # 403
    NotFound, # 404
    MethodNotAllowed, # 405
)
