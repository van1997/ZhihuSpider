import re

'''
从字符串中提取数字
'''
def extract_num(text):
    num_match = re.match('.*?([\d,]+).*',text)
    if num_match:
        num = int(num_match.group(1).replace(',',''))
    else:
        num = 0

    return num

