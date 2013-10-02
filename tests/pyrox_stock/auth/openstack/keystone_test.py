import re
import unittest

import pyrox.http as http
import pyrox.filtering as filtering

from mock import MagicMock
from pyrox_stock.auth.openstack.keystone import KeystoneTokenValidationFilter


class WhenAuthenticatingRequests(unittest.TestCase):

    def setUp(self):
        self.client = MagicMock()

        self.client.authenticate.side_effect = lambda token, tenant_id: {
            '12345': True,
            '22222': False
        }.get(token)

        self.request = MagicMock()
        self.request.url = '/v1/tenant/resource'

        id_regex = re.compile('/v1/([^/?#]+).*')
        self.keystone_filer = KeystoneTokenValidationFilter(id_regex, self.client)

        self.auth_token_header = http.HttpHeader('X-Auth-Token')
        self.auth_token_header.values.append('12345')

        self.request.get_header.side_effect = lambda x: {
            'X-Auth-Token': self.auth_token_header
        }.get(x)

    def test_should_authenticate_good_requests(self):
        action = self.keystone_filer.on_request(self.request)

        self.assertTrue(action.kind == filtering.NEXT_FILTER)

    def test_should_reject_requests_without_id(self):
        self.request.url = '/'
        action = self.keystone_filer.on_request(self.request)

        self.assertTrue(action.kind == filtering.REJECT)

    def test_should_reject_requests_without_auth_token(self):
        self.request.get_header.side_effect = lambda x: None
        action = self.keystone_filer.on_request(self.request)

        self.assertTrue(action.kind == filtering.REJECT)

    def test_should_reject_requests_with_invalid_auth_token(self):
        del self.auth_token_header.values[:]
        self.auth_token_header.values.append('22222')
        action = self.keystone_filer.on_request(self.request)

        self.assertTrue(action.kind == filtering.REJECT)
