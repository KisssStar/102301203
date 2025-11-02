# 主程序：一键执行爬取、分析、可视化
import asyncio
from bilibili_scraper import scrape_bilibili
from data_analysis import analyze_danmaku
from visualization import generate_wordcloud, plot_bar_chart

async def main():
    print("开始爬取B站弹幕数据...")
    results = await scrape_bilibili()
    danmaku_list = [d for r in results for d in r.get("danmaku", [])]

    print(f"共获取弹幕数量: {len(danmaku_list)} 条")
    df = analyze_danmaku(danmaku_list)
    print("分析结果：")
    print(df)

    print("生成可视化...")
    generate_wordcloud(danmaku_list)
    plot_bar_chart(danmaku_list)
    print("所有结果已保存在 output 文件夹。")

if __name__ == "__main__":
    asyncio.run(main())
