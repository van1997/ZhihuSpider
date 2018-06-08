# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi

class ZhihuSpiderPipeline(object):
    def process_item(self, item, spider):
        return item



class MySQLTwistedPipeline(object):

    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):
        dbparams = dict(
            host = settings['MYSQL_HOST'],
            db = settings['MYSQL_DBNAME'],
            user = settings['MYSQL_USER'],
            passwd = settings['MYSQL_PASSWORD'],
            charset = 'utf8mb4',
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb',**dbparams)

        return cls(dbpool)

    def process_item(self,item,spider):
        #使用twisted把数据库操作变成异步执行
        query = self.dbpool.runInteraction(self.do_insert,item)
        #处理异常
        query.addErrback(self.handle_error)

    def handle_error(self,failure):
        #处理异步插入异常
        print(failure)

    def do_insert(self,cursor,item):
        #执行数据插入
        insert_sql,params = item.get_insert_sql()

        cursor.execute(insert_sql,params)

