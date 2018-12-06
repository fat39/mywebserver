# -*- coding:utf-8 -*-
import socket
import select
import re

class HttpRequest():
    def __init__(self, conn):
        self.conn = conn
        self.headers_bytes = bytes("", encoding="utf-8")
        self.body_bytes = bytes("", encoding="utf-8")
        self.initial()

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



class HttpResponse():
    def __init__(self, content=""):
        self.content = content
        self.template = "HTTP/1.1 200 OK\r\nContent-Length: {len}\r\n\r\n{body}"

    def response(self):
        return bytes(self.template.format(
            len=len(self.content),
            body=self.content,
        ),encoding="utf-8")


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

    def process(self,conn):
        request = HttpRequest(conn)
        header_line1 = str(request.headers_bytes.split(b"\r\n",1)[0],encoding="utf-8")
        method,url,version = header_line1.split()
        func = None
        for kv in self.router:
            if len(kv) == 2:
                re_url = kv[0]
                if re.match(re_url,url):
                    func = kv[1]
                    break
        if func:
            return func()

