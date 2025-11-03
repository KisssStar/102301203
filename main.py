from bullet_screen import get_bullet_screen
from bv_maker import get_bv, BV_NUM
from word_cloud import make_word_cloud

if __name__ == '__main__':
    print(f"开始爬取{BV_NUM}个相关视频的BV号...")
    bv_list = get_bv(BV_NUM)
    print(f"成功获取{len(bv_list)}个BV号，开始爬取弹幕...")
    
    bullet_screen_list = get_bullet_screen(bv_list)
    print(f"共爬取到{len(bullet_screen_list)}条弹幕")
    
    try:
        filtered_bullet = make_word_cloud(bullet_screen_list)
        # 可以在这里添加数据分析代码
    except ValueError as e:
        print(f"处理出错：{e}")
