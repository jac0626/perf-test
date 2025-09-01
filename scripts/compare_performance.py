#!/usr/bin/env python3
"""
性能对比脚本 - 比较两次运行的性能指标
使用方法: python3 compare_performance.py baseline.json current.json
"""

import json
import sys
import argparse
from typing import Dict, Any

def load_report(filepath: str) -> Dict[str, Any]:
    """加载性能报告"""
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_change(baseline: float, current: float) -> float:
    """计算百分比变化"""
    if baseline == 0:
        return 0
    return ((current - baseline) / baseline) * 100

def format_change(value: float, higher_is_better: bool = True) -> str:
    """格式化变化值，带颜色标记"""
    if value == 0:
        return "→ 0%"
    
    # 判断是改进还是退步
    is_improvement = (value > 0 and higher_is_better) or (value < 0 and not higher_is_better)
    
    # 选择符号和颜色
    if is_improvement:
        symbol = "↑" if value > 0 else "↓"
        color = "\033[92m"  # 绿色
    else:
        symbol = "↓" if value < 0 else "↑"
        color = "\033[91m"  # 红色
    
    return f"{color}{symbol} {abs(value):.2f}%\033[0m"

def compare_metrics(baseline: Dict, current: Dict) -> None:
    """比较性能指标"""
    
    print("\n" + "="*60)
    print("Performance Comparison Report")
    print("="*60)
    
    # 定义指标及其"越高越好"的属性
    metrics_config = {
        "cache": {
            "hit_rate": (True, "Cache Hit Rate"),
            "miss_rate": (False, "Cache Miss Rate")
        },
        "pipeline": {
            "ipc": (True, "Instructions Per Cycle"),
            "cpi": (False, "Cycles Per Instruction"),
            "branch_accuracy": (True, "Branch Prediction Accuracy")
        }
    }
    
    # 比较各类指标
    for category, metrics in metrics_config.items():
        print(f"\n### {category.upper()} Metrics")
        print("-" * 40)
        
        baseline_cat = baseline.get('metrics', {}).get(category, {})
        current_cat = current.get('metrics', {}).get(category, {})
        
        for metric_key, (higher_is_better, display_name) in metrics.items():
            baseline_val = baseline_cat.get(metric_key, 0)
            current_val = current_cat.get(metric_key, 0)
            
            if baseline_val == 0 and current_val == 0:
                continue
            
            change = calculate_change(baseline_val, current_val)
            change_str = format_change(change, higher_is_better)
            
            print(f"{display_name:30} {baseline_val:8.2f} → {current_val:8.2f}  {change_str}")
    
    # 比较热点函数
    print(f"\n### TOP HOTSPOTS Comparison")
    print("-" * 40)
    
    baseline_hotspots = baseline.get('hotspots', [])[:5]
    current_hotspots = current.get('hotspots', [])[:5]
    
    # 创建热点映射
    baseline_map = {h['function']: float(h['percentage']) for h in baseline_hotspots}
    current_map = {h['function']: float(h['percentage']) for h in current_hotspots}
    
    all_functions = set(baseline_map.keys()) | set(current_map.keys())
    
    for func in sorted(all_functions, key=lambda x: current_map.get(x, 0), reverse=True)[:10]:
        baseline_pct = baseline_map.get(func, 0)
        current_pct = current_map.get(func, 0)
        
        if baseline_pct == 0:
            change_str = "\033[93m(NEW)\033[0m"
        elif current_pct == 0:
            change_str = "\033[94m(REMOVED)\033[0m"
        else:
            change = current_pct - baseline_pct
            if abs(change) < 0.5:
                change_str = "→"
            elif change > 0:
                change_str = f"\033[91m↑ {change:.1f}%\033[0m"  # 更多CPU时间（通常不好）
            else:
                change_str = f"\033[92m↓ {abs(change):.1f}%\033[0m"  # 更少CPU时间（通常好）
        
        func_short = func[:40] + "..." if len(func) > 40 else func
        print(f"{func_short:45} {baseline_pct:6.1f}% → {current_pct:6.1f}%  {change_str}")
    
    # 总体评估
    print("\n" + "="*60)
    print("OVERALL ASSESSMENT")
    print("="*60)
    
    improvements = []
    regressions = []
    
    # 检查关键指标
    if 'cache' in current.get('metrics', {}):
        cache_change = calculate_change(
            baseline.get('metrics', {}).get('cache', {}).get('hit_rate', 0),
            current.get('metrics', {}).get('cache', {}).get('hit_rate', 0)
        )
        if cache_change > 1:
            improvements.append(f"Cache performance improved by {cache_change:.1f}%")
        elif cache_change < -1:
            regressions.append(f"Cache performance degraded by {abs(cache_change):.1f}%")
    
    if 'pipeline' in current.get('metrics', {}):
        ipc_change = calculate_change(
            baseline.get('metrics', {}).get('pipeline', {}).get('ipc', 0),
            current.get('metrics', {}).get('pipeline', {}).get('ipc', 0)
        )
        if ipc_change > 1:
            improvements.append(f"IPC improved by {ipc_change:.1f}%")
        elif ipc_change < -1:
            regressions.append(f"IPC degraded by {abs(ipc_change):.1f}%")
    
    if improvements:
        print("\n✅ Improvements:")
        for imp in improvements:
            print(f"  • {imp}")
    
    if regressions:
        print("\n⚠️  Regressions:")
        for reg in regressions:
            print(f"  • {reg}")
    
    if not improvements and not regressions:
        print("\n→ Performance is relatively stable (no significant changes)")
    
    print()

def main():
    parser = argparse.ArgumentParser(description='Compare performance reports')
    parser.add_argument('baseline', help='Baseline performance report (JSON)')
    parser.add_argument('current', help='Current performance report (JSON)')
    parser.add_argument('--threshold', type=float, default=5.0,
                       help='Threshold for significant change (default: 5%%)')
    
    args = parser.parse_args()
    
    try:
        baseline = load_report(args.baseline)
        current = load_report(args.current)
        compare_metrics(baseline, current)
        
    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()