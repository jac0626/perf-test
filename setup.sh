#!/bin/bash

# Setup script for performance testing project

echo "🚀 Setting up performance testing project..."

# 检查必要的工具
echo "Checking required tools..."

check_tool() {
    if command -v $1 &> /dev/null; then
        echo "  ✓ $1 found"
        return 0
    else
        echo "  ✗ $1 not found"
        return 1
    fi
}

# 检查编译器
check_tool g++ || {
    echo "Installing g++..."
    sudo apt-get update && sudo apt-get install -y build-essential
}

# 检查 perf
check_tool perf || {
    echo "Installing perf..."
    sudo apt-get install -y linux-tools-common linux-tools-generic linux-tools-$(uname -r)
}

# 检查 Python
check_tool python3 || {
    echo "Installing Python3..."
    sudo apt-get install -y python3 python3-pip
}

# 克隆 FlameGraph 如果不存在
if [ ! -d "FlameGraph" ]; then
    echo "Cloning FlameGraph tools..."
    git clone --depth 1 https://github.com/brendangregg/FlameGraph.git
fi

# 安装 Python 依赖
echo "Installing Python dependencies..."
pip3 install --user pandas matplotlib plotly kaleido

# 设置 perf 权限（可选）
echo ""
echo "To enable perf without sudo, run:"
echo "  echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid"
echo ""

# 编译项目
echo "Building project..."
make clean
make release

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "You can now run:"
    echo "  ./perf_test                    # Run the test program"
    echo "  make perf-record               # Record performance data"
    echo "  make flamegraph                # Generate flame graph"
    echo "  make cache-analysis            # Analyze cache performance"
    echo "  make ipc-analysis              # Analyze IPC"
    echo ""
    echo "Or push to GitHub to trigger automated analysis!"
else
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi