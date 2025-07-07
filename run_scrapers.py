import os
import logging
from config_in import CITIES, DB_PATH, BASE_DIR
from database.database_manager import DatabaseManager
from scrapers.lianjia_scraper import LianjiaScraper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding='utf-8')
    ]
)

def run_all_scrapers():
    """执行所有爬虫任务并返回状态"""
    logging.info("========= 开始执行所有爬虫任务 =========")
    
    try:
        db_manager = DatabaseManager(DB_PATH)
        logging.info("数据库管理器初始化完成")

        for city_code, city_config in CITIES.items():
            city_name = city_config['name']
            logging.info(f"\n--------- 开始处理城市: {city_name} ---------")
            
            scraper = LianjiaScraper(city_config)
            scraped_data = scraper.run()
            
            if scraped_data:
                logging.info(f"正在将 {city_name} 的数据存入数据库...")
                db_manager.insert_rent_data(city_name, scraped_data)
                
                excel_filename = f"{city_code}_rent_data.xlsx"
                excel_path = os.path.join(BASE_DIR, excel_filename)
                scraper.save_to_excel(scraped_data, excel_path)
            
            logging.info(f"--------- 城市: {city_name} 处理完毕 ---------")

        logging.info("\n========= 所有爬虫任务执行完毕 =========")
        return True
    except Exception as e:
        logging.error(f"爬虫执行出错: {str(e)}", exc_info=True)
        return False

if __name__ == '__main__':
    run_all_scrapers()