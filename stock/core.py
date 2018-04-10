import hashlib
import logging

from django.core.cache import cache
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class StockPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class IsIdempotent(permissions.BasePermission):
    message = 'Duplicate request detected.'

    def has_permission(self, request, view):
        if request.method not in ['POST', 'PUT']:
            return True
        s = request.path + request.user.username + str(request.data)
        # key = base64.b64encode(pickle.dumps(s))[:128]
        key = hashlib.md5(s.encode('utf-8')).hexdigest().upper()
        is_idempotent = bool(cache.add(key, 'yes', 60))
        if not is_idempotent:
            logger.info(
                u'User: "%s", URL: "%s", Duplicate request (non-idempotent): %s',
                request.user.username, request.path, key)
        return is_idempotent


def customExceptionHandler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code
        if not response.data.get('errmsg'):
            response.data['errmsg'] = response.data['detail']
            del (response.data['detail'])

    return response
