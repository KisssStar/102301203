import requests
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
    """
    创建带有重试机制的请求会话
    
    Returns:
        requests.Session: 配置好的会话对象
    """
    session = requests.Session()
    retry = Retry(
        total=3,  # 最大重试次数
        backoff_factor=1,  # 重试间隔因子
        status_forcelist=[429, 500, 502, 503, 504]  # 需要重试的状态码
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update(HEADER)
    return session


def get_single_video_danmu(bv, session):
    """
    获取单个视频的弹幕内容
    
    Args:
        bv (str): 视频BV号
        session: 请求会话对象
        
    Returns:
        tuple: (弹幕列表, BV号, 错误信息)
    """
    try:
        # 1. 获取CID
        cid_url = CID_API_TEMPLATE.format(bv=bv)
        resp_cid = session.get(cid_url, timeout=10)
        resp_cid.raise_for_status()  # 检查请求是否成功
        cid_data = resp_cid.json()
        cid = cid_data["data"][0]["cid"]

        # 2. 获取弹幕XML
        danmu_url = DANMU_API_TEMPLATE.format(cid=cid)
        resp_danmu = session.get(danmu_url, timeout=10)
        resp_danmu.encoding = "utf-8"  # 设置编码为UTF-8
        resp_danmu.raise_for_status()

        # 3. 匹配XML中的弹幕
        danmu_texts = []
        danmu_pattern = re.compile(r'<d[^>]*>(.*?)</d>')  # 匹配弹幕内容的正则表达式
        matches = danmu_pattern.findall(resp_danmu.text)

         # 遍历所有匹配结果，提取并清理弹幕文本
        for match in matches: 
            text = match.strip()
            if text:
                danmu_texts.append(text)

        return danmu_texts, bv, None

    except Exception as e:
        return [], bv, str(e)


def get_bullet(bv_list):
    """
    根据BV号列表爬取对应视频的弹幕内容
    
    Args:
        bv_list (list): BV号列表
        
    Returns:
        list: 所有视频的弹幕内容列表
    """
    bullet_screen_list = []
    session = create_session()

    print(f"开始处理 {len(bv_list)} 个视频的弹幕爬取...")
    start_time = time.time()

    # 使用线程池并发处理多个视频（控制并发数避免被封IP）
    max_workers = min(5, len(bv_list))  # 最大并发数为5或视频数量，取较小值

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
    print(f"爬取完成！总共获取 {len(bullet_screen_list)} 条弹幕，耗时 {total_time:.2f} 秒")

    return bullet_screen_list


if __name__ == '__main__':
    # 测试代码
    from search_bv import search_bv
    
    # 获取测试用的BV号列表
    test_bv_list = search_bv(5)
    print(f"测试用BV号：{test_bv_list}")
    
    # 爬取弹幕
    test_danmu = get_bullet(test_bv_list)
    print(f"测试爬取到{len(test_danmu)}条弹幕（前3条预览）：{test_danmu[:3]}")
