#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import hmac
import hashlib
import json
import matplotlib.pyplot as plt
from PIL import Image
from zhihu_spider.settings import ZHIHU_ACCOUNTS
from zhihu_spider.utils.captcha_util import *
import threading

HEADERS = {
    'Connection': 'keep-alive',
    'Host': 'www.zhihu.com',
    'Referer': 'https://www.zhihu.com/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/56.0.2924.87 Mobile Safari/537.36'
}
LOGIN_URL = 'https://www.zhihu.com/signup'
LOGIN_API = 'https://www.zhihu.com/api/v3/oauth/sign_in'
FORM_DATA = {
    'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
    'grant_type': 'password',
    'source': 'com.zhihu.web',
    'username': '',
    'password': '',
    # 改为'cn'是倒立汉字验证码
    'lang': 'en',
    'ref_source': 'homepage'
}


class ZhihuLogin(object):

    def __init__(self):
        self.login_url = LOGIN_URL
        self.login_api = LOGIN_API
        self.login_data = FORM_DATA.copy()
        self.session = requests.session()
        self.session.headers = HEADERS.copy()

    def login(self,username, password,cookies=None):
        """
        模拟登录知乎:
        :param username: 登录手机号
        :param password: 登录密码
        :return: cookies
        """
        headers = self.session.headers.copy()
        headers.update({
            'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
            'X-Xsrftoken': self._get_token()
        })
        if '+' not in username:
            username = '+86' + username
        self.login_data.update({
            'username': username,
            'password': password
        })
        timestamp = str(int(time.time()*1000))
        self.login_data.update({
            'captcha': self._get_captcha(headers),
            'timestamp': timestamp,
            'signature': self._get_signature(timestamp)
        })

        resp = self.session.post(self.login_api, data=self.login_data, headers=headers)
        if 'error' in resp.text:
            print(re.findall(r'"message":"(.+?)"', resp.text)[0])
        else :
            return self.check_login()
        print('登录失败')
        return False

    def check_login(self):
        """
        检查登录状态，访问登录页面出现跳转则是已登录，
        如登录成功返回当前 Cookies
        :return: cookies
        """
        resp = self.session.get(self.login_url, allow_redirects=False)
        if resp.status_code == 302:
            print('登录成功')
            return self.session.cookies
        return False

    def _get_token(self):
        """
        从登录页面获取 token
        :return:
        """
        resp = self.session.get(self.login_url)
        token = re.findall(r'_xsrf=([\w|-]+)', resp.headers.get('Set-Cookie'))[0]
        return token

    def _get_captcha(self, headers):
        """
        请求验证码的 API 接口，无论是否需要验证码都需要请求一次
        如果需要验证码会返回图片的 base64 编码
        根据头部 lang 字段匹配验证码，需要人工输入
        :param headers: 带授权信息的请求头部
        :return: 验证码的 POST 参数
        """
        lang = headers.get('lang', 'en')
        if lang == 'cn':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        resp = self.session.get(api, headers=headers)
        show_captcha = re.search(r'true', resp.text)
        if show_captcha:
            put_resp = self.session.put(api, headers=headers)
            img_base64 = re.findall(
                r'"img_base64":"(.+)"', put_resp.text, re.S)[0].replace(r'\n', '')
            with open('./captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(img_base64))
            img = Image.open('./captcha.jpg')
            if lang == 'cn':
                plt.imshow(img)
                print('点击所有倒立的汉字，按回车提交')
                points = plt.ginput(7)
                capt = json.dumps({'img_size': [200, 44],
                                   'input_points': [[i[0]/2, i[1]/2] for i in points]})
            else:
                img.show()
                capt = input('请输入图片里的验证码：')
            # 这里必须先把参数 POST 验证码接口
            self.session.post(api, data={'input_text': capt}, headers=headers)
            return capt
        return ''

    def _get_signature(self, timestamp):
        """
        通过 Hmac 算法计算返回签名
        实际是几个固定字符串加时间戳
        :param timestamp: 时间戳
        :return: 签名
        """
        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = self.login_data['grant_type']
        client_id = self.login_data['client_id']
        source = self.login_data['source']
        ha.update(bytes((grant_type + client_id + source + timestamp), 'utf-8'))
        return ha.hexdigest()

'''
Cookie管理器，具有添加cookie、cookie解禁等功能
'''
class CookieMannager():

    #cookie池，用于保存cookie
    cookies_pool = {}

    def __init__(self):
        self.zhihu_login()

    def zhihu_login(self):
        for account in ZHIHU_ACCOUNTS:
            cookies = ZhihuLogin().login(account['username'],account['password'])
            if cookies:
                self.cookies_pool[account['index']]=requests.utils.dict_from_cookiejar(cookies)

    def get_cookie(self):
        #无效cookie索引列表
        invalid_index=[]
        while True:
            while True:
                #随机从cookie池中选取cookie
                index = random.randint(0,self.cookies_pool.__len__()-1)
                if index not in invalid_index:
                    break
            cookies = self.cookies_pool[index]
            #请求知乎网站测试帐号是否被禁
            status_code = requests.get('https://www.zhihu.com',headers=HEADERS,cookies=cookies, allow_redirects=False).status_code
            print(index,status_code)
            if status_code==200:
                return cookies
            else:
                invalid_index.append(index)
                #破解滑动或字符型验证码
                threading._start_new_thread(cap_crack,(cookies,))
