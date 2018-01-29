# coding:utf-8

"""

此处用于模拟实际的使用

"""

from tornado import gen,ioloop

try:
    from tornado_orm import model_config
except:
    import model_config


@gen.coroutine
def run_server():
    while True:
        data = yield model_config.Test_table.find(1)
        print(data)
        data = yield model_config.Test_table(name='liuhongyu',age='24',sex='1').save()
        print(data)
        break

def main():
    run_server()
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()