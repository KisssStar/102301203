import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

# 请求头配置
HEADER = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "referer": "https://www.bilibili.com/"
}

# 弹幕相关API模板
CID_API_TEMPLATE = "https://api.bilibili.com/x/player/pagelist?bvid={bv}&jsonp=jsonp"
DANMU_API_TEMPLATE = "https://comment.bilibili.com/{cid}.xml"

# 创建带重试机制的会话
def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update(HEADER)
    return session


def get_bullet(bv_list):
    """根据BV号列表爬取对应视频的弹幕内容"""
    bullet_screen_list = []
    session = create_session()

    for idx, bv in enumerate(bv_list, 1):
        print(f"正在处理第{idx}/{len(bv_list)}个BV号: {bv}")

        # 1. 获取CID
        try:
            cid_url = CID_API_TEMPLATE.format(bv=bv)
            resp_cid = session.get(cid_url, timeout=10)
            resp_cid.raise_for_status()
            cid = resp_cid.json()["data"][0]["cid"]
        except Exception as e:
            print(f"获取CID失败：{e}")
            continue

        # 2. 获取弹幕
        try:
            danmu_url = DANMU_API_TEMPLATE.format(cid=cid)
            resp_danmu = session.get(danmu_url, timeout=10)
            resp_danmu.encoding = "utf-8"
            resp_danmu.raise_for_status()
        except Exception as e:
            print(f"获取弹幕失败：{e}")
            continue

        # 3. 解析弹幕
        try:
            xml_soup = BeautifulSoup(resp_danmu.text, "xml")
            danmu_tags = xml_soup.find_all("d")
            danmu_texts = [tag.text.strip() for tag in danmu_tags if tag.text.strip()]
            bullet_screen_list.extend(danmu_texts)
            print(f"成功获取{len(danmu_texts)}条弹幕")
        except Exception as e:
            print(f"解析弹幕失败：{e}")
            continue

        # 控制爬取速度
        if idx % 10 == 0:
            time.sleep(2)  # 每处理10个视频休息2秒
        else:
            time.sleep(0.5)

    session.close()
    return bullet_screen_list


if __name__ == '__main__':
    from search_bv import get_bv
    test_bv_list = get_bv(5)
    print(f"测试用BV号：{test_bv_list}")
    test_danmu = get_bullet(test_bv_list)
    print(f"测试爬取到{len(test_danmu)}条弹幕（前3条预览）：{test_danmu[:3]}")
