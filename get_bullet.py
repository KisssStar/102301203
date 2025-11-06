import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import concurrent.futures
import re

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


def get_single_video_danmu(bv, session):
    """获取单个视频的弹幕内容"""
    try:
        # 1. 获取CID
        cid_url = CID_API_TEMPLATE.format(bv=bv)
        resp_cid = session.get(cid_url, timeout=10)
        resp_cid.raise_for_status()
        cid_data = resp_cid.json()
        cid = cid_data["data"][0]["cid"]

        # 2. 获取弹幕XML
        danmu_url = DANMU_API_TEMPLATE.format(cid=cid)
        resp_danmu = session.get(danmu_url, timeout=10)
        resp_danmu.encoding = "utf-8"
        resp_danmu.raise_for_status()

        # 3. 使用正则表达式替代BeautifulSoup解析，性能提升显著
        danmu_texts = []
        danmu_pattern = re.compile(r'<d[^>]*>(.*?)</d>')
        matches = danmu_pattern.findall(resp_danmu.text)

        for match in matches:
            text = match.strip()
            if text:
                danmu_texts.append(text)

        return danmu_texts, bv, None

    except Exception as e:
        return [], bv, str(e)


def get_bullet(bv_list):
    """根据BV号列表爬取对应视频的弹幕内容 - 优化版"""
    bullet_screen_list = []
    session = create_session()

    print(f"开始处理 {len(bv_list)} 个视频的弹幕爬取...")
    start_time = time.time()

    # 使用线程池并发处理多个视频（控制并发数避免被封IP）
    max_workers = min(5, len(bv_list))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_bv = {
            executor.submit(get_single_video_danmu, bv, session): bv
            for bv in bv_list
        }

        completed_count = 0
        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_bv):
            bv = future_to_bv[future]
            completed_count += 1

            try:
                danmu_texts, result_bv, error = future.result()
                if error:
                    print(f"处理 {bv} 失败: {error}")
                else:
                    bullet_screen_list.extend(danmu_texts)
                    print(f"[{completed_count}/{len(bv_list)}] {bv}: 成功获取 {len(danmu_texts)} 条弹幕")

            except Exception as e:
                print(f"处理 {bv} 时发生异常: {e}")

    session.close()

    total_time = time.time() - start_time
    print(f"爬取完成！总共获取 {len(bullet_screen_list)} 条弹幕")
    print(f"总耗时: {total_time:.2f}秒, 平均每个视频: {total_time / len(bv_list):.2f}秒")

    return bullet_screen_list

