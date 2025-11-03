from re import search

import requests
import re
import time
import random

# 配置参数
BV_NUM = 300  # 需要爬取的视频数量
# 扩展搜索关键词，提高相关视频命中率
Search_Content = "大语言模型 大模型 LLM GPT ChatGPT 文心一言 讯飞星火 通义千问"
MAX_RETRY = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟基础时间（秒）

# 请求头信息，模拟浏览器行为
header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "referer": "https://search.bilibili.com/all?"
}


def search_bv(num):
    """
    爬取指定数量的相关视频BV号

    参数：
        num: 需要获取的BV号数量

    返回：
        bv_list: 去重后的BV号集合
    """
    bv_list = set()  # 使用集合实现自动去重
    page = 1  # 起始页码
    retry_count = 0

    while len(bv_list) < num:
        # 构建搜索页面URL
        main_page_url = f"https://search.bilibili.com/all?keyword={Search_Content}&page={page}"
        try:
            resp = requests.get(main_page_url, headers=header, timeout=10)
            resp.raise_for_status()
            retry_count = 0  # 重置重试计数
        except requests.exceptions.RequestException as e:
            print(f"页面请求失败：{e}，正在重试...")
            retry_count += 1
            if retry_count >= MAX_RETRY:
                print(f"已达到最大重试次数，无法获取更多BV号")
                break
            time.sleep(RETRY_DELAY * retry_count)  # 指数退避
            continue

        # 正则匹配页面中的BV号
        pattern = re.compile(r'aid:.*?bvid:"(?P<bvs>.*?)",')
        matches = pattern.finditer(resp.text)

        # 提取并添加BV号
        new_bvs = 0
        for match in matches:
            bv = match.group("bvs")
            if bv not in bv_list:
                bv_list.add(bv)
                new_bvs += 1
                # 达到目标数量则返回
                if len(bv_list) >= num:
                    print(f"成功获取{len(bv_list)}个BV号")
                    return bv_list

        if new_bvs == 0:
            print(f"第{page}页未找到新的BV号，可能已达搜索上限")
            break

        # 随机延迟避免反爬，翻页继续爬取
        page += 1
        time.sleep(random.uniform(1, 3))  # 随机延迟1-3秒

    return bv_list


if __name__ == '__main__':
    bv_list = search(BV_NUM)
    print(f"获取到{len(bv_list)}个BV号：{bv_list}")
