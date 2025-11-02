# bilibili_scraper.py
# B站弹幕爬虫模块（需联网环境运行）
import aiohttp, asyncio, xml.etree.ElementTree as ET
import time
import logging
from config import SEARCH_KEYWORDS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
VIDEO_INFO_API = "https://api.bilibili.com/x/web-interface/view"
DANMAKU_API = "https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

async def fetch_json(session, url, params=None, retry=3):
    """获取JSON数据，带重试机制"""
    for attempt in range(retry):
        try:
            async with session.get(url, params=params, headers=HEADERS, timeout=20) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.warning(f"请求失败，状态码: {r.status}, URL: {url}")
        except Exception as e:
            logger.warning(f"第{attempt+1}次请求失败: {e}")
            if attempt < retry - 1:
                await asyncio.sleep(2)  # 重试前等待
    return None

async def fetch_text(session, url, params=None, retry=3):
    """获取文本数据，带重试机制"""
    for attempt in range(retry):
        try:
            async with session.get(url, params=params, headers=HEADERS, timeout=20) as r:
                if r.status == 200:
                    return await r.text()
                else:
                    logger.warning(f"请求失败，状态码: {r.status}, URL: {url}")
        except Exception as e:
            logger.warning(f"第{attempt+1}次请求失败: {e}")
            if attempt < retry - 1:
                await asyncio.sleep(2)
    return None

async def search_videos(session, keyword, page=1):
    """搜索视频"""
    params = {
        "search_type": "video", 
        "keyword": keyword, 
        "page": page,
        "page_size": 20  # 每页数量
    }
    data = await fetch_json(session, SEARCH_API, params=params)
    if data and data.get("code") == 0:
        return data
    else:
        logger.error(f"搜索失败: {keyword} 第{page}页")
        return None

async def get_video_cid(session, bvid):
    """获取视频CID"""
    params = {"bvid": bvid}
    j = await fetch_json(session, VIDEO_INFO_API, params=params)
    
    if not j or j.get("code") != 0:
        logger.error(f"获取视频信息失败: {bvid}")
        return None
        
    data = j.get("data", {})
    cid = data.get("cid")
    
    # 处理多P视频
    pages = data.get("pages", [])
    if pages and len(pages) > 1:
        cids = [page.get("cid") for page in pages if page.get("cid")]
        return cids if cids else [cid]
    
    return [cid] if cid else None

async def fetch_danmaku_by_cid(session, cid):
    """根据CID获取弹幕"""
    url = DANMAKU_API.format(cid=cid)
    xml_text = await fetch_text(session, url)
    
    if not xml_text:
        return []
        
    try:
        root = ET.fromstring(xml_text)
        danmaku_list = [d.text for d in root.findall("d") if d.text]
        logger.info(f"获取到 {len(danmaku_list)} 条弹幕 (CID: {cid})")
        return danmaku_list
    except ET.ParseError as e:
        logger.error(f"解析弹幕XML失败: {e}")
        return []

async def process_video(session, video_info, results, max_videos):
    """处理单个视频"""
    bvid = video_info.get("bvid")
    if not bvid or bvid in [r['bvid'] for r in results]:
        return False
        
    logger.info(f"处理视频: {video_info.get('title')} (BV: {bvid})")
    
    cids = await get_video_cid(session, bvid)
    if not cids:
        return False
        
    all_danmaku = []
    for cid in cids:
        danmaku = await fetch_danmaku_by_cid(session, cid)
        all_danmaku.extend(danmaku)
        # 分P之间短暂延迟
        await asyncio.sleep(0.5)
    
    results.append({
        "bvid": bvid,
        "title": video_info.get("title", ""),
        "author": video_info.get("author", ""),
        "cids": cids,
        "danmaku": all_danmaku,
        "danmaku_count": len(all_danmaku)
    })
    
    logger.info(f"视频处理完成: {video_info.get('title')} - 弹幕数: {len(all_danmaku)}")
    return True

async def scrape_bilibili(keywords=SEARCH_KEYWORDS, max_videos=360, delay=1.0):
    """主爬虫函数"""
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession(headers=HEADERS) as sess:
        for kw in keywords:
            logger.info(f"开始搜索关键词: {kw}")
            page = 1
            video_count_for_keyword = 0
            
            while len(results) < max_videos:
                logger.info(f"搜索第{page}页...")
                
                search_data = await search_videos(sess, kw, page=page)
                if not search_data:
                    break
                    
                vids = search_data.get("data", {}).get("result", [])
                if not vids:
                    logger.info(f"关键词 '{kw}' 第{page}页无结果")
                    break
                
                # 处理当前页的所有视频
                for video in vids:
                    if len(results) >= max_videos:
                        break
                        
                    success = await process_video(sess, video, results, max_videos)
                    if success:
                        video_count_for_keyword += 1
                        # 请求延迟，避免被封
                        await asyncio.sleep(delay)
                
                page += 1
                
                # 如果当前关键词已经找不到新视频，跳出
                if len(vids) < 20:  # 最后一页
                    break
            
            logger.info(f"关键词 '{kw}' 完成，获取 {video_count_for_keyword} 个视频")
            
            if len(results) >= max_videos:
                break
    
    end_time = time.time()
    total_danmaku = sum(len(r['danmaku']) for r in results)
    
    logger.info(f"爬取完成! 总共获取 {len(results)} 个视频, {total_danmaku} 条弹幕")
    logger.info(f"总耗时: {end_time - start_time:.2f} 秒")
    
    return results

# 可选：单独运行测试
async def main():
    """测试函数"""
    test_keywords = ["测试关键词"]
    results = await scrape_bilibili(keywords=test_keywords, max_videos=5, delay=1.0)
    print(f"测试完成，获取 {len(results)} 个视频")

if __name__ == "__main__":
    asyncio.run(main())
