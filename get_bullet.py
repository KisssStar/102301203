# bilibili_scraper_stealth.py
# B站弹幕爬虫 - 隐蔽版本
import requests
import xml.etree.ElementTree as ET
import time
import random
import json
from config import SEARCH_KEYWORDS

# 使用浏览器真实的User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# 使用B站移动端API（限制可能更宽松）
MOBILE_API = "https://api.bilibili.com/x/web-interface/search/type"
# 直接通过网页获取视频信息
VIDEO_PAGE_API = "https://api.bilibili.com/x/web-interface/view"
# 弹幕API
DANMAKU_API = "https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"


def get_real_bvid_from_url(url):
    """从视频URL中提取BVID"""
    if "bilibili.com/video/" in url:
        parts = url.split("/video/")
        if len(parts) > 1:
            bvid = parts[1].split("?")[0]
            if bvid.startswith("BV"):
                return bvid
    return None


def manual_search(keyword):
    """手动搜索 - 返回一些热门视频的BVID"""
    # 这些是一些热门视频的BVID，你可以替换成你感兴趣的视频
    popular_videos = [
        "BV1GJ411x7h7",  # 测试用视频1
        "BV1UW411x7pK",  # 测试用视频2
        "BV1Js411o76u",  # 测试用视频3
    ]

    print(f"手动搜索: {keyword}")
    print(f"返回预设的热门视频BVID列表")
    return popular_videos


def get_video_info_direct(bvid):
    """直接获取视频信息（不通过搜索API）"""
    url = f"https://www.bilibili.com/video/{bvid}"

    headers = HEADERS.copy()
    headers["Referer"] = f"https://www.bilibili.com/video/{bvid}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # 从HTML中提取初始数据
            html_content = response.text
            if "window.__INITIAL_STATE__" in html_content:
                start = html_content.find("window.__INITIAL_STATE__") + 25
                end = html_content.find("</script>", start)
                if start > 25 and end > start:
                    json_str = html_content[start:end].split("};")[0] + "}"
                    data = json.loads(json_str)

                    # 提取视频信息
                    video_data = data.get("videoData", {})
                    cid = video_data.get("cid")
                    title = video_data.get("title", "未知标题")
                    owner = video_data.get("owner", {})
                    author = owner.get("name", "未知作者")

                    return {
                        "bvid": bvid,
                        "cid": cid,
                        "title": title,
                        "author": author
                    }
    except Exception as e:
        print(f"获取视频页面失败: {e}")

    return None


def fetch_danmaku_slow(cid):
    """慢速获取弹幕"""
    url = DANMAKU_API.format(cid=cid)

    headers = HEADERS.copy()
    headers["Referer"] = "https://www.bilibili.com/"

    print(f"等待10-20秒后获取弹幕...")
    time.sleep(random.uniform(10, 20))

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.content)
                danmaku_list = [d.text for d in root.findall("d") if d.text]
                print(f"获取到 {len(danmaku_list)} 条弹幕")
                return danmaku_list
            except ET.ParseError:
                print("解析弹幕XML失败")
                return []
        else:
            print(f"获取弹幕失败，状态码: {response.status_code}")
            return []
    except Exception as e:
        print(f"获取弹幕异常: {e}")
        return []


def scrape_from_predefined_bvids(bvid_list, max_videos=3):
    """从预定义的BVID列表爬取"""
    results = []

    for bvid in bvid_list[:max_videos]:
        print(f"\n处理视频: {bvid}")

        # 获取视频信息
        video_info = get_video_info_direct(bvid)
        if not video_info:
            print(f"无法获取视频信息: {bvid}")
            continue

        print(f"标题: {video_info['title']}")
        print(f"作者: {video_info['author']}")

        # 获取弹幕
        danmaku = fetch_danmaku_slow(video_info['cid'])

        results.append({
            "bvid": bvid,
            "title": video_info['title'],
            "author": video_info['author'],
            "cid": video_info['cid'],
            "danmaku": danmaku,
            "danmaku_count": len(danmaku)
        })

        if len(results) >= max_videos:
            break

        # 视频间长时间等待
        if len(results) < max_videos:
            wait_time = random.uniform(30, 60)
            print(f"等待 {wait_time:.1f} 秒后处理下一个视频...")
            time.sleep(wait_time)

    return results


def scrape_with_proxy(bvid_list, max_videos=3):
    """使用代理IP爬取（如果需要）"""
    # 如果需要使用代理，在这里配置
    # proxies = {
    #     "http": "http://your_proxy:port",
    #     "https": "https://your_proxy:port"
    # }
    proxies = None

    results = []

    for bvid in bvid_list[:max_videos]:
        print(f"通过代理处理: {bvid}")

        try:
            video_info = get_video_info_direct(bvid)
            if video_info:
                danmaku = fetch_danmaku_slow(video_info['cid'])

                results.append({
                    "bvid": bvid,
                    "title": video_info['title'],
                    "author": video_info['author'],
                    "danmaku": danmaku,
                    "danmaku_count": len(danmaku)
                })

                time.sleep(random.uniform(20, 40))
        except Exception as e:
            print(f"代理模式处理失败: {e}")

    return results


def main():
    """主函数"""
    print("=== B站弹幕爬虫 - 隐蔽版本 ===\n")

    # 使用预设的BVID列表
    predefined_bvids = [
        "BV1GJ411x7h7",  # 替换为实际可用的BVID
        "BV1UW411x7pK",
        "BV1Js411o76u",
        "BV1C4411B7cH",
        "BV1px41117bH"
    ]

    print("可用视频BVID列表:")
    for i, bvid in enumerate(predefined_bvids, 1):
        print(f"{i}. {bvid}")

    print("\n选择模式:")
    print("1. 直接爬取（使用预设BVID）")
    print("2. 手动输入BVID")

    choice = input("\n请选择模式 (1 或 2): ").strip()

    if choice == "2":
        custom_bvid = input("请输入视频BVID（以BV开头）: ").strip()
        if custom_bvid.startswith("BV"):
            predefined_bvids = [custom_bvid]
        else:
            print("无效的BVID格式，使用预设列表")

    print("\n开始爬取...")

    try:
        results = scrape_from_predefined_bvids(predefined_bvids, max_videos=3)

        if results:
            print(f"\n=== 爬取完成 ===")
            print(f"成功获取 {len(results)} 个视频的弹幕:")

            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} - {result['author']} - {result['danmaku_count']}条弹幕")

            # 保存结果
            try:
                with open("bilibili_danmaku_results.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print("\n结果已保存到: bilibili_danmaku_results.json")

                # 也保存为文本文件便于查看
                with open("bilibili_danmaku.txt", "w", encoding="utf-8") as f:
                    for result in results:
                        f.write(f"=== {result['title']} ===\n")
                        f.write(f"作者: {result['author']}\n")
                        f.write(f"弹幕数量: {result['danmaku_count']}\n")
                        f.write("弹幕内容:\n")
                        for danmaku in result['danmaku']:
                            f.write(f"- {danmaku}\n")
                        f.write("\n" + "=" * 50 + "\n\n")
                print("文本格式已保存到: bilibili_danmaku.txt")

            except Exception as e:
                print(f"保存文件失败: {e}")
        else:
            print("\n没有获取到任何数据")

    except Exception as e:
        print(f"爬取过程出错: {e}")
        print("建议:")
        print("1. 更换网络环境（如使用手机热点）")
        print("2. 等待一段时间后再试")
        print("3. 使用代理服务器")


if __name__ == "__main__":
    main()
