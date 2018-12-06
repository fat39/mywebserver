# -*- coding:utf-8 -*-
import socket
import select
import re

class HttpRequest():
    def __init__(self, conn):
        self.conn = conn
        self.headers_dict = dict()
        self.headers_bytes = bytes("", encoding="utf-8")
        self.body_bytes = bytes("", encoding="utf-8")
        self.method = ""
        self.url = ""
        self.version = ""

        self.initial()
        self.initial_headers()

    @property
    def headers_str(self):
        return str(self.headers_bytes, encoding="utf-8")

    def initial(self):
        # 接收数据get/post
        split_flag = False
        while True:
            try:
                _recv_bytes = self.conn.recv(8096)
            except:
                # 循环收齐数据后，由于setblocking(False)，所以触发except
                break

            if split_flag:
                self.body_bytes += _recv_bytes
            else:
                self.headers_bytes += _recv_bytes
                if b"\r\n\r\n" in self.headers_bytes:
                    self.headers_bytes, self.body_bytes = self.headers_bytes.split(b"\r\n\r\n", 1)
                    split_flag = True

    def initial_headers(self):
        header_lines = self.headers_str.split("\r\n")
        first_line = header_lines[0].split()
        if len(first_line) == 3:
            self.method, self.url, self.version = first_line

            for header_line in header_lines:
                kv = header_line.split(":",1)
                if len(kv) == 2:
                    k, v = kv
                    self.headers_dict[k] = v


class HttpResponse():
    def __init__(self, content=""):
        self.content = content
        self.template = "HTTP/1.1 200 OK\r\nContent-Length: {len}\r\n\r\n{body}"

    def response(self):
        return bytes(self.template.format(
            len=len(self.content),
            body=self.content,
        ),encoding="utf-8")


class HttpNotFound(HttpResponse):

    def __init__(self):
        super(HttpNotFound, self).__init__('404 Not Found')


class Snow():

    def __init__(self,router):
        self.router = router
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
                    # 把“接收数据get/post”这个封装到request里
                    response = self.process(conn)
                    if isinstance(response,HttpResponse):
                        conn.sendall(response.response())
                        self.inputs.remove(conn)
                        conn.close()
                    else:
                        # 可以做其他操作
                        pass


    def process(self,conn):
        self.request = HttpRequest(conn)
        func = None
        for route in self.router:
            if len(route) == 2:
                if re.match(route[0],self.request.url):
                    func = route[1]
                    break
        if func:
            return func(self.request)
        else:
            return HttpNotFound()


