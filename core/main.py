# -*- coding:utf-8 -*-
import socket
import select


class Snow():

    def __init__(self):
        self.inputs = set()

    def run(self,ip="localhost",port=9999):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip,port))
        sock.setblocking(False)
        sock.listen(128)
        self.inputs.add(sock)

        while True:
            # 使用select模块达到io多路复用
            readable_list, writeable_list, error_list = select.select(self.inputs, [], self.inputs, 0.005)
            for conn in readable_list:
                if sock is conn:
                    # 新建连接
                    client,address = conn.accept()
                    client.setblocking(False)
                    self.inputs.add(client)
                else:
                    # 接收数据get/post
                    recv_bytes = bytes("",encoding="utf-8")
                    while True:
                        try:
                            _recv = conn.recv(8096)
                            recv_bytes += _recv
                        except:
                            # 循环收齐数据后，由于set blocking(False)，所以出发except
                            break
                    print(recv_bytes)
                    conn.sendall(bytes("hello world",encoding="utf-8"))
                    self.inputs.remove(conn)


