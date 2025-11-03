
import requests
import re   #使用re解析
BV_NUM = 300  # 定义需要的视频数量
Search_Content = "大语言模型 大模型 LLM" 
header = {
"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
"referer":'https://search.bilibili.com/all?'
}
def get_bv(num):
    """
    爬取指定内容，指定视频数量的bv号
    :param num:
    :return: bv_list
    """
    bv_list = set([])   #用set()实现去重
    page = 1
    while (True):
        main_page_url = f"https://search.bilibili.com/all?keyword={Search_Content}&page={page}" #搜索主页面url
        resp = requests.get(main_page_url, headers=header)
        # 提取视频的BVID
        obj = re.compile(r'aid:.*?bvid:"(?P<bvs>.*?)",')
        its = obj.finditer(resp.text)
        for it in its:
            bv_list.add(it.group("bvs"))
            if len(bv_list) >= num:
                return list(bv_list)  # 转换为列表返回，确保顺序性
        page += 1
        # 防止无限循环，设置最大页数限制
        if page > 50:
            break
    return list(bv_list)

if __name__ == '__main__':
    bv_list = get_bv(BV_NUM)
    print(f"获取到{len(bv_list)}个BV号")
    print(bv_list)
