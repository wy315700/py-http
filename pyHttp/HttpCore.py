#!/usr/bin/python
#-*- encoding: utf-8 -*-

import os, time

BASE_HTML_DIR = '../html'

BASE_HTML_FILE = 'index.html'

# 获得文件的详细信息
def get_file_info(filePath):
    httpFileInfo = {
        'filePath':filePath
    }
    if os.path.isfile(filePath) and os.path.exists(filePath):
        httpFileInfo['exists'] = 1
        httpFileInfo['size'] = os.path.getsize(filePath)
        mtime= os.path.getmtime(filePath) # 文件的修改时间
        httpFileInfo['mtime'] = time.mktime(time.gmtime(mtime)) # 转化为GMT时间

        from email.utils import formatdate
        httpFileInfo['mtimestr'] = formatdate(mtime, localtime=False, usegmt=True)

        import mimetypes
        mimetypes.init()
        try:
            mime = mimetypes.types_map[os.path.splitext(filePath)[1]]
        except KeyError:
            # RFC 2046, The "octet-stream" subtype is used to indicate that a body contains arbitrary binary data.
            mime = "application/octet-stream"
        httpFileInfo['mimetype'] = mime

    else:
        httpFileInfo['exists'] = 0
    return httpFileInfo

def get_gmttime(stamp):
    return time.mktime(time.gmtime(stamp)) # 转化为GMT时间

def get_gmttime_str(expires=0):
    from email.utils import formatdate
    from datetime import datetime
    from time import mktime
    now = datetime.now()  # datetime.datetime(2014, 4, 10, 22, 29, 36, 957720)
    stamp = mktime(now.timetuple())  # 1397140176.0
    stamp = mktime(now.timetuple())+expires   # 1397140176.0
    date = formatdate(stamp, localtime=False, usegmt=True)  # 'Thu, 10 Apr 2014 14:29:36 GMT'
    return date


def is_path_a_dir(path):
    if path[-1] == '/':
        return True
    else:
        return False


def get_full_file_path(url_path):
    if is_path_a_dir(url_path):
        url_path += BASE_HTML_FILE

    file_path = BASE_HTML_DIR + url_path

    file_path = os.path.normpath(file_path)

    return file_path