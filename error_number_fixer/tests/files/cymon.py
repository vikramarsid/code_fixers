#!/bin/env python
# -*- coding: utf-8 -*-
"""
**Module**: Cymon.io Plugin
       :platform: Linux
       :synopsis: FSO Plugin to allow to easily synchronize the
       Threat Intelligence available in Cymon.io.
.. moduleauthor:: Vikram Arsid
"""
import functools
import json
import traceback
import urllib
from StringIO import StringIO

import requests
from iso.data import parameters
from iso.data.user_param_types import UserComplexType
from iso.plugins.device.iso_device_plugin import ISODevicePlugin
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
from urllib3 import Retry

__author__ = "Vikram Arsid"
__dependency__ = '{"requests": "2.8.14"}'
__notes__ = """The Cymon plugin allows you to easily synchronize the
Threat Intelligence to the tools you use to monitor your environment."""
__fso_version__ = "4.2.0"


class Indicators(UserComplexType):
    __description__ = "Lookup Indicators"
    description = (parameters.String, "Description")
    feed = (parameters.String, "Feed")
    feed_id = (parameters.String, "Feed Id")

    class IOC(UserComplexType):
        __description__ = "Ioc"
        domain = (parameters.DomainName, "Domain")
        hostname = (parameters.HostName, "Hostname")
        ip = (parameters.IPAddress, "Ip")
        md5 = (parameters.FileHashMD5, "Md5")
        sha1 = (parameters.FileHashSHA1, "Sha1")
        sha256 = (parameters.FileHashSHA256, "Sha256")
        ssdeep = (parameters.FileHashSSDeep, "Ssdeep")
        url = (parameters.URL, "Url")

    ioc = (IOC, "Ioc")

    class Location(UserComplexType):
        __description__ = "Location"
        city = (parameters.String, "City")
        country = (parameters.String, "Country")

        class Point(UserComplexType):
            __description__ = "Point"
            lat = (parameters.String, "Lat")
            lon = (parameters.String, "Lon")

        point = (Point, "Point")

    location = (Location, "Location")
    reported_by = (parameters.String, "Reported By")
    tags = (parameters.String.list, "Tags")
    timestamp = (parameters.String, "Timestamp")
    title = (parameters.String, "Title")


class LookupDetails(UserComplexType):
    __description__ = "Lookup Details"

    class IP(UserComplexType):
        __description__ = "IP details"
        black_list = (parameters.IPAddress.list, "Blacklisted IP Address list")
        unknown_list = (parameters.IPAddress.list, "Unknown IP Address list")
        hits = (Indicators.list, "indicator details")

    ip = (IP, "IP details")

    class DomainName(UserComplexType):
        __description__ = "IP details"
        black_list = (parameters.DomainName.list,
                      "Blacklisted DomainName list")
        unknown_list = (parameters.DomainName.list, "Unknown DomainName list")
        hits = (Indicators.list, "indicator details")

    domain_name = (DomainName, "Domain Name")

    class HostName(UserComplexType):
        __description__ = "HostName details"
        black_list = (parameters.HostName.list, "Blacklisted ")
        unknown_list = (parameters.HostName.list, "UnkAddress list")
        hits = (Indicators.list, "indicator details")

    host_name = (HostName, "Host Name")

    class KeyWord(UserComplexType):
        __description__ = "KeyWord details"
        black_list = (parameters.String.list, "Blacklisted keyword list")
        unknown_list = (parameters.String.list, "Unknown keyword list")
        hits = (Indicators.list, "indicator details")

    keyword = (KeyWord, "Keyword")

    class MD5(UserComplexType):
        __description__ = "MD5 details"
        black_list = (parameters.FileHashMD5.list, "Blacklisted MD5 list")
        unknown_list = (parameters.FileHashMD5.list, "Unknown MD5 list")
        hits = (Indicators.list, "indicator details")

    md5 = (MD5, "MD5 hash")

    class SHA1(UserComplexType):
        __description__ = "SHA1 details"
        black_list = (parameters.FileHashSHA1.list, "Blacklisted SHA1 list")
        unknown_list = (parameters.FileHashSHA1.list, "Unknown SHA1 list")
        hits = (Indicators.list, "indicator details")

    sha1 = (SHA1, "SHA1 hash")

    class SHA256(UserComplexType):
        __description__ = "SHA256 details"
        black_list = (parameters.FileHashSHA256.list,
                      "Blacklisted SHA256 list")
        unknown_list = (parameters.FileHashSHA256.list, "Unknown SHA256 list")
        hits = (Indicators.list, "indicator details")

    sha256 = (SHA256, "SHA256 hash")

    class SSDEEP(UserComplexType):
        __description__ = "SSDEEP"
        black_list = (parameters.String.list, "Blackl list")
        unknown_list = (parameters.String.list, "Unknown SSDEEP list")
        hits = (Indicators.list, "indicator details")

    ssdeep = (SSDEEP, "SSDEEP hash")


