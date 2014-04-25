#!/usr/bin/python
#-*- encoding: utf-8 -*-
import sys
import socket
import time
import os
import struct
import ConfigParser


try:
    import gevent
    from gevent import monkey

    monkey.patch_all()
except Exception, e:
    raise e

global_file_cache_list = {}

HAS_BUFFERD = True

DEBUG_MODE = True

BUFFER_SIZE = 4096

#BASE_HTML_DIR = 'C:\\Users\\wangyang\\Downloads\\lame3.99.5'
BASE_HTML_DIR = '../html'

BASE_HTML_FILE = 'index.html'

DEFAULT_PORT = 7777

HTTP_STATUS_CODE = {
    200: "200 OK",
    304: "304 Not Modified",
    404: "404 Not Found",
    500: "500 Internal Server Error",
}


def server(port):
    s = socket.socket()
    s.bind(('127.0.0.2', port))
    s.listen(500)
    global greenlets
    greenlets = []
    while True:
        cli, addr = s.accept()
        if DEBUG_MODE:
            g = gevent.spawn(handle_request, cli, gevent.sleep)
            greenlets.append(g)
        else:
            gevent.spawn(handle_request, cli, gevent.sleep)


def handle_request(s, sleep):
    if DEBUG_MODE:
        print("running greenlets:")
        for i, g in enumerate(greenlets, 1):
            if not g.started and g.successful():
                print("greenlet %d has finished" % i)
            elif g.started and not g.successful():
                print("greenlet %d is running" % i)
            else:
                print("greenlet {0} started:{4} ready:{1} succ:{2} ex:{3}".\
                      format(i, g.ready(), g.successful(), g.exception, g.started))
    try:
        data = ''

        while True:
            tmp = s.recv(BUFFER_SIZE)

            data += tmp
            if len(tmp) < BUFFER_SIZE or len(tmp) == 0:
                break
        # print data
        header_list = get_header_from_request(data)  # 仅仅按\r\n分割
        try:
            print(header_list)
            header_dict = {h[0:h.index(':')].strip().lower(): h[h.index(':') + 1:].strip()\
                    for h in header_list if ':' in h}
        except KeyError:
            print('KeyError:\n', header_list)
        request_line = header_list[0]
        method = get_request_method(request_line)
        path = get_request_path(request_line)
        file_full_path = get_full_file_path(path)

        def normal_response(file_full_path):
            send_http_status_code(s, 200)
            send_http_header(s, "Content-Length", file=file_full_path)
            send_http_header(s, "Date")
            send_http_header(s, "Content-Type", file=file_full_path)
            send_http_header(s, "Server")
            send_http_header(s, "Last-Modified", file=file_full_path)
            s.send("\r\n")
            for buff in read_html_from_file(file_full_path):
                result = s.send(buff)

        if if_file_exists(file_full_path):
            if "if-modified-since" in header_dict:
                mtime = os.path.getmtime(file_full_path)
                mtime = time.mktime(time.gmtime(mtime))
                check_to_time = header_dict["if-modified-since"]
                check_to_time = time.mktime(time.strptime(check_to_time, "%a, %d %b %Y %H:%M:%S GMT"))
                if mtime <= check_to_time:
                    send_http_status_code(s, 304)
                    send_http_header(s, "Date")
                    send_http_header(s, "Server")
                    send_http_header(s, "Last-Modified", file=file_full_path)
                    s.send("\r\n")
                else:
                    normal_response(file_full_path)
            else:
                normal_response(file_full_path)
        else:
            send_http_status_code(s, 404)

        #s.shutdown(socket.SHUT_RDWR)
        #print '.', 'be killed'
    except Exception, ex:
        print ex
    finally:
        s.close()


def get_header_from_request(request):
    req_list = request.split("\r\n")
    return req_list


def get_request_method(req):
    l = req.split(' ')
    return l[0]


def get_request_path(req):
    l = req.split(' ')
    return l[1]


def send_http_status_code(sock, status_code):
    sock.send("http/1.0 ")
    try:
        sock.send(HTTP_STATUS_CODE[status_code])
    except Exception, e:
        sock.send(HTTP_STATUS_CODE[500])
    sock.send("\r\n")

def get_gmttime(mode, file=''):
    from email.utils import formatdate
    from datetime import datetime
    from time import mktime
    if mode == 'now':
        now = datetime.now()  # datetime.datetime(2014, 4, 10, 22, 29, 36, 957720)
        stamp = mktime(now.timetuple())  # 1397140176.0
    if mode == 'last-modified':
        stamp = os.path.getmtime(file)  # 1396614590.19
    date = formatdate(stamp, localtime=False, usegmt=True)  # 'Thu, 10 Apr 2014 14:29:36 GMT'
    return date

def send_http_header(sock, header, **kwargs):
    if header == "Content-Length":
        content_length = os.path.getsize(kwargs['file'])
        sock.send("{0}: {1}\r\n".format("Content-Length", content_length))
    if header == "Date":
        date = get_gmttime(mode='now')
        sock.send("{0}: {1}\r\n".format("Date", date))
    if header == "Content-Type":
        import mimetypes
        mimetypes.init()
        try:
            mime = mimetypes.types_map[os.path.splitext(kwargs['file'])[1]]
        except KeyError:
            # RFC 2046, The "octet-stream" subtype is used to indicate that a body contains arbitrary binary data.
            mime = "application/octet-stream"
        sock.send("{0}: {1}\r\n".format("Content-Type", mime))
    if header == "Server":
        sock.send("{0}: {1}\r\n".format("Server", "ProfessorWang Server/1.0"))
    if header == "Last-Modified":
        mtime = get_gmttime('last-modified', file=kwargs['file'])
        sock.send("{0}: {1}\r\n".format("Last-Modified", mtime))


def get_full_file_path(url_path):
    if is_path_a_dir(url_path):
        url_path += BASE_HTML_FILE

    file_path = BASE_HTML_DIR + url_path

    file_path = os.path.normpath(file_path)

    return file_path


def if_file_exists(file_path):
    return os.path.exists(file_path)


def read_html_from_file(file_path):

    if HAS_BUFFERD:
        if file_path in global_file_cache_list:
            yield global_file_cache_list[file_path]
        else:
            with open(file_path, 'rb') as html_file:
                global_file_cache_list[file_path] = ''
                line = html_file.read(BUFFER_SIZE)
                while len(line) > 0:
                    global_file_cache_list[file_path] += line
                    yield line
                    line = html_file.read(BUFFER_SIZE)
    else:
        with open(file_path, 'rb') as html_file:
            line = html_file.read(BUFFER_SIZE)
            while len(line) > 0:
                yield line
                line = html_file.read(BUFFER_SIZE)


def is_path_a_dir(path):
    if path[-1] == '/':
        return True
    else:
        return False


def phrase_other_header(request_list):
    pass


def read_config_file(file_path):
    cf = ConfigParser.ConfigParser()
    cf.read(file_path)
    # 返回所有的section
    try:
        BASE_HTML_FILE = cf.get("http", "default_page")
        DEFAULT_PORT = cf.getint("http", "default_port")
    except Exception, e:
        print e


if __name__ == '__main__':
    read_config_file("http.conf")
    server(DEFAULT_PORT)
