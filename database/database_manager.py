# database/database_manager.py
import sqlite3
import re
from datetime import datetime

class DatabaseManager:
    """统一管理所有数据库操作。"""
    def __init__(self, db_path):
        """
        初始化数据库管理器。
        参数:
            db_path (str): SQLite数据库文件的路径。
        """
        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        """获取数据库连接，并设置row_factory以便返回字典。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self):
        """创建rent_data表（如果不存在）。"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rent_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    title TEXT,
                    zone TEXT,
                    district TEXT,
                    area_name TEXT,
                    area_size_str TEXT,
                    area_size_num REAL, -- 新增：存储清洗后的面积数值
                    orientation TEXT,
                    layout TEXT,
                    price_str TEXT,
                    price_num INTEGER, -- 新增：存储清洗后的价格数值
                    crawled_at TIMESTAMP
                )
            ''')
            print(f"数据库 '{self.db_path}' 表已检查/创建。")

    def _clean_data(self, raw_data_list, city_name):
        """在插入数据库前，集中清洗数据。"""
        cleaned_data = []
        crawled_time = datetime.now()
        for item in raw_data_list:
            price_str = item.get('价格', '0')
            area_size_str = item.get('面积', '0')

            price_match = re.search(r'[\d.]+', price_str)
            price_num = int(float(price_match.group())) if price_match else 0

            area_match = re.search(r'[\d.]+', area_size_str)
            area_size_num = float(area_match.group()) if area_match else 0.0

            if price_num > 0: # 只要价格有效就插入
                cleaned_data.append((
                    city_name,
                    item.get('标题', 'N/A'),
                    item.get('区域', 'N/A'),
                    item.get('地段', 'N/A'),
                    item.get('小区', 'N/A'),
                    area_size_str,
                    area_size_num,
                    item.get('朝向', 'N/A'),
                    item.get('户型', 'N/A'),
                    price_str,
                    price_num,
                    crawled_time
                ))
        return cleaned_data

    def insert_rent_data(self, city_name, data_list):
        """
        将一个城市的数据批量插入数据库，插入前会清空该城市旧数据。
        """
        if not data_list:
            print(f"没有可供插入 {city_name} 的数据。")
            return

        rows_to_insert = self._clean_data(data_list, city_name)
        if not rows_to_insert:
            print(f"数据清洗后，没有可供插入 {city_name} 的有效数据。")
            return
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 事务开始
            cursor.execute("DELETE FROM rent_data WHERE city = ?", (city_name,))
            
            insert_sql = '''
                INSERT INTO rent_data (
                    city, title, zone, district, area_name, area_size_str, area_size_num,
                    orientation, layout, price_str, price_num, crawled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.executemany(insert_sql, rows_to_insert)
            # 事务提交
            conn.commit()
            
        print(f"成功将 {len(rows_to_insert)} 条 {city_name} 数据写入数据库。")

    def fetch_analyzed_data(self, city_name):
        """
        使用SQL直接进行分组聚合分析，返回分析结果。
        这是最高效的方式！
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql_query = """
                SELECT
                    zone AS "区域",
                    COUNT(id) AS "house_count",
                    AVG(price_num) AS "avg_price",
                    -- 避免除以0的错误
                    CASE WHEN SUM(CASE WHEN area_size_num > 0 THEN 1 ELSE 0 END) > 0
                         THEN SUM(price_num) / SUM(area_size_num)
                         ELSE 0
                    END AS "avg_price_per_sqm"
                FROM
                    rent_data
                WHERE
                    city = ? AND price_num > 0 AND zone IS NOT NULL AND zone != ''
                GROUP BY
                    zone
                HAVING
                    COUNT(id) > 1 -- 过滤掉只有一个房源的区域，让分析更有意义
                ORDER BY
                    avg_price DESC;
            """
            cursor.execute(sql_query, (city_name,))
            # 将 sqlite3.Row 对象转换为普通字典列表
            return [dict(row) for row in cursor.fetchall()]