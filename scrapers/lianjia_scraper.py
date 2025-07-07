# scrapers/lianjia_scraper.py
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from config_in import USER_AGENTS

class LianjiaScraper:
    """链家租房通用爬虫"""
    def __init__(self, city_config):
        self.city_name = city_config['name']
        self.url = city_config['url']
        self.driver = None

    def _setup_driver(self):
        """配置并初始化Selenium WebDriver,包含所有反爬虫设置。"""
        print(f"[{self.city_name}] 正在以【高级反爬虫模式】启动浏览器...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 注入JS脚本隐藏webdriver特征
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception as e:
            print(f"[{self.city_name}] WebDriver启动失败: {e}")
            raise


    def _get_page_source(self):
        """访问URL并获取页面源码。"""
        self.driver =None
        try:
            self._setup_driver() 
            
            print(f"[{self.city_name}] 正在访问: {self.url}")
            self.driver.get(self.url) # type: ignore
            
            WebDriverWait(self.driver, 20).until( # type: ignore
                EC.presence_of_element_located((By.CSS_SELECTOR, ".content__list"))
            )
            time.sleep(random.uniform(2, 4)) 
            return self.driver.page_source # type: ignore
        
        except Exception as e:
            print(f"[{self.city_name}] 在获取页面源码过程中发生错误: {e}")
            return None
        

        finally:
            if self.driver:
                self.driver.quit()
                print(f"[{self.city_name}] 浏览器已关闭。")

    def _parse_html(self, html_content):
        """使用BeautifulSoup解析HTML,提取房源信息。"""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.find_all('div', class_='content__list--item')
        if not items:
            print(f"[{self.city_name}] 警告：未能找到房源列表项。")
            return []

        data_list = []
        print(f"[{self.city_name}] 找到 {len(items)} 个房源，开始解析...")
        for item in items:
            try:
                title_tag = item.find('p', class_='content__list--item--title')
                title = title_tag.get_text(strip=True) if title_tag else 'N/A'
                
                desc_p = item.find('p', class_='content__list--item--des')
                desc_parts = [s for s in desc_p.stripped_strings if s not in ['-', '/']] if desc_p else []
                
                price_span = item.find('span', class_='content__list--item-price')
                price = price_span.get_text(strip=True) if price_span else 'N/A'
                
                # 过滤广告或无效条目
                if '精选' in title or '广告' in title or '仅剩' in desc_parts[0] or len(desc_parts[0])>=4 or not desc_parts:
                    continue

                data_list.append({
                    '标题': title,
                    '区域': desc_parts[0] if len(desc_parts) > 0 else 'N/A',
                    '地段': desc_parts[1] if len(desc_parts) > 1 else 'N/A',
                    '小区': desc_parts[2] if len(desc_parts) > 2 else 'N/A',
                    '面积': desc_parts[3] if len(desc_parts) > 3 else 'N/A',
                    '朝向': desc_parts[4] if len(desc_parts) > 4 else 'N/A',
                    '户型': desc_parts[5] if len(desc_parts) > 5 else 'N/A',
                    '价格': price
                })
            except Exception as e:
                print(f"处理一个条目时发生错误: {e}")
                continue
        return data_list

    def run(self):
        """执行爬虫的主流程。"""
        html = self._get_page_source()
        data = self._parse_html(html)
        print(f"[{self.city_name}] 爬取并解析完成，共获得 {len(data)} 条数据。")
        return data

    def save_to_excel(self, data, file_path):
        """将数据保存到Excel文件。"""
        if not data:
            print("数据为空，不创建Excel文件。")
            return
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        print(f"数据已成功保存到 {file_path}")