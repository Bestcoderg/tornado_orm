# coding:utf-8

"""

试图封装orm，所有的操作将在此处完成

初步完成

::

    表模型本身的find(),save()功能,但字段限制较少，各自未进行详细处理

"""
import logging

from tornado import gen

from tornado_mysql import pools

_SQL_SETTING = None


def set_sql_db(setting):
    """
    配置需要连接的数据库配置

    形如
    ::

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

    :param setting: dict 采用的是tornado_mysql 这个异步库，并且用的是连接池
    :return: None
    """
    global _SQL_SETTING
    _SQL_SETTING = setting


_DB_ROUTER = lambda table_name: 'default'

_DB_CONNECTION = dict(default=None)


def set_router(func):
    """
    用于设定db 路由

    函数形如

    ::

        def func(table_name):
            if table_name in [...]:
                return db_name_a
            elfi table_name in [...]:
                return db_name_b
            ....

    :param func: 传入的路由函数
    :return: None
    """
    global _DB_ROUTER
    _DB_ROUTER = func


def _create_args_string(number_in):
    """
    安装传入的数据，生成百分号组成的字符串返回，用于insert语句

    :param number_in:
    :return:
    """
    data_list = ['%s' for _ in range(number_in)]
    return ', '.join(data_list)


def make_pool():
    """
    配置了数据库，并且穿进去了路由(默认返回default),通过make_poll 建立各个数据库的连接池，需要放在构造的表模型前面

    :return: None
    """
    try:
        for k, v in _SQL_SETTING.items():
            _DB_CONNECTION[k] = pools.Pool(v['connect_kwargs'], **v['other_kwargs'])
        return True
    except Exception as e:
        logging.error("连接失败：{}".format(e))
        return False


def _change_sql_data_to_data(description, data):
    """
    将查询的数据，[{},{}]的形式

    :param description: 描述
    :param data: 数据
    :return:数组中包含字典
    """
    column_names = [d[0] for d in description]
    return [dict(zip(column_names, row)) for row in data]


@gen.coroutine
def _execute(sql, args=None, db_name='default'):
    """
    此函数将真正的执行所有的sql语句

    :param sql:sql 语句
    :return:列表形式的内容，元素为字典
    """
    if args == None:
        args = []
    connection = _DB_CONNECTION[db_name]
    try:
        data = yield connection.execute(sql, args)
    except Exception as e:
        logging.warning(sql)
        logging.warning(args)
        logging.warning("执行失败：{} ".format(e))
        return {}
    all_data = data.fetchall()
    if all_data:
        data = _change_sql_data_to_data(data.description, all_data)
    else:
        data = {}

    raise gen.Return(data)


class PrimaryKeyError(Exception):
    """
    提示主键重复的错误

    """

    def __init__(self, message=''):
        self.message = message
        super(PrimaryKeyError, self).__init__()

    def __str__(self):
        return self.message


class QuerySet(object):
    """
    此类用于按需生成sql语句，最后调用do()执行

    此部分未在orm中具体启用，即模仿django的orm的objects 未实际开始
    """

    def __init__(self, primary_key, mappings, table_name):
        self.fileds_all = mappings.keys()  # 所有的字段
        self.primay_key = primary_key  # 主键
        self.mappings = mappings  # 映射
        self.table_name = table_name  # 表名
        self.needs_files = False  # 需要的字段
        self.where = False  # 条件字段
        super(QuerySet, self).__init__()

    @gen.coroutine
    def do(self):
        """
        由gen.coroutine 装饰，一个异步函数，用于支持tornado的协程异步

        :return: future sqldata
        """
        sql_line = self._get_sql_line()
        data = yield _execute(sql_line)
        raise gen.Return(data)

    def filter(self, **kwargs):
        """
        不断更新

        :param kwargs: type dict,对应where中的参数
        :return: self
        """
        self.where = kwargs
        return self

    def _get_fileds(self):
        """
        根据需要查询的字段，生成select 后的选择字段字符串

        :return: type strf
        """
        if not self.needs_files:
            return ', '.join(self.fileds_all)
        # list
        return ', '.join(self.needs_files)

    def _get_tables(self):
        """
        返回表名字

        :return:
        """
        return self.table_name

    def _get_where(self):
        if not self.where:
            return ''
        else:
            where_list = []
            for k, v in self.where.items():
                where_list.append('{} = {}'.format(k, v))
            return ' and '.join(where_list)

    def _get_sql_line(self):
        files = self._get_fileds()
        table = self._get_tables()
        where = self._get_where()
        sql_line = "select {} from {}".format(files, table)
        if where:
            sql_line = "{} where {}".format(sql_line, where)
        return sql_line

    def __str__(self):
        return self._get_sql_line()


