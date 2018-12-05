# -*- coding:utf-8 -*-
import socket
import select


class HttpRequest():
    def __init__(self, conn):
        self.conn = conn
        self.raw_bytes = bytes("", encoding="utf-8")
        self.headers_bytes = bytes("", encoding="utf-8")
        self.body_bytes = bytes("", encoding="utf-8")
        self.initial()

    def initial(self):
        # 接收数据get/post
        while True:
            try:
                _recv = self.conn.recv(8096)
                self.raw_bytes += _recv
            except:
                # 循环收齐数据后，由于set blocking(False)，所以出发except
                break
        self.headers_bytes, self.body_bytes = self.raw_bytes.split(bytes("\r\n\r\n", encoding="utf-8"))


class HttpResponse():
    def __init__(self, content=""):
        self.content = content

    def response(self):
        return self.content


class Snow():

    def __init__(self):
        self.inputs = set()

    def run(self, ip="localhost", port=9999):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
        sock.setblocking(False)
        sock.listen(128)
        self.inputs.add(sock)

        while True:
            # 使用select模块达到io多路复用
            readable_list, writeable_list, error_list = select.select(self.inputs, [], self.inputs, 0.005)
            for conn in readable_list:
                if sock is conn:
                    # 新建连接
                    client, address = conn.accept()
                    client.setblocking(False)
                    self.inputs.add(client)
                else:
                    # 接收数据get/post
                    request = self.process(conn)
                    print(request.raw_bytes)
                    conn.sendall(bytes("HTTP/1.1 200 OK\r\nContent-Length: {len}\r\n\r\n{body}".format(len=len("hello world"),body="hello world"), encoding="utf-8"))
                    self.inputs.remove(conn)

    def process(self,conn):
        request = HttpRequest(conn)
        return request

