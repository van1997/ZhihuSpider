import requests
from http import cookiejar
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import html
import cv2
import numpy as np
from selenium.webdriver import ActionChains
import time
import random
import threading

lock = threading.Lock()

def cap_crack(cookies):
    lock.acquire()
    executable_path = '/usr/lib64/firefox/geckodriver'
    browser = webdriver.Firefox(executable_path=executable_path)
    #加载cookie实现知乎登录
    browser.get('https://zhihu.com')
    for k,v in cookies.items():
        print(k)
        browser.add_cookie({'name':k,'value':v})
    #刷新页面实现cookie发送
    browser.refresh()

    #尝试五次
    for i in range(5):
        try:
            #等待iframe出现
            WebDriverWait(browser,10).until(EC.presence_of_element_located((By.ID,'root')))
            WebDriverWait(browser,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#root > div > div > section > div > div>iframe')))
            #切换iframe
            browser.switch_to.frame(browser.find_element_by_css_selector('#root>div>div>section>div>div>iframe'))
            #等待滑块出现
            WebDriverWait(browser,10).until(EC.presence_of_element_located((By.ID,'tcaptcha_drag_button')))
            result = slide_cap(browser)
            if result=='success':
                return 'success'
        except:
            # 如果等待滑块超时则可能是字符型验证码,识别尚未完成
            # char_cap()
            pass
        finally:
            #关闭浏览器
            browser.close()
    lock.release()

def slide_cap(browser):

    browser.switch_to.default_content()

    #等待滑动验证码图片出现
    WebDriverWait(browser,10).until(EC.presence_of_element_located((By.XPATH,'//img[@id="slideBkg" and @src]')))

    slide = browser.find_element_by_id('tcaptcha_drag_button')

    #下载验证码图片
    page = browser.page_source
    template_img_url = html.unescape(re.match('.*img.*?id="slideBkg"\ssrc="(.*?)".*',page).group(1))

    target_img_url = template_img_url[:-1]+'2'
    img_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    #模版图片
    with open('template_color.jpeg','wb') as f:
        f.write(requests.get('https://captcha.guard.qcloud.com'+template_img_url,headers=img_headers).content)
        f.close()
    #目标图片
    with open('target_color.jpeg','wb') as f:
        f.write(requests.get('https://captcha.guard.qcloud.com'+target_img_url,headers=img_headers).content)
        f.close()

    #取得距离
    distance = get_distance()
    #根据生成位移
    steps = get_steps(distance)
    #也可以采用自己采集的位置生成轨迹，附上生成代码
    #steps = [10,24,34,20,39,24,6,17,4]
    #if distance>178 :
    #    steps.append(distance-178)
    '''
    //位置采集代码
    var slide_location=new Array();
    document.getElementById('tcaptcha_drag_button').addEventListener('mousemove',function(e){
        slide_location.push(e.x);
    });
    
    //采集完毕后计算位移
    var track=new Array();
    var current_location =48;
    for(var i=10;i<slide_location.length;i+=5){
         track.push(slide_location[i]-current_location);
         current_location=slide_location[i];
    }
    track
    '''
    action = ActionChains(browser)
    #按住滑块不放
    action.click_and_hold(slide).perform()
    print(distance)
    print(steps)
    #根据轨迹执行滑动动作
    for step in steps:
        action.move_by_offset(xoffset=step, yoffset=random.random).perform()
        print(step,slide.location['x'])
        #新建ActionChains对象防止累加位移
        action = ActionChains(browser)
    time.sleep(random.random()+0.5)
    #释放滑块
    action.release().perform()

    #等待出现知乎首页
    WebDriverWait(browser,5).until(EC.presence_of_element_located((By.ID,'zhihu')))

    return 'success'

def get_distance():
    '''
    把图片转换成灰度图后调用OpenCV进行匹配
    '''
    #读取彩色模版与目标图片
    template_color = cv2.imread('template_color.jpeg', 0)
    target_color = cv2.imread('target_color.jpeg', 0)
    #把彩色图片转换为黑白图片
    cv2.imwrite('template_plain.jpg', template_color)
    cv2.imwrite('target_plain.jpg', target_color)
    #反转黑白目标图片
    target_plain = cv2.imread('target_plain.jpg')
    target_plain = cv2.cvtColor(target_plain, cv2.COLOR_BGR2GRAY)
    target_plain = abs(255 - target_plain)
    cv2.imwrite('target_plain.jpg', target_plain)
    #调用OpenCV进行匹配
    template_plain = cv2.imread('template_plain.jpg')
    target_plain = cv2.imread('target_plain.jpg')
    result = cv2.matchTemplate(target_plain, template_plain, cv2.TM_CCOEFF_NORMED)
    #读取横向距离以及模版长度
    distance_x = np.unravel_index(result.argmax(), result.shape)[1]

    #返回结果，0.412为原图与网页图片缩放比例
    return (distance_x)*0.412-10

def get_steps(distance):
    steps = []
    current = 0
    mid = distance * 3 / 4
    t = 0.2
    v = 0
    while current < distance:
        if current < mid:
            a = 2
        else:
            a = -3
        v0 = v
        v = v0 + a*t
        move = v0*t + 0.5* a * t * t
        current += move
        steps.append(round(move))
    return steps

