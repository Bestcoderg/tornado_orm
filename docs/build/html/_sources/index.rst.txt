.. mysqldb documentation master file, created by
   sphinx-quickstart on Sat Jan 27 09:21:17 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tornado_mysql_orm 初衷
===================================

我试图封装一个tornado 可以使用的，仅支持异步的，关于mysql 的orm

首先需要满足的是单张表的增删改查，然后是支持多张表的增删改查

至于锁等稍微复杂的操作，暂时不考虑

而调用方式上，尽可能希望它和django的orm相近，降低学习成本

.. toctree::
   :maxdepth: 2
   :caption: 内容:

   modules


其他
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
