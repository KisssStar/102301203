from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import openpyxl
import jieba
import re
import numpy as np

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
jieba.setLogLevel(jieba.logging.INFO)


# ------------------- 核心：定义观点维度的关键词词典 -------------------
VIEW_DIMENSIONS = {
    # 1. 应用成本相关（用户对成本的看法）
    "应用成本": [
        "成本", "价格", "免费", "付费", "昂贵", "廉价", "费用",
        "性价比", "经济", "成本高", "成本低", "收费","便宜","划算"
    ],
    # 2. 潜在应用领域（用户提到的适用场景）
    "潜在领域": [
        "教育", "医疗", "办公", "写作", "编程", "翻译", "客服",
        "创作", "设计", "学习", "科研", "教育领域", "工作", "生活",
        "游戏", "娱乐", "聊天", "对话", "写作", "创作", "文案", "小说"
    ],
    # 3. 不利影响（用户担忧的问题）
    "不利影响": [
        "隐私", "安全", "依赖", "失业", "错误", "偏见", "虚假",
        "滥用", "风险", "漏洞", "数据泄露", "伦理", "取代",
        "失业", "危险", "可怕", "担心", "反对", "不好"
    ],
    # 4. 其他正面看法（补充维度）
    "正面评价": [
        "高效", "方便", "强大", "有用", "创新", "进步", "智能",
        "好用", "厉害", "强大", "惊喜", "支持", "进步", "未来"
    ]
}

# 构建维度-关键词映射（用于快速匹配）
dim_keyword_map = {}
for dim, keywords in VIEW_DIMENSIONS.items():
    for kw in keywords:
        dim_keyword_map[kw.lower()] = dim  # 大小写不敏感


def is_noise(bullet: str) -> bool:
    """过滤无意义弹幕"""
    noise_patterns = [
        r'^\s*$', r'^6+$', r'^[0-9]+$', r'^[^\w\s]+$',
        r'^[赞好强牛6666]+$', r'^[啊啊啊哈哈哈哈嘿嘿嘿]+$',
        r'^[是的对的没错]+$', r'^[观看中路过飘过]+$',
        "点赞", "投币", "收藏", "关注", "弹幕", "打卡", "签到", "来了", "前排"
    ]
    bullet = bullet.strip()
    return len(bullet) < 3 or any(re.match(p, bullet) for p in noise_patterns)


def confirm(bullet: str) -> bool:
    """确认弹幕与大语言模型相关"""
    llm_keywords = ['大语言模型', 'LLM', 'gpt', 'chatgpt', '文心一言', '通义千问',
                    "大模型", "llm", "Large Language Model", "large language model",
                    "语言模型", "大语言", "LLMs", "对话模型", "语言大模型"
                    ]
    return any(kw in bullet.lower() for kw in llm_keywords)


def extract_view_terms(bullet: str) -> dict:
    """从单条弹幕中提取各观点维度的关键词/短语"""
    bullet_lower = bullet.lower()
    # 优先提取2-4字短语（更能表达观点）
    phrases = [p for p in jieba.cut(bullet) if 2 <= len(p) <= 4 and not re.match(r'^\d+$', p)]
    # 按维度分类
    dim_terms = defaultdict(list)
    for phrase in phrases:
        # 匹配维度关键词（短语包含关键词则归为该维度）
        for kw, dim in dim_keyword_map.items():
            if kw in phrase:
                dim_terms[dim].append(phrase)
                break  # 只匹配第一个维度
    return dim_terms


def make_word_cloud(bullet_screen_list: list) -> dict:
    """生成按观点维度分类的词云，辅助分析用户看法"""
    # 过滤有效弹幕
    filtered_bullet = [
        re.sub(r'[^\w\s]', ' ', b).strip()
        for b in bullet_screen_list
        if not is_noise(b) and confirm(b)
    ]
    if not filtered_bullet:
        raise ValueError("无相关弹幕")

    # ------------------- 按观点维度统计关键词 -------------------
    dim_counter = defaultdict(Counter)  # {维度: {关键词: 次数}}
    for bullet in filtered_bullet:
        dim_terms = extract_view_terms(bullet)
        for dim, terms in dim_terms.items():
            dim_counter[dim].update(terms)

    # 合并所有维度的词频，用于总词云
    all_terms = []
    for dim, counter in dim_counter.items():
        all_terms.extend([term for term, cnt in counter.most_common(30) for _ in range(cnt)])
    total_counter = Counter(all_terms)

    # ------------------- 生成带维度颜色的词云图 -------------------
    # 定义维度颜色（蓝=成本，绿=领域，红=不利，黄=正面）
    dim_colors = {
        "应用成本": "#1f77b4",
        "潜在领域": "#2ca02c",
        "不利影响": "#ff7f0e",
        "正面评价": "#d62728"
    }

    # 生成颜色映射函数（根据词所属维度分配颜色）
    def color_func(word, font_size, position, orientation, font_path, random_state):
        # 查找词所属的维度
        for dim, counter in dim_counter.items():
            if word in counter:
                return dim_colors[dim]
        return "#888888"  # 未匹配维度的词用灰色

    # 生成词云
    wordcloud = WordCloud(
        font_path='C:/Windows/Fonts/simhei.ttf',
        width=1600, height=800,
        background_color='white',
        max_words=100,
        color_func=color_func,  # 应用维度颜色
        prefer_horizontal=0.9
    ).generate_from_frequencies({k: v/len(total_counter) for k, v in total_counter.items()})

    # 保存词云（带图例说明维度颜色）
    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    # 添加颜色图例
    for i, (dim, color) in enumerate(dim_colors.items()):
        plt.scatter([], [], c=color, label=dim, s=100)
    plt.legend(loc='lower right', fontsize=12)
    plt.savefig('大语言模型用户观点词云.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("带观点维度的词云图已保存")

    # ------------------- 生成Excel统计（按维度分类） -------------------
    wb = openpyxl.Workbook()
    for dim, counter in dim_counter.items():
        sheet = wb.create_sheet(title=dim)
        sheet.append(["关键词/短语", "出现次数"])
        for term, cnt in counter.most_common(10):
            sheet.append([term, cnt])
    # 总览表
    sheet = wb.active
    sheet.title = "各维度总览"
    sheet.append(["观点维度", "高频关键词示例", "总出现次数"])
    for dim, counter in dim_counter.items():
        top_terms = ", ".join([t for t, _ in counter.most_common(3)])
        total = sum(counter.values())
        sheet.append([dim, top_terms, total])
    wb.save('大语言模型用户观点统计.xlsx')
    print("观点维度统计Excel已保存")

    return {dim: dict(counter) for dim, counter in dim_counter.items()}

