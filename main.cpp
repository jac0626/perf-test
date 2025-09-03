#include <iostream>
#include <vector>
#include <chrono>
#include <cstdint>
#include <numeric> // For std::iota

// 必须包含此头文件以使用 SVE 内联函数
#include <arm_sve.h>

/**
 * @brief 使用 SVE 指令执行 SAXPY 操作 (Y = a * X + Y)
 * 
 * @param a 标量乘数
 * @param x 输入向量 X
 * @param y 输入/输出向量 Y
 */
void sve_saxpy(float a, const std::vector<float>& x, std::vector<float>& y) {
    // 确保向量大小相同
    if (x.size() != y.size()) {
        throw std::runtime_error("Vector sizes must be equal.");
    }
    
    uint64_t n = x.size();
    const float* x_ptr = x.data();
    float* y_ptr = y.data();

    // SVE 的循环方式：
    // 使用一个谓词(predicate)来处理可能不是向量长度整数倍的数组尾部
    for (uint64_t i = 0; i < n; ) {
        // svwhilelt_b32: 创建一个谓词(pg)，对于 i+lane < n 的通道(lane)为 true
        // 这有效地为循环的最后一次迭代创建了一个掩码
        svbool_t pg = svwhilelt_b32(i, n);
        
        // svld1: 根据谓词 pg 从内存加载数据到向量寄存器
        svfloat32_t vec_x = svld1_f32(pg, x_ptr + i);
        svfloat32_t vec_y = svld1_f32(pg, y_ptr + i);
        
        // svmad_f32_z: 核心计算！执行 "multiply-add" 操作。
        // result = (a * vec_x) + vec_y
        // _z 后缀表示 "zeroing"，即谓词为 false 的通道将被置为 0
        svfloat32_t result = svmad_f32_z(pg, svdup_n_f32(a), vec_x, vec_y);
        
        // svst1: 根据谓词 pg 将结果写回内存
        svst1_f32(pg, y_ptr + i, result);
        
        // svcntw(): 获取当前硬件上 SVE 向量寄存器可以容纳的 32-bit 元素数量。
        // 这是 "Scalable" 的关键！代码无需硬编码向量宽度。
        i += svcntw();
    }
}

int main() {
    // ================== 1. 参数设置 ==================
    const size_t VECTOR_SIZE = 10000000; // 1000 万个元素
    const float a = 2.5f;
    const int TARGET_DURATION_SECONDS = 120; // 目标运行时间：2分钟

    std::cout << "SVE SAXPY Benchmark" << std::endl;
    std::cout << "---------------------" << std::endl;
    std::cout << "Target duration: " << TARGET_DURATION_SECONDS << " seconds" << std::endl;
    std::cout << "Vector size:     " << VECTOR_SIZE << " elements" << std::endl;
    
    // 打印当前 SVE 向量长度（以字节为单位）
    std::cout << "SVE vector length: " << svcntb() * 8 << " bits (" << svcntb() << " bytes)" << std::endl;
    std::cout << "---------------------" << std::endl;


    // ================== 2. 数据初始化 ==================
    std::cout << "Initializing vectors..." << std::endl;
    std::vector<float> x(VECTOR_SIZE);
    std::vector<float> y(VECTOR_SIZE);
    std::vector<float> y_original(VECTOR_SIZE);

    // 用一些值填充向量
    std::iota(x.begin(), x.end(), 0.0f); // x = {0.0, 1.0, 2.0, ...}
    for(size_t i = 0; i < VECTOR_SIZE; ++i) {
        y[i] = static_cast<float>(VECTOR_SIZE - i);
    }
    y_original = y; // 保存 y 的初始状态，以便每次循环重置

    std::cout << "Initialization complete. Starting computation." << std::endl;


    // ================== 3. 主计算循环 ==================
    auto start_time = std::chrono::high_resolution_clock::now();
    long long iterations = 0;
    
    while (true) {
        // 每次迭代前重置 y，以确保计算负载恒定
        y = y_original;

        // 执行核心计算
        sve_saxpy(a, x, y);

        iterations++;

        auto current_time = std::chrono::high_resolution_clock::now();
        auto elapsed_seconds = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time).count();

        // 每秒打印一次进度
        if (iterations % 10 == 0) { // 减少打印频率
            std::cout << "\rElapsed time: " << elapsed_seconds << "s, Iterations: " << iterations << std::flush;
        }

        if (elapsed_seconds >= TARGET_DURATION_SECONDS) {
            break;
        }
    }
    
    std::cout << std::endl << "Computation finished." << std::endl;


    // ================== 4. 结果验证和报告 ==================
    auto end_time = std::chrono::high_resolution_clock::now();
    auto total_duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count();
    
    std::cout << "---------------------" << std::endl;
    std::cout << "Total iterations: " << iterations << std::endl;
    std::cout << "Total time:       " << total_duration / 1000000.0 << " seconds" << std::endl;
    double gflops = (2.0 * VECTOR_SIZE * iterations) / (total_duration / 1000000.0) / 1e9;
    std::cout << "Performance:      " << gflops << " GFLOPS" << std::endl;
    
    // 抽样验证结果是否正确
    std::cout << "\nVerifying a few results..." << std::endl;
    size_t indices_to_check[] = {0, 1, 42, VECTOR_SIZE / 2, VECTOR_SIZE - 1};
    for(size_t idx : indices_to_check) {
        float expected = a * x[idx] + y_original[idx];
        std::cout << "y[" << idx << "]: Expected=" << expected << ", Got=" << y[idx] << std::endl;
    }

    return 0;
}
