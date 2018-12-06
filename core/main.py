# -*- coding:utf-8 -*-
import socket
import select
import re
import time

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
                kv = header_line.split(":", 1)
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
        ), encoding="utf-8")


class HttpNotFound(HttpResponse):

    def __init__(self):
        super(HttpNotFound, self).__init__('404 Not Found')


class Future(object):
    """
    异步非阻塞模式时封装回调函数以及是否准备就绪
    """
    def __init__(self, callback):
        self.callback = callback
        self._ready = False
        self.value = None

    def set_result(self, value=None):
        self.value = value
        self._ready = True

    @property
    def ready(self):
        return self._ready


class TimeoutFuture(Future):
    """
    异步非阻塞超时
    """
    def __init__(self, timeout):
        super(TimeoutFuture, self).__init__(callback=None)
        self.timeout = timeout
        self.start_time = time.time()

    @property
    def ready(self):
        current_time = time.time()
        if current_time > self.start_time + self.timeout:
            self._ready = True
        return self._ready



class Snow():

    def __init__(self, router):
        self.router = router
        self.inputs = set()
        self.request = None
        self.async_request_handler = dict()

    def run(self, ip="localhost", port=9999):
        print("http://{}:{}".format(ip,port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
        sock.setblocking(False)
        sock.listen(128)
        self.inputs.add(sock)

        try:
            while True:
                # 使用select模块达到io多路复用
                readable_list, writeable_list, error_list = select.select(self.inputs, [], self.inputs, 0.005)
                for conn in readable_list:
                    if conn is sock:
                        # 新建连接
                        client, address = conn.accept()
                        client.setblocking(False)
                        self.inputs.add(client)
                    else:
                        # 把“接收数据get/post”这个封装到request里
                        _process = self.process(conn)
                        if isinstance(_process, HttpResponse):
                            conn.sendall(_process.response())
                            self.inputs.remove(conn)
                            conn.close()
                        else:
                            print(_process)
                            # 可以做其他操作
                            self.async_request_handler[conn] = _process
                self.polling_callback()

        except Exception as e:
            print(e)
            pass
        finally:
            sock.close()

    def polling_callback(self):
        for conn in list(self.async_request_handler.keys()):
            fut = self.async_request_handler[conn]
            if not fut.ready:
                continue
            if fut.callback:
                ret = fut.callback(self.request,fut)
                conn.sendall(ret.response())
            self.inputs.remove(conn)
            del self.async_request_handler[conn]
            conn.close()

    def process(self, conn):
        self.request = HttpRequest(conn)
        func = None
        for route in self.router:
            if len(route) == 2:
                if re.match(route[0], self.request.url):
                    func = route[1]
                    break
        if func:
            return func(self.request)
        else:
            return HttpNotFound()
