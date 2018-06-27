# Copyright (c) 2013, PagerDuty, Inc. <info@pagerduty.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of PagerDuty Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
import urllib
import urlparse
import urllib2

from types import DictType, ListType
from models.service import Service

from ZenPacks.PagerDuty.APINotification.constants import SUPPORTED_VERSIONS

import logging
log = logging.getLogger('zen.PagerDuty.ServicesRouter')

class InvalidTokenException(Exception): pass
class PagerDutyUnreachableException(Exception): pass
class ParseException(Exception): pass

def _add_default_headers(req):
    _DEFAULT_HEADERS = {'Content-Type' : 'application/json'}
    for header,value in _DEFAULT_HEADERS.iteritems():
        req.add_header(header, value)

def _invoke_pagerduty_resource_api(uri, headers, json_root, params={}, timeout_seconds=None):
    """
    Calls the PagerDuty API at uri and paginates through all of the results.
    """
    uri_parts = list(urlparse.urlparse(uri))
    uri_parts[4] = urllib.urlencode(params, True)
    query_uri = urlparse.urlunparse(uri_parts)

    req = urllib2.Request(query_uri)
    for header,value in headers.iteritems():
        req.add_header(header, value)
    _add_default_headers(req)

    try:
        f = urllib2.urlopen(req, None, timeout_seconds)
    except urllib2.URLError as e:
        if hasattr(e, 'code'):
            if e.code == 401: # Unauthorized
                raise InvalidTokenException()
            else:
                msg = 'The PagerDuty server couldn\'t fulfill the request: HTTP %d (%s)' % (e.code, e.msg)
                raise PagerDutyUnreachableException(msg)
        elif hasattr(e, 'reason'):
            msg = 'Failed to contact the PagerDuty server: %s' % (e.reason)
            raise PagerDutyUnreachableException(msg)
        else:
            raise PagerDutyUnreachableException()

    response_data = f.read()
    f.close()

    try:
        response = json.loads(response_data)
    except ValueError as e:
        raise ParseException(e.message)

    if type(response) is not DictType:
        raise ParseException('Dictionary not returned')

    if json_root not in response:
        raise ParseException("Missing '%s' key in API response" % json_root)

    resource = response[json_root]

    if type(resource) is not ListType:
        raise ParseException("'%s' is not a list" % json_root)

    limit = response.get('limit')
    offset = response.get('offset')
    more = response.get('more')

    if more:
        newOffset = offset + limit
        params.update({'limit': limit, 'offset': newOffset})
        return resource + _invoke_pagerduty_resource_api(uri, headers, json_root, params, timeout_seconds)
    else:
        return resource

def _valid_service(service):
    return ('id' in service
        and 'name' in service
        and 'integrations' in service
        and len(service['integrations']) > 0)

def _get_zenoss_integration(service):
    for integration in service['integrations']:
        if ('vendor' not in integration
            or integration['vendor'] is None
            or 'summary' not in integration['vendor']):
            continue

        for version in SUPPORTED_VERSIONS:
            if integration['vendor']['summary'] == 'Zenoss %s' % version:
                return integration

    return False

def retrieve_services(account):
    """
    Fetches the list of all services for an Account from the PagerDuty API.

    Returns:
        A list of Service objects.
    """
    uri = "https://api.pagerduty.com/services"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token token=' + account.api_access_key,
        'Accept': 'application/vnd.pagerduty+json;version=2'
    }
    json_root = 'services'
    timeout_seconds = 10
    params = {'include[]': 'integrations', 'sort_by': 'name:desc'}
    all_services = _invoke_pagerduty_resource_api(uri, headers, json_root, params, timeout_seconds)

    services = []
    for svcDict in all_services:
        if (_valid_service(svcDict)):
            integration = _get_zenoss_integration(svcDict)
            if integration == False:
                continue

            service = Service(name=svcDict['name'],
                              id=svcDict['id'],
                              type=svcDict['type'],
                              service_key=integration['integration_key'])
            services.append(service)

    return services
