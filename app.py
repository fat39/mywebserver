# -*- coding:utf-8 -*-

from core.main import Snow,HttpResponse,TimeoutFuture,Future

def index(request):
    print(request.url)
    print(request.headers_bytes)
    print(request.body_bytes)
    return HttpResponse("index ok")


def async(request):

    obj = TimeoutFuture(5)

    return obj


request_list = []


def callback(request, future):
    return HttpResponse(future.value)


def req(request):
    obj = Future(callback=callback)

    request_list.append(obj)

    return obj


def stop(request):
    obj = request_list[0]

    del request_list[0]

    obj.set_result('done')

    return HttpResponse('stop')


router = [
    (r"/index/",index),
    (r"/async/",async),
    (r'/req/', req),
    (r'/stop/', stop),
]


if __name__ == '__main__':

    Snow(router).run()