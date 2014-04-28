#!/usr/bin/python
#-*- encoding: utf-8 -*-
import socket
import time
import ConfigParser
import HttpHeaderParse
import HttpCore

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

DEFAULT_PORT = 7777

EXPIRES_ON = False

EXPIRES_FILE_REG = {}

HTTP_STATUS_CODE = {
    200: "200 OK",
    304: "304 Not Modified",
    404: "404 Not Found",
    500: "500 Internal Server Error",
}

import logging
import logging.config
logging.config.fileConfig("logging.conf")
logger = logging.getLogger('')


def server(port):
    s = socket.socket()
    s.bind(('0.0.0.0', port))
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

        # 空内容
        if not len(data):
            return

        # print data
        header_info = HttpHeaderParse.parse_header(data)

        # 记录访问日志
        peer = s.getpeername()
        logger.info(str(peer[0]) + ":" + str(peer[1]) + " " + header_info['method'] +" " + header_info['url'])

        file_full_path = HttpCore.get_full_file_path(header_info['url']) # 获得文件的全路径
        # 获取文件信息
        fileInfo = HttpCore.get_file_info(file_full_path)

        # 响应http header消息
        def normal_response(fileInfo):
            send_http_header(s, "Content-Length", fileInfo['size'])
            send_http_header(s, "Date", HttpCore.get_gmttime_str())
            send_http_header(s, "Content-Type", fileInfo['mimetype'])
            send_http_header(s, "Server", 'ProfessorWang Server/1.0')
            send_http_header(s, "Last-Modified", fileInfo['mtimestr'])

            expiresInfo = check_expires(file_full_path)
            if EXPIRES_ON and expiresInfo['is']:
                send_http_header(s, "expires", HttpCore.get_gmttime_str(expires=expiresInfo['sec']))

            s.send("\r\n")

        # 响应文本内容
        def content_response(fileInfo):
            for buff in read_html_from_file(fileInfo['filePath']):
                result = s.send(buff)

        if fileInfo['exists']:
            # 文件存在
            if "if-modified-since" in header_info['header']:  #有modf参数
                check_to_time = header_info['header']["if-modified-since"]
                check_to_time = time.mktime(time.strptime(check_to_time, "%a, %d %b %Y %H:%M:%S GMT"))
                if fileInfo['mtime'] <= check_to_time:
                    send_http_status_code(s, 304)
                    normal_response(fileInfo)
                else:
                    send_http_status_code(s, 200)
                    normal_response(fileInfo)
                    content_response(fileInfo)
            else:
                send_http_status_code(s, 200)
                normal_response(fileInfo)
                content_response(fileInfo)
        else:
            # 文件不存在
            send_http_status_code(s, 404)

        #s.shutdown(socket.SHUT_RDWR)
        #print '.', 'be killed'
    except Exception, ex:
        print ex
        logger.debug(str(peer[0]) + ":" + str(peer[1]) + " " + ex + " " + data)
    finally:
        s.close()


def send_http_status_code(sock, status_code):
    sock.send("http/1.0 ")
    try:
        sock.send(HTTP_STATUS_CODE[status_code])
    except Exception, e:
        sock.send(HTTP_STATUS_CODE[500])
    sock.send("\r\n")

def send_http_header(sock, headerKey, headerValue):
    sock.send("{0}: {1}\r\n".format(headerKey, headerValue))

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

def read_config_file(file_path):
    cf = ConfigParser.ConfigParser()
    cf.read(file_path)
    # 返回所有的section
    try:
        global BASE_HTML_FILE, DEFAULT_PORT, EXPIRES_ON, EXPIRES_FILE_REG  # add global
        BASE_HTML_FILE = cf.get("http", "default_page")
        DEFAULT_PORT = cf.getint("http", "default_port")
        EXPIRES_ON = cf.getboolean("http", "expires")
        EXPIRES_FILE_REG = eval(cf.get("http", "expiresreg"))  # to dict
    except Exception, e:
        print e

		
def check_expires(url):
    expires = {'is':0}
    import re
    for preg in EXPIRES_FILE_REG:
        m = re.search(preg, url)
        if m:
            expires['is'] = 1
            expires['sec'] = EXPIRES_FILE_REG[preg]
            break
    return expires

if __name__ == '__main__':
    read_config_file("http.conf")
    server(DEFAULT_PORT)
