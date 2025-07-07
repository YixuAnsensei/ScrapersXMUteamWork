import streamlit as st
import pandas as pd
from config_in import CITIES, DB_PATH
from database.database_manager import DatabaseManager
from analysis.visualizer import (
    create_advanced_rent_bar_chart, 
    create_rent_treemap, 
    create_price_vs_count_scatter
)
from openai import OpenAI
import os
import time

# --- 安全警告 ---
st.warning("⚠️ **安全警告**: 此应用包含硬编码的API密钥。请勿公开分享此代码或部署到公共环境！")

# --- 页面配置 ---
st.set_page_config(
    page_title="城市生活分析仪",
    layout="wide"
)

# --- 嵌入的API密钥 (仅供测试使用) ---
DEEPSEEK_API_KEY = "自行填写你的apiKey"
AI_MODEL_NAME = "deepseek-chat"  # DeepSeek专用模型名称

# --- 应用状态初始化 ---
@st.cache_resource
def get_db_manager():
    """缓存数据库管理器实例，避免重复创建。"""
    return DatabaseManager(DB_PATH)

db_manager = get_db_manager()

# --- 数据加载与缓存 ---
@st.cache_data(ttl=3600)
def load_data(city_name):
    """从数据库加载并分析指定城市的数据。"""
    analyzed_list = db_manager.fetch_analyzed_data(city_name)
    if not analyzed_list:
        st.warning(f"未能加载到 {city_name} 的数据。请先运行爬虫脚本。")
        return None
    return pd.DataFrame(analyzed_list)

# --- 独立的城市看板渲染函数 ---
def display_city_dashboard(city_name: str, city_code: str):
    """
    为一个城市渲染完整的仪表盘UI，包含图表、表格和二级分析。
    """
    st.header(f'📈 {city_name}租房市场分析')
    
    # 加载数据
    df = load_data(city_name)
    
    if df is not None:
        # 1. 主区域：高级条形图 + 数据表格
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            advanced_chart = create_advanced_rent_bar_chart(df, city_name)
            st.plotly_chart(advanced_chart, use_container_width=True)
            
        with col2:
            st.markdown("#### 核心数据一览")
            df_display = df.rename(columns={
                '区域': '行政区',
                'house_count': '房源数',
                'avg_price': '平均租金',
                'avg_price_per_sqm': '每平米均价'
            })

            # --- 【核心修改点】 ---
            # 将DataFrame的索引从0开始改为从1开始
            df_display.index = df_display.index + 1
            # --- 修改结束 ---

            st.dataframe(df_display.style.format({
                "平均租金": "¥{:.0f}",
                "每平米均价": "{:.2f}元/㎡",
                "房源数": "{}套"
            }))
        
        # 2. 二级分析区域：使用Expander提供更多图表
        with st.expander("展开查看更多维度分析..."):
            st.subheader("房源数量与价格分布")
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                treemap_fig = create_rent_treemap(df, city_name)
                st.plotly_chart(treemap_fig, use_container_width=True)
            with exp_col2:
                scatter_fig = create_price_vs_count_scatter(df, city_name)
                st.plotly_chart(scatter_fig, use_container_width=True)

        return df
    else:
        st.info(f"暂无 {city_name} 数据，请先执行爬虫。")
        return None

# --- 页面UI ---
st.title('🤖 城市生活分析仪')
st.markdown("---")

# --- 动态生成城市看板 ---
city_names = [CITIES[key]['name'] for key in CITIES]
city_tabs = st.tabs(city_names)

all_data = {}

for i, city_code in enumerate(CITIES.keys()):
    with city_tabs[i]:
        city_name = CITIES[city_code]['name']
        city_df = display_city_dashboard(city_name, city_code)
        if city_df is not None:
            all_data[city_name] = city_df

st.markdown("---")

# --- AI 对话模块 - 硬编码密钥版 ---
st.header("💬 与AI数据分析师对话")

# 添加使用说明
with st.sidebar:
    st.subheader("AI服务状态")
    st.info(f"🔑 使用预置DeepSeek API密钥 (模型: {AI_MODEL_NAME})")
    st.warning("此密钥将在所有用户间共享，请勿滥用！")

@st.cache_resource
def get_ai_client():
    """获取并缓存AI客户端。"""
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,  # 直接使用硬编码密钥
            base_url="https://api.deepseek.com/v1"  # DeepSeek专用API端点
        )
        
        # 测试连接
        try:
            client.models.list()
            st.sidebar.success(f"✅ 连接DeepSeek成功! 模型可用: {AI_MODEL_NAME}")
        except Exception as test_error:
            st.sidebar.error(f"❌ 连接测试失败: {str(test_error)}")
            return None
            
        return client
    except Exception as e:
        st.error(f"初始化AI客户端时出错: {e}")
        return None

# 初始化客户端
client = get_ai_client()

def get_ai_response(user_prompt, city_data_map):
    if not client:
        return "错误: AI客户端初始化失败，请联系管理员。", False

    # 简化数据摘要
    data_summary = "\n".join([
        f"{city}: {len(df)}个区域数据" 
        for city, df in city_data_map.items() 
        if df is not None
    ])

    system_prompt = f"""
    你是一个专业的中国城市房地产数据分析助手。以下是各城市数据区域数量摘要:
    {data_summary}
    
    请根据这些数据，用中文回答用户问题。回答要简洁专业，包含具体数据支持。
    """

    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=AI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1024,
                temperature=0.7,
                timeout=10
            )
            return response.choices[0].message.content, True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                error_msg = f"请求AI服务时出错: {str(e)}"
                return error_msg, False
    
    # 【修改点 1】: 添加防御性返回语句。
    # 这段代码在理论上不应该被执行到，但作为安全保障，
    # 它可以防止函数在任何意想不到的情况下隐式返回 None。
    return "AI响应循环意外结束，未能获取结果。", False

# Streamlit 聊天界面逻辑 - 修复版
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "你好！我是你的租房数据分析助手，请问有什么可以帮你的吗？"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("例如：哪个区的平均租金最贵？"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 准备AI响应区域
    with st.chat_message("assistant"):
        if client is None:  # 检查client是否为None
            error_msg = "AI服务不可用，请检查连接设置"
            st.error(error_msg)
            # 添加错误消息到历史记录
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            with st.spinner("AI正在思考中..."):
                response, success = get_ai_response(prompt, all_data)
                
                # 【修改点 2】: 强制确保 response 是一个字符串。
                # 这可以彻底解决类型检查器的警告，并防止在处理 content 时出现意外。
                if not isinstance(response, str):
                    response = str(response)

                if success:
                    st.write(response)
                    # 添加成功响应到历史记录
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error(response)
                    # 添加错误消息到历史记录
                    st.session_state.messages.append({"role": "assistant", "content": response})