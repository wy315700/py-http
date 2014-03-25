#xiaorui.cc
import sys
import socket
import time

try:
    import gevent
    from gevent import monkey

    monkey.patch_all()
except Exception, e:
    raise e

BUFFER_SIZE = 4096

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

        s.send('''http/1.0 200 OK

                  Hello World! this is xiaorui.cc !!!\r\n''')
        print data
        # s.send(request_string)
        s.shutdown(socket.SHUT_WR)
        print '.','be killed'
    except Exception, ex:
        print ex
    finally:
                                                                                                                                                                                                                                                                                                                                                                                   
        s.close()
if __name__ == '__main__':
    server(7777)