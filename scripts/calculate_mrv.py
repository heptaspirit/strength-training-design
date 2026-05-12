#!/usr/bin/env python3
"""
MRV 审计计算脚本
用法：python calculate_mrv.py --muscle_group chest --weekly_sets 18 --mrv 22
"""

import argparse
import sys

# MRV 参考值（基于 近年 ACSM 指南和 JTS 数据）
MRV_TABLE = {
    'chest': 22,
    'quadriceps': 20,
    'back': 25,
    'posterior_chain': 16,
    'shoulders': 24,
    'biceps': 20,
    'triceps': 20,
    'hamstrings': 20,
    'glutes': 20,
    'calves': 16,
}

def calculate_mrv_status(weekly_sets: int, mrv: int) -> dict:
    """
    计算 MRV 状态和百分比
    
    Returns:
        dict: {percentage, status, emoji, recommendation}
    """
    percentage = (weekly_sets / mrv) * 100
    
    if percentage < 80:
        status = "安全"
        emoji = "✅"
        recommendation = "可继续增容或保持"
    elif percentage < 100:
        status = "接近 MRV"
        emoji = "⚠️"
        recommendation = "监控疲劳信号（睡眠、情绪、力量下降）"
    else:
        status = "超过 MRV"
        emoji = "❌"
        recommendation = "必须减容 20-30%，或插入减载周"
    
    return {
        'percentage': round(percentage, 1),
        'status': status,
        'emoji': emoji,
        'recommendation': recommendation,
        'weekly_sets': weekly_sets,
        'mrv': mrv,
    }

def main():
    parser = argparse.ArgumentParser(description='MRV 审计计算')
    parser.add_argument('--muscle_group', type=str, help='肌群名称（如 chest, back）')
    parser.add_argument('--weekly_sets', type=int, required=True, help='周训练组数')
    parser.add_argument('--mrv', type=int, help='MRV 参考值（不提供则从表中查询）')
    
    args = parser.parse_args()
    
    # 查询 MRV
    mrv = args.mrv
    if not mrv and args.muscle_group:
        mrv = MRV_TABLE.get(args.muscle_group.lower())
        if mrv:
            print(f"ℹ️  肌群 '{args.muscle_group}' 的 MRV 参考值: {mrv}")
        else:
            print(f"❌ 未找到肌群 '{args.muscle_group}' 的 MRV 数据，请手动指定 --mrv")
            sys.exit(1)
    
    if not mrv:
        print(f"❌ 必须提供 --mrv 或有效的 --muscle_group")
        sys.exit(1)
    
    # 计算
    result = calculate_mrv_status(args.weekly_sets, mrv)
    
    # 输出 Markdown 表格行
    print(f"\n| {args.muscle_group or '肌群'} | {result['weekly_sets']} 组 | {result['mrv']} | {result['percentage']}% | {result['emoji']} {result['status']} |")
    print(f"\n💡 建议: {result['recommendation']}")

if __name__ == '__main__':
    main()
