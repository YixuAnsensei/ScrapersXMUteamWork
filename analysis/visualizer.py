import plotly.express as px
import pandas as pd

def create_advanced_rent_bar_chart(data_df: pd.DataFrame, city_name: str):
    """创建一个带有切换按钮的高级交互式条形图。"""
    if data_df.empty:
        return px.bar(title=f'{city_name} - 数据为空')

    print(f"可视化模块：正在为 {city_name} 生成高级图表...")

    # 先按总价创建基础图表
    fig = px.bar(
        data_frame=data_df,
        x='区域',
        y='avg_price',
        title=f'{city_name}各区租金对比分析',
        labels={'区域': '行政区', 'avg_price': '平均月租金 (元)', 'avg_price_per_sqm': '平均每平米租金 (元/㎡)'},
        text='avg_price',
        color='avg_price',
        color_continuous_scale=px.colors.sequential.Reds
    )

    # 再创建一个按每平米均价的图表，用于“切换”
    fig2 = px.bar(
        data_frame=data_df,
        x='区域',
        y='avg_price_per_sqm',
        text='avg_price_per_sqm',
        color='avg_price_per_sqm',
        color_continuous_scale=px.colors.sequential.Blues
    )

    # 将图2的轨迹(traces)添加到图1中，但先设为不可见
    fig.add_trace(fig2.data[0])
    fig.data[1].visible = False

    # --- 创建交互式按钮 ---
    fig.update_layout(
        title_x=0.5,
        coloraxis_showscale=False,
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                active=0,
                x=0.7,
                y=1.15,
                buttons=list([
                    dict(label="按总价",
                         method="update",
                         # 【修改】args现在包含两个字典，第二个用于更新layout
                         args=[{"visible": [True, False]},
                               {"title": f"{city_name}各区平均月租金对比",
                                "yaxis.title.text": "平均月租金 (元)"}]),
                    dict(label="按每平米单价",
                         method="update",
                         # 【修改】args现在包含两个字典，第二个用于更新layout
                         args=[{"visible": [False, True]},
                               {"title": f"{city_name}各区每平米月租金对比",
                                "yaxis.title.text": "平均每平米租金 (元/㎡)"}]),
                ]),
            )
        ])
    
    # 更新两个轨迹的文本显示格式
    fig.data[0].update(texttemplate='¥%{text:,.0f}', textposition='outside')
    fig.data[1].update(texttemplate='¥%{text:,.2f}', textposition='outside')
    
    print(f"可视化模块：{city_name} 高级图表已生成。")
    return fig



def create_rent_treemap(data_df: pd.DataFrame, city_name: str):
    """
    使用Plotly创建一个展示各区房源数量分布的树状图。
    矩形的面积代表房源数量，颜色代表该区域的平均租金。
    
    参数:
        data_df (pd.DataFrame): 包含分析结果的DataFrame。
        city_name (str): 城市名称，用于图表标题和根节点。
    """
    # 安全检查：如果数据为空，返回一个空状态的图表
    if data_df.empty:
        return px.treemap(title=f'{city_name} - 房源分布数据为空')

    print(f"可视化模块：正在为 {city_name} 生成房源分布树状图...")
    
    fig = px.treemap(
        data_frame=data_df,
        # path 定义了层级结构。px.Constant(city_name) 创建了一个统一的根节点（整个大方块代表城市），
        # '区域' 则是在这个根节点下，根据“区域”列创建子节点。
        path=[px.Constant(city_name), '区域'], 
        
        # values 定义了每个矩形的面积大小，这里我们用房源数量(house_count)来决定
        values='house_count',
        
        # color 定义了每个矩形的颜色，这里我们用平均租金(avg_price)来决定
        color='avg_price',
        
        # color_continuous_scale 设置了颜色的渐变方案，'viridis'是一个视觉效果很好的色阶
        color_continuous_scale='viridis',
        
        # hover_data 自定义了鼠标悬浮时显示的信息
        hover_data={'avg_price': ':.0f'}, # 将悬浮显示的平均价格格式化为整数
        
        title=f'{city_name}各区房源数量及平均租金分布'
    )
    
    # 将标题居中，并设置一个合适的字体大小
    fig.update_layout(title_x=0.5, font=dict(size=16))
    
    print(f"可视化模块：{city_name} 树状图已生成。")
    return fig



def create_price_vs_count_scatter(data_df: pd.DataFrame, city_name: str):
    """
    使用Plotly创建一个散点图，探索各区“平均租金”与“房源数量”之间的关系。
    点的位置由(x, y)决定，点的大小和颜色可以用来展示更多维度的数据。
    
    参数:
        data_df (pd.DataFrame): 包含分析结果的DataFrame。
        city_name (str): 城市名称，用于图表标题。
    """
    # 安全检查
    if data_df.empty:
        return px.scatter(title=f'{city_name} - 关系数据为空')

    print(f"可视化模块：正在为 {city_name} 生成均价-数量散点图...")

    fig = px.scatter(
        data_frame=data_df,
        x='house_count',       # X轴：房源数量
        y='avg_price',         # Y轴：平均租金
        
        # size 参数让点的大小可以代表第三个维度的数据，这里我们用“每平米均价”
        size='avg_price_per_sqm',
        
        # color 参数让点的颜色可以代表第四个维度的数据，这里我们用“区域”来区分
        color='区域',
        
        # hover_name 设置了鼠标悬浮时，信息框顶部的粗体标题
        hover_name='区域',
        
        # size_max 控制了点的最大尺寸，防止因数值差异过大导致某些点过分巨大
        size_max=60,
        
        title=f'{city_name}各区平均租金 vs. 房源数量关系图',
        labels={'house_count': '房源数量 (套)', 'avg_price': '平均月租金 (元)'}
    )
    
    # 将标题居中
    fig.update_layout(title_x=0.5)
    
    print(f"可视化模块：{city_name} 散点图已生成。")
    return fig