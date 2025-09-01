#!/usr/bin/env python3
"""
Generate interactive HTML dashboard for performance metrics
"""

import json
import os
import sys
import argparse
from typing import Dict, Any

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print("Error: plotly not installed. Install with: pip install plotly")
    sys.exit(1)

class DashboardGenerator:
    def __init__(self, report_file: str = "results/performance_report.json"):
        self.report_file = report_file
        self.data = {}
        
    def load_report(self) -> bool:
        """Load performance report JSON"""
        if not os.path.exists(self.report_file):
            print(f"Error: Report file {self.report_file} not found")
            return False
        
        with open(self.report_file, 'r') as f:
            self.data = json.load(f)
        return True
    
    def create_dashboard(self, output_file: str = "results/dashboard.html") -> None:
        """Create interactive HTML dashboard"""
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Cache Hit Rates', 
                'Pipeline Efficiency',
                'Top Hotspots', 
                'Stall Analysis',
                'Performance Metrics Table',
                'IPC Gauge'
            ),
            specs=[
                [{'type': 'bar'}, {'type': 'indicator'}],
                [{'type': 'bar'}, {'type': 'pie'}],
                [{'type': 'table', 'colspan': 2}, None]
            ],
            row_heights=[0.3, 0.3, 0.4],
            vertical_spacing=0.1,
            horizontal_spacing=0.15
        )
        
        # 1. Cache Hit Rates Bar Chart
        cache_metrics = self.data.get('metrics', {}).get('cache', {})
        if cache_metrics:
            cache_names = []
            cache_values = []
            for key, value in cache_metrics.items():
                if 'hit_rate' in key:
                    display_name = key.replace('_', ' ').title()
                    cache_names.append(display_name)
                    cache_values.append(value)
            
            fig.add_trace(
                go.Bar(
                    x=cache_names,
                    y=cache_values,
                    text=[f'{v:.1f}%' for v in cache_values],
                    textposition='auto',
                    marker_color=['green' if v > 90 else 'orange' if v > 80 else 'red' 
                                  for v in cache_values],
                    name='Cache Hit Rates'
                ),
                row=1, col=1
            )
        
        # 2. IPC Indicator
        pipeline_metrics = self.data.get('metrics', {}).get('pipeline', {})
        ipc_value = pipeline_metrics.get('ipc', 0)
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=ipc_value,
                title={'text': "Instructions Per Cycle", 'font': {'size': 14}},
                delta={'reference': 2.0, 'position': "bottom"},
                gauge={
                    'axis': {'range': [0, 4], 'tickwidth': 1},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 1], 'color': "lightgray"},
                        {'range': [1, 2], 'color': "gray"},
                        {'range': [2, 3], 'color': "lightgreen"},
                        {'range': [3, 4], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 3.5
                    }
                }
            ),
            row=1, col=2
        )
        
        # 3. Top Hotspots Horizontal Bar
        hotspots = self.data.get('hotspots', [])[:10]
        if hotspots:
            hotspot_functions = []
            hotspot_percentages = []
            
            for h in hotspots:
                func_name = h['function'][:40] + '...' if len(h['function']) > 40 else h['function']
                hotspot_functions.append(func_name)
                hotspot_percentages.append(float(h['percentage']))
            
            fig.add_trace(
                go.Bar(
                    x=hotspot_percentages,
                    y=hotspot_functions,
                    orientation='h',
                    text=[f'{p:.1f}%' for p in hotspot_percentages],
                    textposition='auto',
                    marker_color='indianred',
                    name='CPU Usage'
                ),
                row=2, col=1
            )
        
        # 4. Stall Analysis Pie Chart
        frontend_stall = pipeline_metrics.get('frontend_stall_ratio', 0)
        backend_stall = pipeline_metrics.get('backend_stall_ratio', 0)
        
        if frontend_stall or backend_stall:
            stall_labels = []
            stall_values = []
            stall_colors = []
            
            if frontend_stall > 0:
                stall_labels.append('Frontend Stall')
                stall_values.append(frontend_stall)
                stall_colors.append('#FF6B6B')
            
            if backend_stall > 0:
                stall_labels.append('Backend Stall')
                stall_values.append(backend_stall)
                stall_colors.append('#FFA500')
            
            # Add non-stalled portion
            total_stall = frontend_stall + backend_stall
            if total_stall < 100:
                stall_labels.append('Not Stalled')
                stall_values.append(100 - total_stall)
                stall_colors.append('#4CAF50')
            
            fig.add_trace(
                go.Pie(
                    labels=stall_labels,
                    values=stall_values,
                    marker_colors=stall_colors,
                    textinfo='label+percent',
                    hole=0.3
                ),
                row=2, col=2
            )
        
        # 5. Metrics Table
        table_data = []
        headers = ['Category', 'Metric', 'Value', 'Status']
        
        # Add cache metrics
        for key, value in cache_metrics.items():
            category = 'Cache'
            metric = key.replace('_', ' ').title()
            if 'rate' in key:
                val_str = f"{value:.2f}%"
                status = '✅' if value > 90 else '⚠️' if value > 80 else '❌'
            else:
                val_str = str(value)
                status = ''
            table_data.append([category, metric, val_str, status])
        
        # Add pipeline metrics
        for key, value in pipeline_metrics.items():
            category = 'Pipeline'
            metric = key.replace('_', ' ').title()
            if 'ratio' in key or 'rate' in key or 'accuracy' in key:
                val_str = f"{value:.2f}%"
                if 'accuracy' in key:
                    status = '✅' if value > 95 else '⚠️' if value > 90 else '❌'
                else:
                    status = '✅' if value < 20 else '⚠️' if value < 40 else '❌'
            else:
                val_str = f"{value:.3f}" if isinstance(value, float) else str(value)
                if key == 'ipc':
                    status = '✅' if value > 2 else '⚠️' if value > 1 else '❌'
                else:
                    status = ''
            table_data.append([category, metric, val_str, status])
        
        if table_data:
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=headers,
                        fill_color='paleturquoise',
                        align='left',
                        font=dict(size=12)
                    ),
                    cells=dict(
                        values=list(zip(*table_data)),
                        fill_color='lavender',
                        align=['left', 'left', 'right', 'center'],
                        font=dict(size=11)
                    )
                ),
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Performance Analysis Dashboard',
                'font': {'size': 20, 'color': '#2c3e50'},
                'x': 0.5,
                'xanchor': 'center'
            },
            showlegend=False,
            height=1000,
            margin=dict(t=80, b=40, l=60, r=40),
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='white'
        )
        
        # Update axes
        fig.update_xaxes(title_text="Percentage (%)", row=1, col=1)
        fig.update_yaxes(title_text="Cache Type", row=1, col=1)
        fig.update_xaxes(title_text="CPU Usage (%)", row=2, col=1)
        
        # Write to HTML file
        fig.write_html(
            output_file,
            config={'displayModeBar': True, 'displaylogo': False}
        )
        
        print(f"Dashboard created: {output_file}")
    
    def create_simple_dashboard(self, output_file: str = "results/simple_dashboard.html") -> None:
        """Create a simple text-based dashboard if plotly fails"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .metric-group {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px;
        }}
        .metric-name {{
            font-weight: bold;
        }}
        .metric-value {{
            color: #2c3e50;
        }}
        .good {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .bad {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Analysis Dashboard</h1>
        <p>Generated: {self.data.get('timestamp', 'N/A')}</p>
        """
        
        # Add cache metrics
        cache = self.data.get('metrics', {}).get('cache', {})
        if cache:
            html_content += '<div class="metric-group"><h2>Cache Performance</h2>'
            for key, value in cache.items():
                status_class = 'good' if value > 90 else 'warning' if value > 80 else 'bad'
                html_content += f'<div class="metric"><span class="metric-name">{key}:</span>'
                html_content += f'<span class="metric-value {status_class}">{value}%</span></div>'
            html_content += '</div>'
        
        # Add pipeline metrics
        pipeline = self.data.get('metrics', {}).get('pipeline', {})
        if pipeline:
            html_content += '<div class="metric-group"><h2>Pipeline Efficiency</h2>'
            for key, value in pipeline.items():
                html_content += f'<div class="metric"><span class="metric-name">{key}:</span>'
                html_content += f'<span class="metric-value">{value}</span></div>'
            html_content += '</div>'
        
        # Add hotspots
        hotspots = self.data.get('hotspots', [])[:10]
        if hotspots:
            html_content += '<div class="metric-group"><h2>Top Hotspots</h2><ol>'
            for h in hotspots:
                html_content += f'<li>{h["percentage"]}% - {h["function"]}</li>'
            html_content += '</ol></div>'
        
        html_content += """
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Simple dashboard created: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate performance dashboard')
    parser.add_argument('--report', default='results/performance_report.json',
                       help='Performance report JSON file')
    parser.add_argument('--output', default='results/dashboard.html',
                       help='Output HTML file')
    parser.add_argument('--simple', action='store_true',
                       help='Generate simple HTML dashboard without plotly')
    
    args = parser.parse_args()
    
    generator = DashboardGenerator(args.report)
    
    if not generator.load_report():
        sys.exit(1)
    
    if args.simple:
        generator.create_simple_dashboard(args.output)
    else:
        try:
            generator.create_dashboard(args.output)
        except Exception as e:
            print(f"Error creating plotly dashboard: {e}")
            print("Falling back to simple dashboard...")
            generator.create_simple_dashboard(args.output.replace('.html', '_simple.html'))

if __name__ == "__main__":
    main()