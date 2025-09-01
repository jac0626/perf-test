// main.cpp - 性能测试程序
// 包含多种计算模式以展示不同的性能特征

#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <cstring>

// 矩阵乘法 - CPU密集型，测试流水线和缓存
void matrix_multiply(int size = 256) {
    std::vector<std::vector<double>> a(size, std::vector<double>(size));
    std::vector<std::vector<double>> b(size, std::vector<double>(size));
    std::vector<std::vector<double>> c(size, std::vector<double>(size, 0.0));
    
    // 初始化矩阵
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 1.0);
    
    for (int i = 0; i < size; ++i) {
        for (int j = 0; j < size; ++j) {
            a[i][j] = dis(gen);
            b[i][j] = dis(gen);
        }
    }
    
    // 矩阵乘法 - 不同的循环顺序影响缓存性能
    for (int i = 0; i < size; ++i) {
        for (int k = 0; k < size; ++k) {
            double temp = a[i][k];
            for (int j = 0; j < size; ++j) {
                c[i][j] += temp * b[k][j];
            }
        }
    }
}

// 随机内存访问 - 测试缓存未命中
void random_memory_access(size_t size = 64 * 1024 * 1024) {
    std::vector<char> memory(size);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<size_t> dis(0, size - 1);
    
    // 预热
    std::fill(memory.begin(), memory.end(), 0);
    
    // 随机访问 - 导致大量缓存未命中
    volatile char sum = 0;
    for (int i = 0; i < 10000000; ++i) {
        size_t index = dis(gen);
        sum += memory[index];
        memory[index] = sum;
    }
}

// 顺序内存访问 - 测试缓存友好的访问模式
void sequential_memory_access(size_t size = 64 * 1024 * 1024) {
    std::vector<char> memory(size);
    
    // 顺序写入
    for (size_t i = 0; i < size; ++i) {
        memory[i] = static_cast<char>(i & 0xFF);
    }
    
    // 顺序读取并计算
    volatile long long sum = 0;
    for (int iter = 0; iter < 10; ++iter) {
        for (size_t i = 0; i < size; ++i) {
            sum += memory[i];
        }
    }
}

// 分支密集型代码 - 测试分支预测
void branch_intensive(int iterations = 50000000) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 100);
    
    volatile long long sum = 0;
    
    // 可预测的分支
    for (int i = 0; i < iterations; ++i) {
        if (i % 2 == 0) {
            sum += i;
        } else {
            sum -= i;
        }
    }
    
    // 难以预测的分支
    for (int i = 0; i < iterations / 10; ++i) {
        int random_val = dis(gen);
        if (random_val < 30) {
            sum += random_val;
        } else if (random_val < 60) {
            sum *= 2;
        } else if (random_val < 90) {
            sum -= random_val;
        } else {
            sum /= 2;
        }
    }
}

// 浮点密集计算 - 测试浮点单元
void floating_point_intensive(int iterations = 10000000) {
    volatile double result = 1.0;
    
    for (int i = 1; i < iterations; ++i) {
        double x = static_cast<double>(i);
        result += std::sin(x) * std::cos(x);
        result += std::sqrt(x) / std::log(x + 1);
        result += std::exp(-x / 1000000.0);
    }
}

// 递归函数 - 测试调用栈和函数调用开销
long long fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

void recursive_workload() {
    volatile long long sum = 0;
    for (int i = 30; i < 40; ++i) {
        sum += fibonacci(i);
    }
}

// 向量化友好的代码
void vectorizable_loop(size_t size = 10000000) {
    std::vector<float> a(size), b(size), c(size);
    
    // 初始化
    for (size_t i = 0; i < size; ++i) {
        a[i] = static_cast<float>(i);
        b[i] = static_cast<float>(i * 2);
    }
    
    // 向量化友好的循环
    for (int iter = 0; iter < 100; ++iter) {
        for (size_t i = 0; i < size; ++i) {
            c[i] = a[i] * 2.5f + b[i] * 3.7f;
        }
        
        // 防止优化掉
        volatile float sum = std::accumulate(c.begin(), c.end(), 0.0f);
    }
}

// 主函数
int main(int argc, char* argv[]) {
    using namespace std::chrono;
    
    auto start_time = high_resolution_clock::now();
    auto target_duration = minutes(2); // 运行2分钟
    
    std::cout << "Starting performance test workload..." << std::endl;
    std::cout << "Target duration: 2 minutes" << std::endl;
    
    int iteration = 0;
    while (duration_cast<seconds>(high_resolution_clock::now() - start_time) < target_duration) {
        iteration++;
        
        // 记录每个阶段
        auto phase_start = high_resolution_clock::now();
        
        std::cout << "\nIteration " << iteration << ":" << std::endl;
        
        // 1. 矩阵乘法
        std::cout << "  - Matrix multiplication..." << std::flush;
        matrix_multiply(200);
        std::cout << " done" << std::endl;
        
        // 2. 随机内存访问
        std::cout << "  - Random memory access..." << std::flush;
        random_memory_access(32 * 1024 * 1024);
        std::cout << " done" << std::endl;
        
        // 3. 顺序内存访问
        std::cout << "  - Sequential memory access..." << std::flush;
        sequential_memory_access(32 * 1024 * 1024);
        std::cout << " done" << std::endl;
        
        // 4. 分支密集
        std::cout << "  - Branch intensive..." << std::flush;
        branch_intensive(10000000);
        std::cout << " done" << std::endl;
        
        // 5. 浮点计算
        std::cout << "  - Floating point operations..." << std::flush;
        floating_point_intensive(5000000);
        std::cout << " done" << std::endl;
        
        // 6. 递归
        std::cout << "  - Recursive calls..." << std::flush;
        recursive_workload();
        std::cout << " done" << std::endl;
        
        // 7. 向量化
        std::cout << "  - Vectorizable loops..." << std::flush;
        vectorizable_loop(5000000);
        std::cout << " done" << std::endl;
        
        auto phase_duration = duration_cast<milliseconds>(high_resolution_clock::now() - phase_start);
        std::cout << "  Iteration time: " << phase_duration.count() << " ms" << std::endl;
        
        // 检查是否超时
        auto elapsed = duration_cast<seconds>(high_resolution_clock::now() - start_time);
        std::cout << "  Total elapsed: " << elapsed.count() << " seconds" << std::endl;
    }
    
    auto total_duration = duration_cast<seconds>(high_resolution_clock::now() - start_time);
    std::cout << "\nPerformance test completed!" << std::endl;
    std::cout << "Total iterations: " << iteration << std::endl;
    std::cout << "Total duration: " << total_duration.count() << " seconds" << std::endl;
    
    return 0;
}