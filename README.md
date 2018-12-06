参考：http://www.cnblogs.com/wupeiqi/p/6536518.html

# mywebserver
开发简单的io多路复用的webserver

##核心
```
# 使用select达到io多路复用的目的
readable_list, writeable_list, error_list = select.select(self.inputs, [], self.inputs, 0.005)
```

## process
```
    def process(self, conn):
        # 初始化request对象，分析头部，可在这加一些headers的检测
        self.request = HttpRequest(conn)
        
        func = None
        
        # 匹配router
        for route in self.router:
            if len(route) == 2:
                if re.match(route[0], self.request.url):
                    func = route[1]
                    break
        if func:
            # 返回func对应的是用户的视图函数view，返回的是response对象
            return func(self.request)
```
### HttpRequest对象
```
    def initial(self):
        略
    def initial_headers(self):
        略
```

### HttpResponse对象
```
class HttpResponse():
    ''' 可以换种写法，比如单独一个headers_dict，再结合body '''
    def response(self):
        
        略
```

## Future对象
```
    待看了tornado的Future再写这里
    通过ready和callback，进行自定制操作
```