from get_bullet import get_bullet
from search_bv import search_bv, BV_NUM
from make_excelcloud import make_word_cloud
import logging
import os

# 配置日志
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/crawl.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print(f"开始爬取{BV_NUM}个相关视频的BV号...")
        logging.info(f"开始爬取{BV_NUM}个相关视频的BV号")

        bv_list = search_bv(BV_NUM)
        print(f"成功获取{len(bv_list)}个BV号，开始爬取弹幕...")
        logging.info(f"成功获取{len(bv_list)}个BV号")

        bullet_screen_list = get_bullet(bv_list)
        print(f"共爬取到{len(bullet_screen_list)}条弹幕")
        logging.info(f"共爬取到{len(bullet_screen_list)}条弹幕")

        filtered_bullet = make_word_cloud(bullet_screen_list)
        logging.info(f"处理完成，有效弹幕数：{len(filtered_bullet)}")

    except Exception as e:
        print(f"程序出错：{e}")
        logging.error(f"程序出错：{e}", exc_info=True)


if __name__ == '__main__':
    main()
