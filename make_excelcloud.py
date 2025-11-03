from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import openpyxl
import jieba
import re

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
jieba.setLogLevel(jieba.logging.INFO)


def is_noise(bullet: str) -> bool:
    """判断弹幕是否为无意义的噪声信息"""
    noise_patterns = [
        r'^\s*$', r'^6+$', r'^[0-9]+$', r'^[^\w\s]+$',
        r'^[赞好强牛6666]+$', r'^[啊啊啊哈哈哈哈嘿嘿嘿]+$',
        r'^[一二三四五六七八九零]+$', r'^[是的对的没错]+$',
        r'^[？?！!。,.，、]+$', r'^[观看中路过飘过]+$',
        r'^[视频不错很好]+$',
    ]

    bullet = bullet.strip()
    if len(bullet) < 3:
        return True

    for pattern in noise_patterns:
        if re.match(pattern, bullet):
            return True

    return False


def confirm(bullet: str) -> bool:
    """判断弹幕是否与大语言模型相关"""
    keywords = [
        '大语言模型', '大模型', 'LLM', 'llm',
        'GPT', 'gpt', '文心一言', 'ERNIE', 'ernie',
        '讯飞星火', '通义千问', '智谱AI', 'Claude', 'claude'
    ]
    # 统一转为小写匹配，避免大小写遗漏
    pattern = r'(?<![a-zA-Z])(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')(?![a-zA-Z])'
    return bool(re.search(pattern, bullet.lower()))


def make_word_cloud(bullet_screen_list: list) -> list:
    """处理弹幕数据，仅统计前8名（Excel无排名列），词云大小写视为同一词"""
    # 过滤噪声和不相关弹幕
    filtered_bullet = []
    for bullet in bullet_screen_list:
        if not is_noise(bullet) and confirm(bullet):
            cleaned = re.sub(r'[^\w\s]', ' ', bullet)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            filtered_bullet.append(cleaned)

    if not filtered_bullet:
        raise ValueError("没有找到相关的弹幕内容")

    # 仅获取前8名弹幕统计
    top8_bullet = Counter(filtered_bullet).most_common(8)
    print("排名前8的完整弹幕及其出现次数：")
    for item in top8_bullet:
        print(f"{item[0]}: {item[1]}次")

    # 生成Excel（移除排名列，仅保留弹幕内容和出现次数）
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "大语言模型弹幕前8统计"
    sheet.append(["弹幕内容", "出现次数"])  # 移除排名列
    for item in top8_bullet:  # 直接遍历前8名，不添加排名
        sheet.append([item[0], item[1]])
    wb.save('大语言模型弹幕前8统计.xlsx')
    print("前8名弹幕数据已写入Excel（无排名列）")

    # 生成词云
    all_words = []
    for bullet, _ in top8_bullet:
        words = jieba.cut(bullet)
        for word in words:
            # 大小写归一化：转为小写统计
            lower_word = word.lower()
            if len(lower_word) >= 2 and not re.match(r'^\d+$', lower_word):
                all_words.append(lower_word)

    if not all_words:
        print("无有效词语生成词云")
        return filtered_bullet

    # 统计归一化后的词频
    word_counts = Counter(all_words)
    # 保留原始词语的大小写形式用于显示
    word_display_map = {}
    for bullet, _ in top8_bullet:
        for word in jieba.cut(bullet):
            lower_word = word.lower()
            if lower_word in word_counts and lower_word not in word_display_map:
                word_display_map[lower_word] = word  # 记录首次出现的原始形式

    # 生成词云数据
    word_freq = {
        word_display_map.get(lower_word, lower_word): count / max(word_counts.values())
        for lower_word, count in word_counts.items()
    }

    # 生成词云图
    wordcloud = WordCloud(
        font_path='C:/Windows/Fonts/simhei.ttf',
        width=1200, height=600,
        background_color='white',
        max_words=50
    ).generate_from_frequencies(word_freq)

    plt.figure(figsize=(15, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('大语言模型弹幕前8词云图.png', dpi=300)
    print("基于前8名弹幕的词云图已保存")
    plt.close()

    return filtered_bullet
