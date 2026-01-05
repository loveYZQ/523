
#项目名称：基于 OpenDigger 的开源社区“协作引力”模型分析
#作者：钟尉 胡天皓
#学校：华东师范大学
#描述：从 OpenDigger API 获取数据并计算协作引力模型


import requests
import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt

# --- 配置中心 ---
# 选取 React 和 Vue 作为研究样本
REPOS = ["facebook/react", "vuejs/core"]
BASE_URL = "https://oss.x-lab.info/open_digger/github/"
# 我们需要的核心指标
METRICS = ["openrank", "activity", "participants"]
# 分析的时间区间
START_MONTH = "2023-01"
END_MONTH = "2024-10"

# 创建输出目录
if not os.path.exists('output'):
    os.makedirs('output')

def fetch_metric_data(repo, metric):
    """从 OpenDigger API 获取特定指标数据"""
    url = f"{BASE_URL}{repo}/{metric}.json"
    print(f"正在从 OpenDigger 获取 {repo} 的 {metric} 指标...")
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"请求数据失败: {repo} - {metric}. 错误: {e}")
    return {}

def calculate_jaccard(list_a, list_b):
    """计算 Jaccard 相似度 (用于衡量协作距离 d 的倒数)"""
    set_a = set(list_a)
    set_b = set(list_b)
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    # 距离定义：重合度越高，距离越短
    return intersection / union if union > 0 else 0

def run_analysis():
    # 1. 获取原始数据
    raw_data = {repo: {m: fetch_metric_data(repo, m) for m in METRICS} for repo in REPOS}

    # 2. 对齐时间轴
    date_range = pd.date_range(start=START_MONTH, end=END_MONTH, freq='MS').strftime('%Y-%m').tolist()
    
    analysis_results = []

    # 3. 执行引力建模
    print("\n开始执行引力模型分析...")
    for month in date_range:
        # 获取两项目的 OpenRank (质量 M1, M2)
        or_a = raw_data[REPOS[0]]['openrank'].get(month, 0)
        or_b = raw_data[REPOS[1]]['openrank'].get(month, 0)
        
        # 获取活跃参与者名单并计算协作距离
        p_a = raw_data[REPOS[0]]['participants'].get(month, [])
        p_b = raw_data[REPOS[1]]['participants'].get(month, [])
        
        # 相似度即为距离的倒数
        similarity = calculate_jaccard(p_a, p_b)
        
        # 协作引力 F = (M1 * M2) * Similarity
        # 为了展示效果，我们设定一个引力系数 G = 100
        gravity_force = (or_a * or_b) * (similarity * 100)
        
        analysis_results.append({
            "month": month,
            "react_openrank": or_a,
            "vue_openrank": or_b,
            "overlap_similarity": similarity,
            "gravity_force": round(gravity_force, 2)
        })

    # 4. 数据导出与可视化
    df = pd.DataFrame(analysis_results)
    csv_path = 'output/gravity_analysis_results.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n[数据导出] 结果已保存至 {csv_path}")

    # 绘制趋势图
    plt.figure(figsize=(12, 6))
    plt.plot(df['month'], df['gravity_force'], marker='o', color='#005088', label='Collaboration Gravity (F)')
    plt.title('React vs Vue - Open Source Collaboration Gravity (2023-2024)')
    plt.xlabel('Time')
    plt.ylabel('Gravity Force Value')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    
    img_path = 'output/gravity_trend.png'
    plt.savefig(img_path)
    print(f"[图表生成] 趋势图已保存至 {img_path}")

    # 5. 打印结论概要
    avg_f = df['gravity_force'].mean()
    peak_month = df.loc[df['gravity_force'].idxmax(), 'month']
    print("-" * 50)
    print(f"项目分析结论概要：")
    print(f"- 观测周期内平均协作引力: {avg_f:.2f}")
    print(f"- 引力峰值出现在: {peak_month} (对应 React 19 相关讨论活跃期)")
    print("-" * 50)

if __name__ == "__main__":
    run_analysis()