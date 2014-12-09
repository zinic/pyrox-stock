import re

import pyrox.log as logging
import pyrox.filtering as filtering

from ConfigParser import ConfigParser
from keystoneclient.v2_0.client import Client as KeystoneClient

"""
This is a very rough example of what an authentication function might look like

Configuration Example
---------------------

[auth.openstack.keystone]
id_regex = /v1/service/([^/]+).*
service_tenant = tenant
service_user = user
password = password
keystone_url = http://127.0.0.1:35357/v2.0
"""

_LOG = logging.get_logger(__name__)

_CONFIG_KEY = 'auth.openstack.keystone'
X_AUTH_TOKEN = 'X-Auth-Token'

_CONFIG = ConfigParser()
_CONFIG.read("/etc/pyrox/keystone/keystone.conf")


def keystone_token_validator():
    """
    Factory method for token validation filters
    """

    service_user = _CONFIG.get(_CONFIG_KEY, 'service_user')
    service_tenant = _CONFIG.get(_CONFIG_KEY, 'service_tenant')
    password = _CONFIG.get(_CONFIG_KEY, 'password')
    auth_url = _CONFIG.get(_CONFIG_KEY, 'keystone_url')

    id_regex = re.compile(
        config.get(_CONFIG_KEY, 'id_regex'))

    keystone_client = KeystoneClient(
        username=service_user,
        password=password,
        tenant_name=service_tenant,
        auth_url=auth_url)

    return KeystoneTokenValidationFilter(id_regex, keystone_client)


class KeystoneTokenValidationFilter(filtering.HttpFilter):

    def __init__(self, id_regex, keystone_client):
        self.id_regex = id_regex
        self.client = keystone_client

    @filtering.handles_request_head
    def on_request_head(self, request_head):
        token_header = request_head.get_header(X_AUTH_TOKEN)

        if token_header and len(token_header.values) >= 1:
            match = self.id_regex.match(request_head.url)

            if match and len(match.groups()) >= 1:
                tenant_id = match.group(1)

                try:
                    auth_result = self.client.authenticate(
                        token=token_header.values[0],
                        tenant_id=tenant_id)

                    if auth_result:
                        return filtering.next()
                except Exception as ex:
                    _LOG.exception(ex)

        return filtering.reject()
