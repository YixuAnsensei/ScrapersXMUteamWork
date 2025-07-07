# analysis/analyzer.py
from database.database_manager import DatabaseManager

def get_analyzed_rent_data(db_manager: DatabaseManager, city_name: str):
    """
    获取指定城市的租房分析数据。
    真正的计算发生在DatabaseManager的fetch_analyzed_data方法中。
    """
    print(f"分析模块：正在为 {city_name} 获取分析数据...")
    try:
        data = db_manager.fetch_analyzed_data(city_name)
        print(f"分析模块：成功获取 {len(data)} 条 {city_name} 的分析结果。")
        return data
    except Exception as e:
        print(f"分析模块：获取 {city_name} 数据时出错: {e}")
        return []