"""Python module containing helper http utility functions """

import json
import requests
from requests.auth import HTTPBasicAuth

from f5cloudsdk import constants
from f5cloudsdk.logger import Logger

logger = Logger(__name__).get_logger() # pylint: disable=invalid-name

def download_to_file(url, file_name):
    """Downloads an artifact to a local file

    Notes
    -----
    Uses a stream to avoid loading into memory

    Parameters
    ----------
    url : str
        the URL where the artifact should be downloaded from
    file_name : str
        the local file name where the artifact should be downloaded

    Returns
    -------
    None
    """

    response = requests.request(
        'GET',
        url,
        stream=True
    )
    with open(file_name, 'wb+') as file_object:
        for chunk in response.iter_content(chunk_size=1024):
            # filter out keep-alive new lines
            if chunk:
                file_object.write(chunk)

def make_request(host, uri, **kwargs):
    """Makes request to device (HTTP/S)

    Parameters
    ----------
    uri : str
        the URI where the request should be made
    **kwargs :
        optional keyword arguments

    Keyword Arguments
    -----------------
    port : int
        the port to use
    method : str
        the HTTP method to use
    headers : str
        the HTTP headers to use
    body : str
        the HTTP body to use
    body_content_type : str
        the HTTP body content type to use
    bool_response : bool
        return boolean based on HTTP success/failure
    basic_auth : dict
        use basic auth: {'user': 'foo', 'password': 'bar'}
    advanced_return : bool
        return additional information, like HTTP status code to caller

    Returns
    -------
    dict
        a dictionary containing the JSON response
    """

    port = kwargs.pop('port', 443)
    method = kwargs.pop('method', 'GET').lower()
    headers = {'User-Agent': constants.USER_AGENT}
    # add any supplied headers, allow the caller to override default headers
    headers.update(kwargs.pop('headers', {}))

    # check for body, normalize
    body = kwargs.pop('body', None)
    body_content_type = kwargs.pop('body_content_type', 'json') # json (default), raw
    if body and body_content_type == 'json':
        headers.update({'Content-Type': 'application/json'})
        body = json.dumps(body)

    # check for auth options
    auth = None
    basic_auth = kwargs.pop('basic_auth', None)
    if basic_auth:
        auth = HTTPBasicAuth(basic_auth['user'], basic_auth['password'])

    # note: certain requests *may* contain large payloads, do *not* log body
    logger.debug('Making HTTP request: %s %s' % (method.upper(), uri))

    # construct url
    url = 'https://%s:%s%s' % (host, port, uri)
    # make request
    response = requests.request(
        method,
        url,
        headers=headers,
        data=body,
        auth=auth,
        timeout=constants.HTTP_TIMEOUT['DFL'],
        verify=constants.HTTP_VERIFY
    )

    status_code = response.status_code
    status_reason = response.reason
    # helpful debug
    logger.debug('HTTP response: %s %s' % (status_code, status_reason))

    # return boolean response, if requested
    if kwargs.pop('bool_response', False):
        return response.ok

    # raise exception on 4xx and 5xx status code(s)
    response.raise_for_status()

    # response body
    response_body = response.json()
    logger.trace('HTTP response body: %s' % (response_body))

    # optionally return tuple containing status code, response, (future)
    if kwargs.pop('advanced_return', False):
        return (response_body, status_code)
    # finally, simply return response data
    return response_body

def parse_url(url):
    """Parse URL


    Parameters
    ----------
    url : str
        the URL that should be parsed

    Returns
    -------
    dict
        object containing the parsed URL contents

        ::

            {
                'path': '/foo/bar'
            }

    """

    parsed_url = requests.utils.urlparse(url)

    return {
        'path': parsed_url.path
    }
