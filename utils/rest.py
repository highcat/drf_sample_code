from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

class CommonPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'first': self.get_first_link(),
            'next': self.get_next_link(),
            'prev': self.get_previous_link(),

            'total_pages': self.page.paginator.num_pages,
            'total_entries': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.page.paginator.per_page,

            'results': data,
        })

    def get_first_link(self):
        url = self.request.build_absolute_uri()
        page_number = 1
        return replace_query_param(url, self.page_query_param, page_number)
