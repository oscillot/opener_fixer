"""
This is a reimplementation of urllib2 that patches OpenerDirector so that you
 can set your own Content-Type and not have it be overwritten with
 x-www-form-urlencoded. Totally bizarre design decision on somebody's part,
 considering it amounted to a one line change.
"""

import urllib2
from urllib import splithost, splittype
import httplib

class AbstractHTTPHandler(urllib2.AbstractHTTPHandler):
    def do_request_(self, request):
        host = request.get_host()
        if not host:
            raise urllib2.URLError('no host given')

        if request.has_data():  # POST
            data = request.get_data()
            if not request.has_header('Content-type'):
                request.add_unredirected_header(
                    'Content-type',
                    'application/x-www-form-urlencoded')
            if not request.has_header('Content-length'):
                request.add_unredirected_header(
                    'Content-length', '%d' % len(data))

        sel_host = host
        if request.has_proxy():
            scheme, sel = splittype(request.get_selector())
            sel_host, sel_path = splithost(sel)

        if not request.has_header('Host'):
            request.add_unredirected_header('Host', sel_host)
        for name, value in self.parent.addheaders:
            name = name.capitalize()
#            if not request.has_header(name):
            request.add_unredirected_header(name, value)

        return request

class HTTPHandler(AbstractHTTPHandler):
    def http_open(self, req):
        return self.do_open(httplib.HTTPConnection, req)

    http_request = AbstractHTTPHandler.do_request_

if hasattr(httplib, 'HTTPS'):
    class HTTPSHandler(AbstractHTTPHandler):

        def https_open(self, req):
            return self.do_open(httplib.HTTPSConnection, req)

        https_request = AbstractHTTPHandler.do_request_


def build_opener(*handlers):
    """Create an opener object from a list of handlers.

    The opener will use several default handlers, including support
    for HTTP, FTP and when applicable, HTTPS.

    If any of the handlers passed as arguments are subclasses of the
    default handlers, the default handlers will not be used.
    """
    import types
    def isclass(obj):
        return isinstance(obj, (types.ClassType, type))

    opener = OpenerDirector()
    default_classes = [urllib2.ProxyHandler, urllib2.UnknownHandler, HTTPHandler,
                       urllib2.HTTPDefaultErrorHandler, urllib2.HTTPRedirectHandler,
                       urllib2.FTPHandler, urllib2.FileHandler, urllib2.HTTPErrorProcessor]
    if hasattr(httplib, 'HTTPS'):
        default_classes.append(urllib2.HTTPSHandler)
    skip = set()
    for klass in default_classes:
        for check in handlers:
            if isclass(check):
                if issubclass(check, klass):
                    skip.add(klass)
            elif isinstance(check, klass):
                skip.add(klass)
    for klass in skip:
        default_classes.remove(klass)

    for klass in default_classes:
        opener.add_handler(klass())

    for h in handlers:
        if isclass(h):
            h = h()
        opener.add_handler(h)
    return opener

class ProxyHandler(urllib2.ProxyHandler):
    pass

class OpenerDirector(urllib2.OpenerDirector):
    pass

class Request(urllib2.Request):
    pass

def urlopen(*args, **kwargs):
    return urllib2.urlopen(*args, **kwargs)