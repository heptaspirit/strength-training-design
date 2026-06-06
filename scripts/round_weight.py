#!/usr/bin/env python3
"""
strength-training-design skill — weight rounding to nearest plate step
Used by: 功能三 step 3 — rounding calculated weights to actual gym plates
Usage: python scripts/round_weight.py --weight <value> --plate_step <step>
"""

import argparse

def round_weight(weight: float, plate_step: float = 2.5) -> float:
    """
    根据健身房哑铃片最小步进取整重量
    
    Args:
        weight: 计算出的理论重量
        plate_step: 哑铃片最小重量（kg），常见 2.5 / 1.25 / 0.5
    
    Returns:
        取整后的重量
    """
    # 向下取整到最近的 plate_step 倍数
    rounded = (weight // plate_step) * plate_step
    
    # 可选：向上取整（更激进）
    # rounded_up = rounded + plate_step if rounded < weight else rounded
    
    return rounded

def generate_weight_options(weight: float, plate_step: float = 2.5) -> list:
    """生成几个可选重量（向下和向上）"""
    base = round_weight(weight, plate_step)
    return [
        base - plate_step,  # 保守
        base,              # 标准
        base + plate_step,  # 激进
    ]

def main():
    parser = argparse.ArgumentParser(description='重量取整（根据哑铃片步进）')
    parser.add_argument('--weight', type=float, required=True, help='理论重量（kg）')
    parser.add_argument('--plate_step', type=float, default=2.5, help='哑铃片最小步进（kg，默认 2.5）')
    parser.add_argument('--show_options', action='store_true', help='显示多个可选重量')
    
    args = parser.parse_args()
    
    rounded = round_weight(args.weight, args.plate_step)
    
    print(f"📊 重量取整结果:")
    print(f"   理论重量: {args.weight} kg")
    print(f"   哑铃片步进: {args.plate_step} kg")
    print(f"   取整重量: {rounded} kg")
    
    if args.show_options:
        options = generate_weight_options(args.weight, args.plate_step)
        print(f"\n💡 可选重量（保守 → 激进）:")
        for i, opt in enumerate(options):
            label = ["保守（降一档）", "标准（推荐）", "激进（加一档）"][i]
            print(f"   {opt} kg - {label}")
    
    # 输出 Markdown 表格行（用于 AI 生成计划）
    print(f"\n💡 AI 输出参考:")
    print(f"   - 参考重量 {args.weight}kg → 取整 {rounded}kg（步进 {args.plate_step}kg）")

if __name__ == '__main__':
    main()
