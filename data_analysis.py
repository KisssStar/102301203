# data_analysis.py
# 弹幕数据分析模块
import re
from collections import Counter, defaultdict
import pandas as pd
from config import CASE_KEYWORDS, OUTPUT_DIR

def clean_text(text):
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def analyze_danmaku(danmaku_list):
    case_counts = Counter()
    case_examples = defaultdict(list)

    for msg in danmaku_list:
        text = clean_text(str(msg))
        for case, kws in CASE_KEYWORDS.items():
            if any(kw in text for kw in kws):
                case_counts[case] += 1
                if len(case_examples[case]) < 5:
                    case_examples[case].append(msg)
                break

    top8 = case_counts.most_common(8)
    df = pd.DataFrame(top8, columns=["应用场景", "弹幕数量"])
    df["示例弹幕"] = [ " | ".join(case_examples[c][:3]) for c,_ in top8 ]
    out_path = f"{OUTPUT_DIR}/llm_danmaku.xlsx"
    df.to_excel(out_path, index=False)
    return df
