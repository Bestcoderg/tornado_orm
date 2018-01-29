# coding:utf-8
"""

测试部分,用于模拟一个外部调用

大致希望的调用方式

::

    import tornado_mysql_orm

    setting = {
        'default':{
            "host":'',
            'password':'',
        },
        'anthor_db':{
            'host':'',
            'password':'',
        }
    }

    tornado_mysql_orm.set_connection(setting=setting)
    class UserInfo(tornado_mysql_orm.BaseModel):
        name = tornado_mysql_orm.ChardFiled(name='姓名',primark_key=True)
        ...

其他地方调用时

::

    import UserInfo
    data = yield UserInfo.objects.get(name='123')
    data = yield UserInfo.objects.filter(name='123').do()
    ...

所以此部分主要是配置model，具体的使用将在另外一个文件，尽力模拟真实使用环境

"""

try:
    from tornado_orm import tornado_mysql_orm
except:
    import tornado_mysql_orm  # import BaseModel,BaseField

setting = {
    'default': {
        'connect_kwargs': {
            'host': '192.168.99.100',
            'port': 3306,
            'user': 'root',
            'passwd': 'root',
            'db': 'tornado_mysql_orm'
        },
        'other_kwargs': {
            'max_idle_connections': 1,
            'max_recycle_sec': 3
        }

    }
}
tornado_mysql_orm.set_sql_db(setting)
tornado_mysql_orm.make_pool()


class Test_table(tornado_mysql_orm.BaseModel):
    __table__ = 'test'
    name = tornado_mysql_orm.StringField(name="姓名")
    sex = tornado_mysql_orm.StringField(name='性别')
    age = tornado_mysql_orm.StringField(name='年龄')
