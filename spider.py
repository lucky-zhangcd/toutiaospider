from urllib.parse import urlencode
from multiprocessing import Pool
from hashlib import md5
import requests
import json
import os
import re

"""
根据每一个AJAX分页的url，返回每个分页里的20个相册的链接
"""
def parse_ajax(ajax_url):
    headers = {
        "authority": "www.toutiao.com",
        "method": "GET",
        "accept-encoding": "gzip, deflate, br",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
    }
    res = requests.get(ajax_url, headers=headers)

    # loads()方法将JSON文本字符串转为JSON对象，通过dumps()方法将JSON对象转为文本字符串
    data = json.loads(res.text)
    street_naps_url_list = []
    for item in data['data']:
        if item.get('group_id'):
            street_naps_url_list.append("https://www.toutiao.com/a" + item.get('group_id'))
        else:
            print("not a street snap url......")
    return street_naps_url_list

"""
根据每个相册的链接，获取相册里所有图片的地址
返回list，每个数据为dict，包含图片地址和图片主题
"""
def get_gallery(street_snaps_url):
    headers = {
        "authority": "www.toutiao.com",
        "method": "GET",
        "accept-encoding": "gzip, deflate, br",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
    }

    try:
        response = requests.get(street_snaps_url, headers=headers)
        html = response.text

        # 获取主题
        title = re.search("title: '(.*?)'", html)
        title = title.group(1)

        gallery = []

        # 从相册中取得每张照片的地址
        # 相册中每张照片的地址在JavaScript的gallery中，用正则表达式取出来
        address = re.search('parse\("(.*?)"\)', html)
        address = address.group(1)
        # 为什么要用4个\，我也不懂，只是因为没报错并且结果也对
        address = re.sub('\\\\', '', address)
        address = json.loads(address)
        sub_images = address['sub_images']
        for single_image in sub_images:
            aImage = single_image['url']
            item = {}
            item['title'] = title
            item['image'] = aImage
            gallery.append(item)
        return gallery
    except Exception as e:
        print("Fail to get images url")

def save_image(item):
    file_path = 'street_snaps' + os.path.sep + item.get('title')
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    try:
        response = requests.get(item.get('image'))
        if response.status_code == 200:
            img_path = file_path + os.path.sep + '{0}.{1}'.format(md5(response.content).hexdigest(), 'jpg')
            if not os.path.exists(img_path):
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                print('Downloaded image path is {}'.format(img_path))
            else:
                print('Already Downloaded {}'.format(img_path))
    except Exception as e:
        print('Failed to Save Image due to {}'.format(e))


def main(offset):
    params = {
        "offset": offset,
        "format": "json",
        "keyword": "街拍",
        "autoload": "true",
        "count": 20,
        "cur_tab": 3,
        "from": "gallery"
    }
    url = "https://www.toutiao.com/search_content/?" + urlencode(params)
    # 根据每一页的链接，获取每一页里面的20个相册的链接
    # 根据每个相册的链接，获取每个相册里图片的地址
    # 根据每张图片的地址，保存图片
    for street_snaps_url in parse_ajax(url):
        for aImage in get_gallery(street_snaps_url):
            save_image(aImage)


OFFSET_START = 0
OFFSET_END = 5

if __name__ == "__main__":
    pool = Pool()
    offset_list = [x * 20 for x in range(OFFSET_START, OFFSET_END + 1)]
    pool.map(main, offset_list)
    pool.close()
    pool.join()