def _born_table_name_by_model_name(model_name):
    return model_name


class MetaClass(type):
    """
    元类
    """

    def __new__(cls, name, bases, attrs):
        """

        :param name:
        :param bases:
        :param attrs:
        :return:
        """
        if name == 'BaseModel':
            return super(MetaClass, cls).__new__(cls, name, bases, attrs)
        table_name = attrs.get('__table__') or _born_table_name_by_model_name(name)
        mappings = dict()
        fields = []
        primary_key = False
        for k, v in attrs.items():
            if isinstance(v, BaseField):
                mappings[k] = v
                if v.primary_key:
                    if primary_key:
                        raise PrimaryKeyError("主键重复")
                    primary_key = k
                else:
                    fields.append(k)

        for a in mappings:
            attrs.pop(a)

        if not primary_key:
            logging.debug("缺少主键，默认主键为id")
            primary_key = 'id'
            mappings[primary_key] = BaseField(name='id', primary_key=True, column_type=False)

        escaped_fields = list(map(lambda f: '`{}`'.format(f), fields))  # 防止sql攻击使用此功能

        attrs['__mappings__'] = mappings
        attrs['__table__'] = table_name
        attrs['__primary_key__'] = primary_key
        attrs['__fields__'] = fields
        # 构造默认的select，insert，update，delete
        attrs['__select__'] = 'select `{}`, {} from {}'.format(primary_key, ', '.join(escaped_fields), table_name)
        attrs['__update__'] = 'update `{}` set {} where {}=?'.format(table_name, ','.join(
            map(lambda f: '`{}`=?'.format(f), fields)), primary_key)  # update 是根据主键更新
        attrs['__delete__'] = 'delete from `{}` where `{}`=?'.format(table_name, primary_key)  # 依据主键删除)
        attrs['__db_name__'] = _DB_ROUTER(table_name)
        attrs['__insert__'] = 'insert into `{}` ({}) value ({})'.format(table_name, ','.join(escaped_fields),
                                                                        _create_args_string(len(escaped_fields)))
        # 暂时放弃
        # 尝试构造queryset对象用于查询
        cls.objects = QuerySet(primary_key=primary_key, mappings=mappings, table_name=table_name)
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)


class BaseModel(dict, metaclass=MetaClass):
    """
    构建表的基础类
    """

    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        try:
            return self[item]
        except:
            raise AttributeError("无此属性")

    def __setattr__(self, key, value):
        self[key] = value

    def get_value(self, key):
        return getattr(self, key, None)

    def get_value_or_default(self, key):

        value = getattr(self, key, None)
        field = self.__mappings__[key]
        if value is not None:
            field.default = value
        return field.get_value()

    @classmethod
    @gen.coroutine
    def find(cls, pk):
        """
        通过主键查找

        :param pk: 主键值
        :return:
        """
        sql_line = '{} where `{}`=%s'.format(cls.__select__, cls.__primary_key__)
        data = yield _execute(sql_line % pk, db_name=cls.__db_name__)
        datas = [cls(**data_dic) for data_dic in data]

        raise gen.Return(datas)

    @gen.coroutine
    def save(self):
        args = list(map(self.get_value_or_default, self.__fields__))
        data = yield _execute(self.__insert__ % tuple(args),args=[])
        raise gen.Return(data)


class BaseField(object):
    def __init__(self, name, column_type, primary_key=False, default=None):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
        super(BaseField, self).__init__()

    def __str__(self):
        return '<{}, {}: {}>'.format(self.__class__, self.column_type, self.name)

    def get_value(self):
        return self.default


class StringField(BaseField):
    """
    字符类字段
    """

    def __init__(self, name=None, primary_key=False, default=None, column_type='varchar(100)'):
        super(StringField, self).__init__(name, column_type, primary_key, default)

    def get_value(self):

        if callable(self.default):
            return self.default
        else:
            return "'{}'".format(self.default)
