import requests
import xml.etree.ElementTree as ET
import time
import random
from config import SEARCH_KEYWORDS

# 简化的请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
VIDEO_INFO_API = "https://api.bilibili.com/x/web-interface/view"
DANMAKU_API = "https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"

def fetch_json(url, params=None, retry=2):
    """获取JSON数据"""
    for attempt in range(retry):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"请求失败，状态码: {response.status_code}")
                if response.status_code == 412:
                    print("被B站反爬机制拦截，请稍后重试或更换网络环境")
                    return None
        except Exception as e:
            print(f"请求异常: {e}")
        
        if attempt < retry - 1:
            time.sleep(random.uniform(2, 5))
    
    return None

def fetch_text(url, params=None, retry=2):
    """获取文本数据"""
    for attempt in range(retry):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"请求异常: {e}")
        
        if attempt < retry - 1:
            time.sleep(random.uniform(2, 5))
    
    return None

def search_videos(keyword, page=1):
    """搜索视频"""
    params = {
        "search_type": "video", 
        "keyword": keyword, 
        "page": page,
        "page_size": 20
    }
    return fetch_json(SEARCH_API, params=params)

def get_video_cid(bvid):
    """获取视频CID"""
    params = {"bvid": bvid}
    data = fetch_json(VIDEO_INFO_API, params=params)
    
    if not data or data.get("code") != 0:
        print(f"获取视频信息失败: {bvid}")
        return None
        
    video_data = data.get("data", {})
    cid = video_data.get("cid")
    
    return cid

def fetch_danmaku_by_cid(cid):
    """根据CID获取弹幕"""
    url = DANMAKU_API.format(cid=cid)
    xml_text = fetch_text(url)
    
    if not xml_text:
        return []
        
    try:
        root = ET.fromstring(xml_text)
        danmaku_list = [d.text for d in root.findall("d") if d.text]
        print(f"获取到 {len(danmaku_list)} 条弹幕")
        return danmaku_list
    except ET.ParseError as e:
        print(f"解析弹幕XML失败: {e}")
        return []

def scrape_bilibili_simple(keywords=SEARCH_KEYWORDS, max_videos=10):
    """简化版爬虫 - 使用同步请求"""
    results = []
    
    for kw in keywords:
        print(f"搜索关键词: {kw}")
        
        # 只搜索第一页
        search_data = search_videos(kw, page=1)
        if not search_data:
            print(f"搜索失败: {kw}")
            continue
            
        videos = search_data.get("data", {}).get("result", [])
        if not videos:
            print(f"没有找到相关视频: {kw}")
            continue
            
        print(f"找到 {len(videos)} 个视频，开始处理前{min(3, len(videos))}个...")
        
        # 只处理前3个视频
        for video in videos[:3]:
            if len(results) >= max_videos:
                break
                
            bvid = video.get("bvid")
            title = video.get("title", "未知标题")
            
            if not bvid:
                continue
                
            print(f"处理视频: {title}")
            
            # 较长的延迟避免被封
            time.sleep(random.uniform(5, 10))
            
            cid = get_video_cid(bvid)
            if not cid:
                continue
                
            # 获取弹幕前的延迟
            time.sleep(random.uniform(3, 6))
            
            danmaku = fetch_danmaku_by_cid(cid)
            
            results.append({
                "bvid": bvid,
                "title": title,
                "author": video.get("author", ""),
                "cid": cid,
                "danmaku": danmaku,
                "danmaku_count": len(danmaku)
            })
            
            print(f"完成: {title} - {len(danmaku)}条弹幕")
            
            # 视频间较长延迟
            time.sleep(random.uniform(8, 15))
    
    print(f"爬取完成! 总共获取 {len(results)} 个视频")
    return results
