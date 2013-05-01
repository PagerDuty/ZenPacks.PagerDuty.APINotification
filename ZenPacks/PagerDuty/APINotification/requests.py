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

class InvalidTokenException(Exception): pass
class PagerDutyUnreachableException(Exception): pass
class ParseException(Exception): pass

def _add_default_headers(req):
    _DEFAULT_HEADERS = {'Content-Type' : 'application/json'}
    for header,value in _DEFAULT_HEADERS.iteritems():
        req.add_header(header, value)

def _invoke_pagerduty_resource_api(uri, headers, json_root, timeout_seconds=None, limit=None, offset=None):
    """
    Calls the PagerDuty API at uri and paginates through all of the results.
    """
    params = {}
    if offset is not None:
        params.update({'offset': offset})

    if limit is not None:
        params.update({'limit': limit})

    uri_parts = list(urlparse.urlparse(uri))
    uri_parts[4] = urllib.urlencode(params)
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
                msg = 'The PagerDuty server couldn\'t fulfill the request: HTTP %d' % (e.code)
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

    total = response.get('total')
    limit = response.get('limit')
    offset = response.get('offset')

    if (total is None or limit is None or offset is None):
        return resource

    additionalResultsAvailable = int(total) > (int(offset) + int(limit))

    if additionalResultsAvailable:
        newOffset = offset + limit
        return resource + _invoke_pagerduty_resource_api(uri, headers, json_root, timeout_seconds, limit, newOffset)
    else:
        return resource

def retrieve_services(account):
    """
    Fetches the list of all services for an Account from the PagerDuty API.

    Returns:
        A list of Service objects.
    """
    uri = "https://%s.pagerduty.com/api/v1/services" % account.subdomain
    headers = {'Authorization': 'Token token=' + account.api_access_key}
    json_root = 'services'
    timeout_seconds = 10
    all_services = _invoke_pagerduty_resource_api(uri, headers, json_root, timeout_seconds)

    services = []
    for svcDict in all_services:
        if ('name' in svcDict
            and 'id' in svcDict
            and 'service_key' in svcDict
            and 'type' in svcDict):
            service = Service(name=svcDict['name'],
                              id=svcDict['id'],
                              service_key=svcDict['service_key'],
                              type=svcDict['type'])
            services.append(service)

    return services