class FeedDetails(UserComplexType):
    __description__ = "Feed Details"

    class Feed(UserComplexType):
        __description__ = "Feed"
        created = (parameters.String, "Created")
        description = (parameters.String, "Description")
        id = (parameters.String, "Id")
        is_admin = (parameters.Bool, "Is Admin")
        is_guest = (parameters.Bool, "Is Guest")
        is_member = (parameters.Bool, "Is Member")
        is_owner = (parameters.Bool, "Is Owner")
        link = (parameters.URL, "Link")
        logo = (parameters.URL, "Logo")
        name = (parameters.String, "Name")
        privacy = (parameters.String, "Privacy")
        slug = (parameters.String, "Slug")
        tags = (parameters.String.list, "Tags")
        tos = (parameters.String, "Tos")
        updated = (parameters.String, "Updated")

    feed = (Feed, "Feed Details")
    hits = (Indicators.list, "indicator details")


def handle_errors(func):
    @functools.wraps(func)
    def wrapped(self, request, *args, **kwargs):
        try:
            result = func(self, request, *args, **kwargs)
        except CymonException as exc:
            result = self.makeResult()
            result.success = True
            result.trace(exc)
            result['statusMsg'] = parameters.String(str(exc))
            result['success'] = parameters.Bool(False)
        except ConnectionError as exc:
            result = self.makeResult()
            result.success = True
            result.trace(exc)
            result['statusMsg'] = parameters.String(str(exc))
            result['success'] = parameters.Bool(False)
        except CymonError as exc:
            result = self.makeResult()
            result.success = False
            result.trace(exc)
            result['statusMsg'] = parameters.String(str(exc))
            result['success'] = parameters.Bool(False)
        except KeyError as exc:
            tb = traceback.format_exc(exc)
            result = self.makeResult()
            self.logger.error(9001, 'Caught exception {} running command {}'.format(tb, func.__name__))
            result.trace('Missing parameter value: '.format(exc))
            result.success = False
            result['statusMsg'] = parameters.String('Missing parameter value.'
                                                    '\nPlease provide values for the required '
                                                    'parameters: {}'.format(exc))
            result['success'] = parameters.Bool(False)
        except Exception as exc:
            tb = traceback.format_exc(exc)
            result = self.makeResult()
            self.logger.error(9002, 'Caught exception {} running command {}'.format(tb, func.__name__))
            result.trace(
                'Caught exception {} running command {}'.format(tb, func.__name__))
            result.success = False
            result['statusMsg'] = parameters.String(
                'Error running command: {}'.format(tb))
            result['success'] = parameters.Bool(False)
        return result

    return wrapped


def make_choice(collection):
    return [{'value': key, 'label': value} for key, value in collection.iteritems()]


