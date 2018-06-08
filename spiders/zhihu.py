# -*- coding: utf-8 -*-

from http import cookiejar
import scrapy
from urllib import parse
import re

from scrapy.loader import ItemLoader
from zhihu_spider.items import ZhihuQuestionItem,ZhihuAnswerItem
import requests
import json
import datetime
from zhihu_spider.utils.cookie_util import CookieMannager

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']

    cookieManager = CookieMannager()
    print(222)
    #answer第一页请求url
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}&sort_by=default'

    headers = {
        'Connection': 'keep-alive',
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    def start_requests(self):
        yield scrapy.Request(url='https://www.zhihu.com', cookies=self.cookieManager.get_cookie(),headers=self.headers, callback=self.parse)

    def parse(self, response):
        '''
        提取出页面所有url，并跟踪这些url进行进一步爬取
        如果url格式为/question/xxx则下载之后直接进入解析函数
        '''
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url,url) for url in all_urls]
        all_urls = filter(lambda x:True if x.startswith('https') else False,all_urls)
        for url in all_urls:
            url_match = re.match('(.*zhihu.com/question/(\d+))(/|$).*',url)
            if url_match:
                #如果提取到question相关的页面则下载后交给提取函数处理
                request_url = url_match.group(1)
                yield scrapy.Request(request_url,headers=self.headers,cookies=self.cookieManager.get_cookie(),callback=self.parse_question)
            else:
                #如果不是question页面则直接进一步跟踪
                yield scrapy.Request(url,headers=self.headers,cookies=self.cookieManager.get_cookie(),callback=self.parse)

    def parse_question(self,response):
        #处理question页面，从页面中提取出具体的question item
        item_loader = ItemLoader(item=ZhihuQuestionItem(),response=response)
        url_match = re.match('(.*zhihu.com/question/(\d+))(/|$).*',response.url)
        if url_match:
            question_id = url_match.group(2)
        item_loader.add_css("title",".QuestionHeader-title::text")
        item_loader.add_css("content",".QuestionHeader-detail")
        item_loader.add_value("url",response.url)
        item_loader.add_value("zhihu_id",question_id)
        if "answer" in response.url:
            answers_num_selector = ".QuestionMainAction::text"
        else:
            answers_num_selector = ".List-headerText span::text"
        item_loader.add_css("answers_num",answers_num_selector)
        item_loader.add_css("comments_num",".QuestionHeader-Comment button::text")
        item_loader.add_css("follwers_num",".NumberBoard-itemValue::text")
        item_loader.add_css("topics",".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id,20,0),headers=self.headers,cookies=self.cookieManager.get_cookie(),callback=self.parse_answer)
        yield question_item

    def parse_answer(self,response):
        #处理answer
        ans_json = json.loads(response.body.decode('utf8'))
        is_end = ans_json['paging']['is_end']
        totals = ans_json['paging']['totals']
        next_url = ans_json['paging']['next']

        #提取answer的具体字段
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['vote_up_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['create_time'] = answer['created_time']
            answer_item['update_time'] = answer['updated_time']
            answer_item['crawl_time'] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url,headers=self.headers,cookies=self.cookieManager.get_cookie(),callback=self.parse_answer)