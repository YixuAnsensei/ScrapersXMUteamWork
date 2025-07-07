import os

# --- 项目根目录 ---
# 计算项目的绝对路径，确保在任何地方运行脚本时路径都正确
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 数据库配置 ---
DB_NAME = "livability.db"
DB_PATH = os.path.join(BASE_DIR, 'database', DB_NAME)

# --- 爬虫配置 ---
# 将城市信息结构化，方便程序调用和未来扩展
#可添加多个城市
CITIES = {
    "sh": {
        "name": "上海",
        "url": "https://sh.lianjia.com/zufang/",
    },
    "qd": {
        "name": "青岛",
        "url": "https://qd.lianjia.com/zufang/",
    },
    "xm": {  
        "name": "厦门",
        "url": "https://xm.lianjia.com/zufang/", 
    }
}

# --- AI模型配置 ---
AI_MODEL_NAME = "deepseek-chat"

# --- 爬虫User-Agent配置 ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
]