#!/usr/bin/python
#-*- encoding: utf-8 -*-


def get_header_from_request(request):
    req_list = request.split("\r\n")
    return req_list

def parse_header(request_header_str):
    #print request_header_str
    header_info = {}

    header_list = get_header_from_request(request_header_str)  # 仅仅按\r\n分割
    try:
        # http header的主要参数
        httpMethod, httpUrl, httpVersion = header_list[0].split(' ', 3)
        header_info = {
			'method': httpMethod,
			'url': httpUrl,
			'version': httpVersion,
		}

        # http header的其他参数
        header_dict = {h[0:h.index(':')].strip().lower(): h[h.index(':') + 1:].strip()\
                for h in header_list if ':' in h}
        header_info['header'] = header_dict

    except KeyError:
        print('KeyError:\n', header_list)
    return header_info

if __name__ == '__main__':
	headerStr = '\
GET / HTTP/1.1\r\n\
Host: 127.0.0.1:7777\r\n\
Connection: keep-alive\r\n\
Cache-Control: max-age=0\r\n\
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n\
User-Agent: Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.117 Safari/537.36\r\n\
Accept-Encoding: gzip,deflate,sdch\r\n\
Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4\r\n\
Cookie: csrftoken=wrgtsbT8jQeSwoebyRbzlSCJ6BnrBIAY\r\n\
If-Modified-Since: Sat, 26 Apr 2014 14:08:02 GMT\r\n\
'

	parse_header(headerStr)