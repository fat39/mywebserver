# -*- coding:utf-8 -*-

from core.main import Snow,HttpResponse

def index(request):
    print(request.url)
    print(request.headers_bytes)
    print(request.body_bytes)
    return HttpResponse("index ok")


router = [
    (r"/index/",index),
]


if __name__ == '__main__':
    print("http://127.0.0.1:9999")
    Snow(router).run()