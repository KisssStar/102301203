from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import openpyxl
import jieba
import re
import string

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
jieba.setLogLevel(jieba.logging.INFO)   #去除warning

def is_noise(bullet):
    """判断是否为噪声信息"""
    noise_patterns = [
        r'^\s*$',  # 空字符串
        r'^6+$',   # 666等
        r'^[0-9]+$', # 纯数字
        r'^[^\w\s]+$', # 纯符号
        r'^[赞好强6666]+$', # 简单点赞类
    ]
    bullet = bullet.strip()
    if len(bullet) < 3:
        return True
    for pattern in noise_patterns:
        if re.match(pattern, bullet):
            return True
    return False

def confirm(bullet):
    """确认是否与大语言模型相关"""
    keywords = ['大语言模型', '大模型', 'LLM', 'llm']
    bullet = bullet.lower()
    obj = r'(?<![a-zA-Z])(?:' + '|'.join(re.escape(keyword) for keyword in keywords) + r')(?![a-zA-Z])'
    return bool(re.search(obj, bullet))

def make_word_cloud(bullet_screen_list):
    """处理弹幕，写入Excel，并生成词云图"""
    # 过滤噪声和不相关弹幕
    filtered_bullet = []
    for bullet in bullet_screen_list:
        if not is_noise(bullet) and confirm(bullet):
            cleaned = re.sub(r'[^\w\s]', ' ', bullet)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            filtered_bullet.append(cleaned)

    if not filtered_bullet:
        raise ValueError("没有找到相关的弹幕内容")

    # 统计词频并获取前8的弹幕
    top8 = Counter(filtered_bullet).most_common(8)
    print("排名前8的弹幕及其出现次数：")
    for item in top8:
        print(f"{item[0]}: {item[1]}次")

    # ------------------- Excel生成部分--------------------------------
    # 写入Excel
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "大语言模型相关弹幕统计"
    sheet.append(["弹幕内容", "出现次数"])
    for item in top8:
        sheet.append([item[0], item[1]])
    # 添加总览信息
    sheet.append([])
    sheet.append(["总弹幕数", len(filtered_bullet)])
    sheet.append(["不重复弹幕数", len(set(filtered_bullet))])
    wb.save('大语言模型弹幕统计.xlsx')
    print("数据已成功写入Excel文件")
    # -----------------------------------------------------------------

    # 生成词云图（修复字体问题）
     text = ' '.join(filtered_bullet)
    cut_text = ' '.join(jieba.cut(text))
    if not cut_text.strip():
        raise ValueError("分词后无有效内容，无法生成词云")

    # 移除 contour 相关参数（可能触发 deepcopy）
    wordcloud = WordCloud(
        font_path='C:/Windows/Fonts/simhei.ttf',  # 确保字体存在
        width=1200,
        height=600,
        background_color='white',
        colormap='viridis',
        max_words=200
        # 去掉 contour_width 和 contour_color，减少复杂计算
    ).generate(cut_text)

    # 简化绘图逻辑
    plt.figure(figsize=(15, 8))
    plt.imshow(wordcloud)
    plt.axis('off')  # 关闭坐标轴
    plt.savefig('大语言模型弹幕词云图.png', dpi=300)  # 直接保存
    print("词云图已保存为PNG文件")
    plt.close()  # 关闭绘图窗口，避免显示环节的问题

    return filtered_bullet