class Cymon(ISODevicePlugin):
    name = "Cymon.IO"
    version = "1.0.0"
    description = "Interface to fetch threat intelligence from Cymon.IO"
    vendor = "eSentire"
    categories = ("Threat Intelligence",)
    icon = "cymon.png"

    pluginParameters = (
        ISODevicePlugin.Parameter(
            typ=parameters.URL,
            name='server',
            description='Cymon.io API server address',
            value='https://api.cymon.io/v2'),
        ISODevicePlugin.Parameter(
            typ=parameters.UserName,
            name='username',
            description='Cymon.io account username'),
        ISODevicePlugin.Parameter(
            typ=parameters.String,
            name='password',
            description='Cymon.io account password',
            encrypted=True),
        ISODevicePlugin.Parameter(
            typ=parameters.Bool,
            name='verify_secure_connection',
            description='Should the secure connection certificates be verified',
            value=False),
        ISODevicePlugin.Parameter(
            typ=parameters.Integer,
            name='timeout',
            description='request timeout',
            value=120),
        ISODevicePlugin.Parameter(
            typ=parameters.String,
            name="proxyProtocol",
            description="Proxy protocol",
            properties={'choices': [{'label': 'HTTP', 'value': 'http'},
                                    {'label': 'HTTPS', 'value': "https"},
                                    {'label': 'Socks', 'value': "socks"}],
                        'optional': True}),
        ISODevicePlugin.Parameter(
            typ=(parameters.HostName | parameters.IPAddress),
            name="proxyHost",
            description="Proxy IP/Host Address",
            properties={'optional': True}),
        ISODevicePlugin.Parameter(
            typ=parameters.Integer,
            name="proxyPort",
            description="Proxy Port",
            properties={'optional': True}),
        ISODevicePlugin.Parameter(
            typ=parameters.String,
            name="proxyUserName",
            description="Proxy Username",
            properties={'optional': True}),
        ISODevicePlugin.Parameter(
            typ=parameters.String.list,
            name="proxyPassword",
            description="Proxy User Password",
            encrypted=True,
            properties={'optional': True}),
    )
    commands = (
        ISODevicePlugin.Command(
            name='lookupIndicator',
            description='look up for threat indicators',
            manualTimeToCompleteInSec=180,
            inputParameters=(
                ISODevicePlugin.InputParameter(
                    typ=parameters.IPAddress.list,
                    name='IP',
                    description="An IP address indicating the online",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.DomainName.list,
                    name='domainName',
                    description="A domain name for a website or server.",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.HostName.list,
                    name='hostName',
                    description="The hostname for a server located",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.String.list,
                    name='keyword',
                    description="Search threat reports by a keyword.",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.FileHashMD5.list,
                    name='MD5',
                    description="Any MD5 hash that summarizes the arch",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.FileHashSHA1.list,
                    name='SHA1',
                    description="Any SHA1 hash that summarizes the",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.FileHashSHA256.list,
                    name='SHA256',
                    description="Any SHA256 hash that summarize",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.String.list,
                    name='SSDEEP',
                    description="Any SSDEEP hash that summarizes th",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.DateTime,
                    name="startDate",
                    description="The start date for searching",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.DateTime,
                    name="endDate",
                    description="The end date for searching",
                    properties={'optional': True}),
                ISODevicePlugin.InputParameter(
                    typ=parameters.Integer,
                    name="maxHits",
                    description="Maximum number of hists to be returned",
                    value=50),
            ),
            outputParameters=(
                ISODevicePlugin.OutputParameter(
                    typ=parameters.cymon.LookupDetails,
                    name='lookupResults',
                    description='IOC lookup results',
                    properties={'optional': True}),
                ISODevicePlugin.OutputParameter(
                    typ=parameters.Bool,
                    name='success',
                    description='True if results are found'),
                ISODevicePlugin.OutputParameter(
                    typ=parameters.String,
                    name='statusMsg',
                    description='Status of the plug-in execution'),
            ),
            summaryParameterNames=("success", "statusMsg"),
            actionName='Lookup',
            targetName='Indicator'
        ),
        ISODevicePlugin.Command(
            name='getFeedDetails',
            description='Get feed details with feed_id',
            manualTimeToCompleteInSec=60,
            inputParameters=(
                ISODevicePlugin.InputParameter(
                    typ=parameters.String.list,
                    name='feedId',
                    description="Feed Id"),
            ),
            outputParameters=(
                ISODevicePlugin.OutputParameter(
                    typ=parameters.cymon.FeedDetails.list,
                    name='feedDetails',
                    description='Cymon.io feed details',
                    properties={'optional': True}),
                ISODevicePlugin.OutputParameter(
                    typ=parameters.Bool,
                    name='success',
                    description='True if results are found'),
                ISODevicePlugin.OutputParameter(
                    typ=parameters.String,
                    name='statusMsg',
                    description='Status of the plug-in execution'),
            ),
            summaryParameterNames=("success", "statusMsg"),
            actionName='Get',
            targetName='Feed'
        ),
    )

    def __init__(self, *args, **kwargs):
        super(Cymon, self).__init__(*args, **kwargs)
        self.server = self["server"].get()
        self.username = self["username"].get()
        self.password = self["password"].get()
        self.timeout = self["timeout"].get()
        self.verify_secure = self["verify_secure_connection"].get()
        self.session = None

    def testDevice(self):
        result = self.makeResult()
        result.success = False
        try:
            result.trace("Running device connection test")
        except Exception as exc:
            result.trace('Error connecting to Cymon.io server {}'.format(exc))
            return result

        result.success = True
        result.trace("Successfully connected to device")
        return result

    @handle_errors
    def lookupIndicator(self, request):

        # Building Result class
        result = self.makeResult()
        result.success = False
        result.trace('Looking indicators...')
        success = False
        # Building query request
        ip_address_list = self._get_parameters(request, 'IP', True)
        domain_name_list = self._get_parameters(request, 'domainName', True)
        host_name_list = self._get_parameters(request, 'hostName', True)
        keyword_list = self._get_parameters(request, 'keyword', True)
        md5_list = self._get_parameters(request, 'MD5', True)
        sha1_list = self._get_parameters(request, 'SHA1', True)
        sha256_list = self._get_parameters(request, 'SHA256', True)
        ssdeep_list = self._get_parameters(request, 'SSDEEP', True)
        start_date = self._get_parameters(request, 'startDate')
        end_date = self._get_parameters(request, 'endDate')
        max_hits = self._get_parameters(request, 'maxHits')
        lookup_results = {}
        if ip_address_list:
            lookup_results["ip"] = self._process_indicator(result, "ip", ip_address_list, start_date, end_date,
                                                           max_hits)
        if domain_name_list:
            lookup_results["domain_name"] = self._process_indicator(result, "domain", domain_name_list, start_date,
                                                                    end_date, max_hits)
        if host_name_list:
            lookup_results["host_name"] = self._process_indicator(result, "hostname", host_name_list, start_date,
                                                                  end_date, max_hits)
        if keyword_list:
            lookup_results["keyword"] = self._process_indicator(result, "term", keyword_list, start_date, end_date,
                                                                max_hits)
        if md5_list:
            lookup_results["md5"] = self._process_indicator(
                result, "md5", md5_list, start_date, end_date, max_hits)
        if sha1_list:
            lookup_results["sha1"] = self._process_indicator(
                result, "sha1", sha1_list, start_date, end_date, max_hits)
        if sha256_list:
            lookup_results["sha256"] = self._process_indicator(result, "sha256", sha256_list, start_date, end_date,
                                                               max_hits)
        if ssdeep_list:
            lookup_results["ssdeep"] = self._process_indicator(result, "ssdeep", ssdeep_list, start_date, end_date,
                                                               max_hits)

        if lookup_results:
            success = True
            status_msg = "Successfully fetched IOC lookup results"
            result['lookupResults'] = parameters.cymon.LookupDetails(
                lookup_results)
        else:
            status_msg = "No results found"

        result['success'] = parameters.Bool(success)
        result['statusMsg'] = parameters.String(status_msg)
        result.success = True
        return result

    def getFeedDetails(self, request):
        # Building Result class
        result = self.makeResult()
        result.success = False
        result.trace('Getting feed details...')
        success = False
        feed_id_list = self._get_parameters(request, 'feedId', True)
        feed_results = None
        if feed_id_list:
            feed_results = self._process_indicator(
                result, "feed", feed_id_list)

        if feed_results:
            success = True
            status_msg = "Successfully fetched feed details"
            result['feedDetails'] = parameters.cymon.FeedDetails.list(
                feed_results)
        else:
            status_msg = "No results found"

        result['success'] = parameters.Bool(success)
        result['statusMsg'] = parameters.String(status_msg)
        result.success = True
        return result

    # =================================================================================================================
    # Helpers
    # =================================================================================================================

    def _process_indicator(self, result, indicator_type, indicator_data, start_date=None, end_date=None, max_hits=50):
        result.trace("Processing indicator lookup")
        # send keep alive to FSO to prevent timeout while fetching all IoC results
        if self.get_api_version().version >= (4, 2, 0):
            self.send_keepalive()
        lookup_result_list = []
        black_list = set()
        unknown_list = set()
        for indicator in indicator_data:
            result.trace("Indicator lookup: %s" % str(indicator))
            lookup_result = self._get_all_indicator_section_results(
                indicator_type, indicator, start_date, end_date)
            if indicator_type != "feed":
                if lookup_result:
                    if lookup_result["total"] == 0:
                        unknown_list.add(indicator)
                    elif lookup_result["total"] > 0:
                        black_list.add(indicator)
                    else:
                        unknown_list.add(indicator)
                    hits = lookup_result.get("hits")
                    if hits:
                        lookup_result_list.extend(hits)
                else:
                    unknown_list.add(indicator)
            else:
                lookup_result_list.append(lookup_result)

        if indicator_type == "feed":
            lookup_results = lookup_result_list[:max_hits]
        else:
            # sorting for latest hist to be on top
            lookup_result_list.sort(
                key=lambda item: item['timestamp'], reverse=True)
            lookup_results = {
                "black_list": list(black_list),
                "unknown_list": list(unknown_list),
                "hits": lookup_result_list[:max_hits]
            }
        return lookup_results

    def _get_all_indicator_section_results(self, indicator_type, indicator, start_date, end_date):
        api_endpoint = "/ioc/search/{indicator_type}/{indicator}".format(
            indicator_type=indicator_type,
            indicator=indicator
        )
        if start_date:
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date:
            end_date = end_date.strftime("%Y-%m-%d")
        indicator_url = self._make_url(
            api_endpoint, size=100, startDate=start_date, endDate=end_date)
        lookup_results = self._request("GET", request_url=indicator_url)
        return lookup_results

    @staticmethod
    def _get_parameters(request, field, is_list=False):
        try:
            req_value = request[field]
            if req_value.isList():
                req_value = [item for item in req_value]
            elif not is_list:
                req_value = req_value.get()
                # handling empty quotes
                if isinstance(req_value, str):
                    if req_value.strip() == "\"\"":
                        return None
                    elif req_value.strip() == "''":
                        return None
            else:
                req_value = [req_value.get(), ]
        except Exception:
            req_value = None
        return req_value

    def _get_proxy(self):
        proxy_host = self._get_parameters(self, 'proxyHost')
        if proxy_host:
            missing = []
            proxy_port = self._get_parameters(self, 'proxyPort')
            if not proxy_port:
                missing.append('proxyPort')
            proxy_proto = self._get_parameters(self, 'proxyProtocol')
            if not proxy_proto:
                missing.append('proxyProtocol')
            proxy_user = self._get_parameters(self, 'proxyUser')
            if not proxy_user:
                missing.append('proxyUser')
            proxy_password = self._get_parameters(self, 'proxyPassword')
            if not proxy_password:
                missing.append('proxyPassword')

            if len(missing) > 0:
                raise KeyError(
                    "Missing required Proxy Parameters:\n%s" % ",".join(missing))
            if "/" in proxy_password:  # This seems to be a bug in urllib
                self.logger.user_error(9003, " '/' Invalid character found in password!")
            proxy_password = urllib.quote(proxy_password)
            proxy_auth = "%s:%s@" % (proxy_user, proxy_password)
            proxies = {proxy_proto: "%s://%s%s:%s/" %
                                    (proxy_proto, proxy_auth, proxy_host, proxy_port)}
        else:
            proxies = None
        return proxies

    def _login(self):
        auth_url = str(self.server).rstrip("/") + "/auth/login"
        data = {"username": self.username, "password": self.password}
        login_request = requests.request(
            "POST", url=auth_url, data=json.dumps(data), verify=self.verify_secure)
        login_data = login_request.json()
        token = login_data.get("jwt", None)
        message = login_data.get("message", "Error in generating tok")
        self.logger.user_info(message)
        return token

    def _request(self, method, request_url, params=None, data=None, custom_headers=None, stream=False,
                 json_output=True):
        self.logger.user_info(
            "Sending request to Cymon global threat intelligence")
        response = None
        try:
            if not self.session:
                session = requests.Session()
                session.params = {} if not params else params
                session.stream = stream
                session.verify = self.verify_secure
                session.proxies = self._get_proxy()
                token = self._login()
                session.headers.update({
                    'Authorization': "Bearer {}".format(token),
                    'Content-Type': "application/json",
                    'Cache-Control': "no-cache"
                })

                session.mount('https://', HTTPAdapter(
                    max_retries=Retry(
                        total=5,
                        status_forcelist=[429, 500, 502, 503],
                        backoff_factor=5,
                    )
                ))
                self.session = session
            else:
                session = self.session

            with session:
                # Request headers
                if custom_headers:
                    session.headers.update(custom_headers)
                response = session.request(
                    method=method, url=request_url, data=data, timeout=self.timeout)
                self.logger.user_info("[%s] Response status: %s" % (
                    response.status_code, response.reason))
                if response.status_code == 404:
                    self.logger.user_error(9004, "[Error 404] Resource not found")
                    return None
                elif response.status_code == 403:
                    raise CymonException(
                        "Forbidden Access. Please check with administrator")
                elif response.status_code == 400:
                    raise CymonError("Bad request")
                else:
                    response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            self.logger.user_error(9005, error)
            raise CymonError(response.text)

        except Exception as exp:
            self.logger.user_info("REQUEST ERROR: %s" % exp)
            raise ConnectionError(exp)

        if stream:
            content_string = StringIO()
            for content in response.iter_content(decode_unicode=True, chunk_size=1024 * 16):
                try:
                    if content:
                        content_string.write(content)
                except StopIteration:
                    break
            response = content_string.getvalue()
            content_string.flush()

        if json_output:
            try:
                response = response.json()
            except Exception as exp:
                raise CymonException(
                    "Internal Error: Unable to decode response json: {}".format(exp))

        return response

    def _get_paginated_resource(self, url, max_results=25):
        results = []
        next_page_url = url
        additional_fields = {}
        while next_page_url and len(results) < max_results:
            json_data = self.get(next_page_url)
            max_results -= len(json_data.get('results'))
            for r in json_data.pop("results"):
                results.append(r)
            next_page_url = json_data.pop("next")
            json_data.pop('previous', '')
            if json_data.items():
                additional_fields.update(json_data)
        resource = {"results": results[:max_results]}
        resource.update(additional_fields)
        return resource

    def _make_url(self, api_endpoint, **kwargs):
        base_url = self.server + api_endpoint
        if kwargs:
            kwargs = {k: v for k, v in kwargs.iteritems() if v}
            base_url += "?" + urllib.urlencode(kwargs)

        return base_url


class CymonError(Exception):
    pass


class CymonException(Exception):
    pass
