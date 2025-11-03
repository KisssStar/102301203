from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import openpyxl
import jieba
import re
from bullet_screen import get_bullet_screen
from bv_maker import get_bv, BV_NUM

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
jieba.setLogLevel(jieba.logging.INFO)   # 去除jieba警告


def is_noise(bullet: str) -> bool:
    """
    判断是否为无意义噪声弹幕
    :param bullet: 原始弹幕
    :return: True（噪声）/False（有效）
    """
    # 过滤规则：空内容、纯数字、纯符号、过短内容
    bullet = bullet.strip()
    if len(bullet) < 3:
        return True
    # 纯数字或纯符号
    if re.match(r'^[0-9]+$', bullet) or re.match(r'^[^\w\s]+$', bullet):
        return True
    # 简单重复无意义内容（如666、哈哈哈）
    if re.match(r'^[6哈啊]+$', bullet):
        return True
    return False


def confirm(bullet: str) -> bool:
    """
    确认是否与AI应用相关
    :param bullet: 原始弹幕
    :return: True（相关）/False（不相关）
    """
    keywords = [
        '人工智能', 'AI', '机器学习', '深度学习', '神经网络',
        '自动驾驶', '自然语言处理', '智能', 'ai', '大模型',
        'GPT', 'ChatGPT', '生成式AI', '计算机视觉'
    ]  # 扩展AI相关关键词
    bullet = bullet.lower()
    # 关键词前后非字母，避免匹配单词中间的子串
    pattern = r'(?<![a-zA-Z])(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')(?![a-zA-Z])'
    return bool(re.search(pattern, bullet))


def make_word_cloud(bullet_screen_list: list) -> None:
    """
    将AI应用相关弹幕写入Excel，并生成词云图
    :param bullet_screen_list: 原始弹幕列表
    """
    # 过滤噪声和非AI相关弹幕
    ai_related_bullet = []
    for bullet in bullet_screen_list:
        if not is_noise(bullet) and confirm(bullet):
            # 简单清洗：去除特殊符号和多余空格
            cleaned = re.sub(r'[^\w\s]', ' ', bullet)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            ai_related_bullet.append(cleaned)
    
    if not ai_related_bullet:
        print("未找到相关AI应用弹幕")
        return
    
    # 统计前8高频弹幕
    top8 = Counter(ai_related_bullet).most_common(8)
    print("排名前8的AI相关弹幕：")
    for item in top8:
        print(f"{item[0]}: {item[1]}次")
    
    # 写入Excel
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "AI Related Bullet-Screen"
    sheet.append(["弹幕内容", "出现次数"])
    for item in top8:
        sheet.append([item[0], item[1]])
    # 补充统计信息
    sheet.append([])
    sheet.append(["总有效弹幕数", len(ai_related_bullet)])
    sheet.append(["不重复弹幕数", len(set(ai_related_bullet))])
    wb.save('ai_bullet_screen示例.xlsx')
    print("数据已写入Excel")
    
    # 生成词云图（保留原始风格，优化显示）
    text = ' '.join(ai_related_bullet)
    cut_text = ' '.join(jieba.cut(text))  # 中文分词
    
    # 词云配置（保留原始参数结构，优化字体和显示）
    wordcloud = WordCloud(
        font_path='C:/Windows/Fonts/simhei.ttf',  # 替换为系统存在的中文字体
        width=800,
        height=400,
        background_color='white',
        colormap='cool',  # 保留原始配色
        max_words=200,    # 最多显示200个词
        prefer_horizontal=0.9  # 优先水平显示
    ).generate(cut_text)
    
    # 显示并保存词云图
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('ai_bullet_wordcloud.png', dpi=300, bbox_inches='tight')  # 保存图片
    plt.show()


if __name__ == '__main__':
    bv_list = get_bv(BV_NUM)
    bullet_screen_list = get_bullet_screen(bv_list)
    make_word_cloud(bullet_screen_list)
