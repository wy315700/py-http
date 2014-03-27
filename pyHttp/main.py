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

BUFFER_SIZE = 4096

BASE_HTML_DIR = 'C:\\Users\\wangyang\\Downloads\\lame3.99.5'

BASE_HTML_FILE = 'index.html'

DEFAULT_PORT = 7777

def server(port):
    s = socket.socket()
    s.bind(('0.0.0.0', port))
    s.listen(500)
    while True:
        cli, addr = s.accept()
        gevent.spawn(handle_request, cli, gevent.sleep)
def handle_request(s, sleep):
    try:
        data = ''

        while True:
            tmp=s.recv(BUFFER_SIZE)

            data += tmp
            if len(tmp) < BUFFER_SIZE or len(tmp) == 0:
                break
        print data
        head_list = get_header_from_request(data)

        head = head_list[0]

        method = get_request_method(head)

        path   = get_request_path(head)



        s.send("http/1.0 200 OK\r\n\r\n")

        for buff in read_html_from_file(path):
            result = s.send(buff)
            print result
        
        # s.send(request_string)
        s.shutdown(socket.SHUT_WR)
        print '.','be killed'
    except Exception, ex:
        print ex
    finally:                                                                                                                                                                                                                                                                                                                                                                  
        s.close()

def get_header_from_request(request):
    req_list = request.split("\r\n")
    return req_list

def get_request_method(req):
    list = req.split(' ')
    return list[0]

def get_request_path(req):
    list = req.split(' ')
    return list[1]

def read_html_from_file(url_path):

    if is_path_a_dir(url_path):
        url_path += BASE_HTML_FILE

    file_path = BASE_HTML_DIR + url_path

    file_path = os.path.normpath(file_path)
    
    print file_path
    if not os.path.exists(file_path):
        # return 0
        pass


    with open(file_path,'rb') as html_file:
        line = html_file.read(2048)
        while len(line) > 0:
            yield line
            line = html_file.read(2048)

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
        print ex
    

if __name__ == '__main__':
    read_config_file("http.conf")
    server(DEFAULT_PORT)