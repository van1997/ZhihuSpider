# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from zhihu_spider.utils.common import extract_num
import datetime
from zhihu_spider.settings import SQL_DATE_FORMAT,SQL_DATETIME_FORMAT
class ZhihuSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ZhihuQuestionItem(scrapy.Item):
    #知乎问题item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    answers_num = scrapy.Field()
    comments_num = scrapy.Field()
    follwers_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        #插入数据库时的sql语句
        insert_sql = 'INSERT INTO zhihu_question(zhihu_id,topics,url,title,' \
                     'content,answers_num,comments_num,follwers_num,' \
                     'click_num,crawl_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  ' \
                     'ON DUPLICATE KEY UPDATE topics=VALUES(topics),content=VALUES(content),' \
                     'answers_num=VALUES(answers_num), comments_num=VALUES(comments_num),' \
                     'follwers_num=VALUES(follwers_num),click_num=VALUES(click_num)'

        zhihu_id = self['zhihu_id'][0]
        topics = ','.join(self['topics'])
        url = ''.join(self['url'])
        title = self['title'][0]
        content = self['content'][0]
        answers_num = extract_num(''.join(self['answers_num']))
        comments_num = extract_num(''.join(self['comments_num']))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        follwers_num = extract_num(self['follwers_num'][0])
        click_num = extract_num(self['follwers_num'][1])

        params = (zhihu_id,topics,url,title,content,answers_num,comments_num,follwers_num,click_num,crawl_time,)

        return insert_sql,params

class ZhihuAnswerItem(scrapy.Item):
    #知乎回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    vote_up_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        #插入数据库时的sql语句
        insert_sql = 'INSERT INTO zhihu_answer(zhihu_id,url,question_id,author_id,content,' \
                     'vote_up_num,comments_num,create_time,update_time,crawl_time)' \
                     'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)' \
                     'ON DUPLICATE KEY UPDATE content=VALUES(content),vote_up_num=VALUES (vote_up_num),' \
                     'comments_num=VALUES(comments_num),update_time=VALUES(update_time)'

        self['create_time'] = datetime.datetime.fromtimestamp(self['create_time']).strftime(SQL_DATETIME_FORMAT)
        self['update_time'] = datetime.datetime.fromtimestamp(self['update_time']).strftime(SQL_DATETIME_FORMAT)
        self['crawl_time'] = self['crawl_time'].strftime(SQL_DATETIME_FORMAT)

        params = (self['zhihu_id'],self['url'],self['question_id'],
                  self['author_id'],self['content'],self['vote_up_num'],self['comments_num'],
                  self['create_time'],self['update_time'],self['crawl_time'],)

        return insert_sql,params
