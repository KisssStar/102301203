import re
import requests
from bs4 import BeautifulSoup
from search_bv import get_bv, BV_NUM


"https://api.bilibili.com/x/v1/dm/list.so?oid="  # 获取b站弹幕api,需要提供bv号获取cid
"https://comment.bilibili.com/{cid}.xml"  # 提供bv号获取cid


header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",  #UA
    "referer": "https://www.bilibili.com/"  #溯源 反反爬
}

def get_bullet_screen(bv_list):
    """
    通过bv号获取视频cid，进一步获取弹幕内容
    :param bv_list:
    :return: bullet_screen_list
    """
    bullet_screen_list = []     #存放弹幕
    for bv in bv_list:
        cid_url = f"https://api.bilibili.com/x/player/pagelist?bvid={bv}&jsonp=jsonp"
        resp1 = requests.get(cid_url, headers=header)
        # print(resp1.json())
        dict = resp1.json()
        cid = dict["data"][0]["cid"]    #获取字典中的cid
        api_url = f"https://comment.bilibili.com/{cid}.xml"
        resp2 = requests.get(api_url, headers=header)
        resp2.encoding = "utf-8"    #设置对应的字符集
        # print(resp2.text)
        xml = BeautifulSoup(resp2.text, "xml")  #使用xml需要安装lxml库
        ds = xml.find_all("d")  #爬取所有的弹幕
        for d in ds:
            bullet_screen_list.append(d.text)   #将弹幕写入列表
        print(f"爬取{bv}的弹幕成功")
    return bullet_screen_list


if __name__ == '__main__':
    bv_list = get_bv(BV_NUM)
    print(bv_list)
    print(get_bullet_screen(bv_list))
