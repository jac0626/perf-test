#!/usr/bin/env python3
"""
Performance metrics analysis script
Analyzes perf output and generates reports
"""

import re
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple

class PerformanceAnalyzer:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = results_dir
        self.metrics = {
            "cache": {},
            "pipeline": {},
            "memory": {},
            "cpu": {}
        }
        self.hotspots = []
        self.system_info = {}
        
    def extract_value(self, pattern: str, text: str) -> int:
        """Extract numeric value from text using regex pattern"""
        match = re.search(pattern, text)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def analyze_cache_metrics(self, filepath: str = None) -> Dict[str, float]:
        """Analyze cache performance metrics"""
        if filepath is None:
            filepath = f"{self.results_dir}/metrics/cache.txt"
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            return {}
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract cache metrics
        patterns = [
            ('cache_references', r'([\d,]+)\s+cache-references'),
            ('cache_misses', r'([\d,]+)\s+cache-misses'),
            ('l1d_loads', r'([\d,]+)\s+L1-dcache-loads'),
            ('l1d_load_misses', r'([\d,]+)\s+L1-dcache-load-misses'),
            ('l1d_stores', r'([\d,]+)\s+L1-dcache-stores'),
            ('l1d_store_misses', r'([\d,]+)\s+L1-dcache-store-misses'),
            ('llc_loads', r'([\d,]+)\s+LLC-loads'),
            ('llc_load_misses', r'([\d,]+)\s+LLC-load-misses'),
            ('dtlb_loads', r'([\d,]+)\s+dTLB-loads'),
            ('dtlb_load_misses', r'([\d,]+)\s+dTLB-load-misses'),
        ]
        
        raw_metrics = {}
        for name, pattern in patterns:
            value = self.extract_value(pattern, content)
            if value:
                raw_metrics[name] = value
        
        # Calculate hit rates
        hit_rates = {}
        
        if 'cache_references' in raw_metrics and 'cache_misses' in raw_metrics:
            refs = raw_metrics['cache_references']
            misses = raw_metrics['cache_misses']
            if refs > 0:
                hit_rates['overall_cache_hit_rate'] = round((1 - misses/refs) * 100, 2)
                hit_rates['overall_cache_miss_rate'] = round((misses/refs) * 100, 2)
        
        if 'l1d_loads' in raw_metrics and 'l1d_load_misses' in raw_metrics:
            loads = raw_metrics['l1d_loads']
            misses = raw_metrics['l1d_load_misses']
            if loads > 0:
                hit_rates['l1d_hit_rate'] = round((1 - misses/loads) * 100, 2)
        
        if 'llc_loads' in raw_metrics and 'llc_load_misses' in raw_metrics:
            loads = raw_metrics['llc_loads']
            misses = raw_metrics['llc_load_misses']
            if loads > 0:
                hit_rates['llc_hit_rate'] = round((1 - misses/loads) * 100, 2)
        
        if 'dtlb_loads' in raw_metrics and 'dtlb_load_misses' in raw_metrics:
            loads = raw_metrics['dtlb_loads']
            misses = raw_metrics['dtlb_load_misses']
            if loads > 0:
                hit_rates['dtlb_hit_rate'] = round((1 - misses/loads) * 100, 2)
        
        self.metrics['cache'] = hit_rates
        
        # Print results
        print("\n=== Cache Hit Rates ===")
        for key, value in hit_rates.items():
            print(f"{key}: {value}%")
        
        return hit_rates
    
    def analyze_pipeline_metrics(self, filepath: str = None) -> Dict[str, float]:
        """Analyze pipeline and IPC metrics"""
        if filepath is None:
            filepath = f"{self.results_dir}/metrics/pipeline.txt"
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            return {}
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract pipeline metrics
        cycles = self.extract_value(r'([\d,]+)\s+cycles', content)
        instructions = self.extract_value(r'([\d,]+)\s+instructions', content)
        branches = self.extract_value(r'([\d,]+)\s+branches', content)
        branch_misses = self.extract_value(r'([\d,]+)\s+branch-misses', content)
        stalled_frontend = self.extract_value(r'([\d,]+)\s+stalled-cycles-frontend', content)
        stalled_backend = self.extract_value(r'([\d,]+)\s+stalled-cycles-backend', content)
        
        # Calculate derived metrics
        derived_metrics = {}
        
        if cycles and instructions:
            if cycles > 0:
                derived_metrics['ipc'] = round(instructions / cycles, 3)
                derived_metrics['cpi'] = round(cycles / instructions, 3)
        
        if branches and branch_misses:
            if branches > 0:
                accuracy = (1 - branch_misses/branches) * 100
                derived_metrics['branch_prediction_accuracy'] = round(accuracy, 2)
                derived_metrics['branch_miss_rate'] = round(branch_misses/branches * 100, 2)
        
        if cycles:
            if stalled_frontend and cycles > 0:
                ratio = (stalled_frontend/cycles) * 100
                derived_metrics['frontend_stall_ratio'] = round(ratio, 2)
            
            if stalled_backend and cycles > 0:
                ratio = (stalled_backend/cycles) * 100
                derived_metrics['backend_stall_ratio'] = round(ratio, 2)
        
        self.metrics['pipeline'] = derived_metrics
        
        # Print results
        print("\n=== Pipeline Efficiency Metrics ===")
        for key, value in derived_metrics.items():
            print(f"{key}: {value}")
        
        return derived_metrics
    
    def analyze_hotspots(self, filepath: str = None) -> List[Dict[str, str]]:
        """Extract performance hotspots from perf report"""
        if filepath is None:
            filepath = f"{self.results_dir}/reports/perf_report.txt"
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            return []
        
        hotspots = []
        with open(filepath, 'r') as f:
            lines = f.readlines()[:50]  # Read top 50 lines
            
            for line in lines:
                # Skip comments and headers
                if line.startswith('#') or not line.strip():
                    continue
                
                # Parse perf report lines (format: percentage command symbol)
                if '%' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            percentage = parts[0].rstrip('%')
                            if float(percentage) > 0.5:  # Only record >0.5% hotspots
                                function_name = ' '.join(parts[4:])[:100]  # Limit length
                                hotspots.append({
                                    'percentage': percentage,
                                    'function': function_name.strip()
                                })
                        except (ValueError, IndexError):
                            continue
        
        self.hotspots = hotspots[:20]  # Keep top 20
        return self.hotspots
    
    def analyze_system_info(self, filepath: str = None) -> Dict[str, Any]:
        """Extract system information"""
        if filepath is None:
            filepath = f"{self.results_dir}/reports/system_info.txt"
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            return {}
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        info = {}
        
        # Extract CPU model
        cpu_model = re.search(r'Model name:\s+(.+)', content)
        if cpu_model:
            info['cpu_model'] = cpu_model.group(1).strip()
        
        # Extract CPU count
        cpu_count = re.search(r'CPU\(s\):\s+(\d+)', content)
        if cpu_count:
            info['cpu_count'] = int(cpu_count.group(1))
        
        # Extract architecture
        arch = re.search(r'Architecture:\s+(.+)', content)
        if arch:
            info['architecture'] = arch.group(1).strip()
        
        # Extract cache sizes
        l1d = re.search(r'L1d cache:\s+(.+)', content)
        if l1d:
            info['l1d_cache'] = l1d.group(1).strip()
        
        l1i = re.search(r'L1i cache:\s+(.+)', content)
        if l1i:
            info['l1i_cache'] = l1i.group(1).strip()
        
        l2 = re.search(r'L2 cache:\s+(.+)', content)
        if l2:
            info['l2_cache'] = l2.group(1).strip()
        
        l3 = re.search(r'L3 cache:\s+(.+)', content)
        if l3:
            info['l3_cache'] = l3.group(1).strip()
        
        self.system_info = info
        return info
    
    def generate_json_report(self, output_file: str = None) -> None:
        """Generate comprehensive JSON report"""
        if output_file is None:
            output_file = f"{self.results_dir}/performance_report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "system": self.system_info,
            "metrics": self.metrics,
            "hotspots": self.hotspots
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nJSON report saved to: {output_file}")
    
    def generate_markdown_report(self, output_file: str = None) -> None:
        """Generate Markdown report"""
        if output_file is None:
            output_file = f"{self.results_dir}/REPORT.md"
        
        with open(output_file, 'w') as f:
            f.write("# Performance Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            # System information
            if self.system_info:
                f.write("## System Information\n\n")
                for key, value in self.system_info.items():
                    f.write(f"- **{key}**: {value}\n")
                f.write("\n")
            
            # Performance metrics
            f.write("## Performance Metrics\n\n")
            
            if self.metrics.get('cache'):
                f.write("### Cache Performance\n\n")
                for key, value in self.metrics['cache'].items():
                    f.write(f"- **{key}**: {value}%\n")
                f.write("\n")
            
            if self.metrics.get('pipeline'):
                f.write("### Pipeline Efficiency\n\n")
                for key, value in self.metrics['pipeline'].items():
                    if 'ratio' in key or 'rate' in key or 'accuracy' in key:
                        f.write(f"- **{key}**: {value}%\n")
                    else:
                        f.write(f"- **{key}**: {value}\n")
                f.write("\n")
            
            # Hotspots
            if self.hotspots:
                f.write("## Performance Hotspots\n\n")
                f.write("Top CPU consuming functions:\n\n")
                for i, hotspot in enumerate(self.hotspots[:10], 1):
                    f.write(f"{i}. **{hotspot['percentage']}%** - `{hotspot['function']}`\n")
                f.write("\n")
            
            # Visualizations
            f.write("## Visualizations\n\n")
            f.write("- [CPU Flame Graph](flamegraphs/cpu_flamegraph.svg)\n")
            f.write("- [Performance Dashboard](dashboard.html)\n")
        
        print(f"Markdown report saved to: {output_file}")
    
    def print_summary(self) -> None:
        """Print performance summary to console"""
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("="*60)
        
        # Key metrics
        cache = self.metrics.get('cache', {})
        pipeline = self.metrics.get('pipeline', {})
        
        if cache.get('overall_cache_hit_rate'):
            print(f"Overall Cache Hit Rate: {cache['overall_cache_hit_rate']}%")
        
        if pipeline.get('ipc'):
            print(f"Instructions Per Cycle: {pipeline['ipc']}")
        
        if pipeline.get('branch_prediction_accuracy'):
            print(f"Branch Prediction Accuracy: {pipeline['branch_prediction_accuracy']}%")
        
        # Top hotspots
        if self.hotspots:
            print("\nTop 3 Hotspots:")
            for i, hotspot in enumerate(self.hotspots[:3], 1):
                print(f"  {i}. {hotspot['percentage']}% - {hotspot['function'][:50]}")
        
        print("="*60 + "\n")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze performance metrics')
    parser.add_argument('--results-dir', default='results', help='Results directory')
    parser.add_argument('--cache', action='store_true', help='Analyze cache metrics')
    parser.add_argument('--pipeline', action='store_true', help='Analyze pipeline metrics')
    parser.add_argument('--hotspots', action='store_true', help='Analyze hotspots')
    parser.add_argument('--all', action='store_true', help='Run all analyses')
    
    args = parser.parse_args()
    
    analyzer = PerformanceAnalyzer(args.results_dir)
    
    # Run analyses
    if args.all or args.cache:
        analyzer.analyze_cache_metrics()
    
    if args.all or args.pipeline:
        analyzer.analyze_pipeline_metrics()
    
    if args.all or args.hotspots:
        analyzer.analyze_hotspots()
    
    if args.all:
        analyzer.analyze_system_info()
        analyzer.generate_json_report()
        analyzer.generate_markdown_report()
        analyzer.print_summary()

if __name__ == "__main__":
    main()