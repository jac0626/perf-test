# Makefile for performance testing project

CXX = g++
CXXFLAGS = -O2 -g -fno-omit-frame-pointer -march=native -std=c++17
LDFLAGS = -lm

# 编译目标
TARGET = perf_test

# 源文件
SOURCES = main.cpp

# 默认目标
all: $(TARGET)

# 编译主程序
$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

# 调试版本
debug: CXXFLAGS = -O0 -g -fno-omit-frame-pointer -std=c++17 -DDEBUG
debug: $(TARGET)

# 优化版本（用于性能测试）
release: CXXFLAGS = -O3 -g -fno-omit-frame-pointer -march=native -std=c++17 -funroll-loops -ftree-vectorize
release: $(TARGET)

# Profile-guided optimization
pgo-generate: CXXFLAGS += -fprofile-generate
pgo-generate: $(TARGET)

pgo-use: CXXFLAGS += -fprofile-use
pgo-use: $(TARGET)

# 清理
clean:
	rm -f $(TARGET) *.o *.gcda *.gcno perf.data perf.data.old

# 运行性能测试
run: $(TARGET)
	./$(TARGET)

# 使用 perf 进行性能分析
perf-record: release
	sudo perf record -F 999 -g --call-graph dwarf ./$(TARGET)

perf-report:
	sudo perf report

# 生成火焰图
flamegraph: perf-record
	sudo perf script > out.perf
	./FlameGraph/stackcollapse-perf.pl out.perf > out.folded
	./FlameGraph/flamegraph.pl out.folded > flamegraph.svg
	@echo "Flame graph generated: flamegraph.svg"

# 收集详细性能指标
perf-stat: release
	sudo perf stat -d -d -d ./$(TARGET)

# 缓存分析
cache-analysis: release
	sudo perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses ./$(TARGET)

# 分支预测分析
branch-analysis: release
	sudo perf stat -e branches,branch-misses ./$(TARGET)

# IPC 分析
ipc-analysis: release
	sudo perf stat -e cycles,instructions ./$(TARGET)

.PHONY: all clean debug release run perf-record perf-report flamegraph perf-stat cache-analysis branch-analysis ipc-analysis