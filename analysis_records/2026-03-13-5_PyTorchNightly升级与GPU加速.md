# Phase 4 完成记录: PyTorch Nightly 升级与 GPU 加速启用

**日期**: 2026-03-13
**时间**: 02:45 - 03:15

---

## 1. 升级概述

**目标**: 解决 PyTorch 2.6 不支持 RTX 5070 Ti (sm_120) 的问题，启用 GPU 加速

**执行命令**:
```bash
# 1. 卸载旧版 PyTorch
pip uninstall torch torchvision torchaudio -y

# 2. 安装 PyTorch Nightly with CUDA 12.8
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

---

## 2. 升级结果

### 版本对比

| 组件 | 旧版本 | 新版本 |
|------|--------|--------|
| PyTorch | 2.6.0+cu126 | **2.12.0.dev20260312+cu128** |
| TorchVision | 0.21.0+cu126 | **0.26.0.dev20260221+cu128** |
| TorchAudio | 2.6.0+cu126 | **2.11.0.dev20260312+cu128** |
| CUDA | 12.6 | **12.8** |
| cuDNN | 90500 | **91002** |

### GPU 支持验证

```
GPU: NVIDIA GeForce RTX 5070 Ti Laptop GPU
Compute capability: 12.0 (sm_120)
Total memory: 11.94 GB
Multi-processors: 46
CUDA available: True
```

**测试结果**: ✅ GPU 矩阵乘法测试通过

---

## 3. DA3 GPU 推理性能对比

### 性能提升

| 指标 | CPU 模式 | GPU 模式 | 加速比 |
|------|----------|----------|--------|
| 单张推理时间 | 1.72s | **0.29s** | **6x** |
| 3张图像总时间 | 5.16s | **0.87s** | **6x** |
| 预处理时间 | 0.02s | 0.06s | - |
| 前向传播时间 | 1.70s | **0.79s** | **2.2x** |

### 输出结果

**深度范围**: [0.07, 7.65] 米
**置信度范围**: [1.00, 6.08]
**输出尺寸**: (378, 504) - DA3 内部处理尺寸

**输出文件**:
```
test_output/da3_official/
├── 0000_depth.png          # 深度可视化
├── 0000_conf.png           # 置信度可视化
├── 0000_depth.npy          # 原始深度数据 [378, 504]
├── 0000_conf.npy           # 原始置信度数据 [378, 504]
├── 0000_extrinsics.npy     # 相机位姿 [3, 4]
├── 0000_intrinsics.npy     # 相机内参 [3, 3]
├── 0000_comparison.png     # 与仿真深度对比
├── 0001_*.png/npy          # 第2帧
└── 0002_*.png/npy          # 第3帧
```

---

## 4. 深度对比分析

### DA3 深度 vs 仿真深度

| 帧 | 仿真深度范围 | DA3 深度范围 | 备注 |
|----|-------------|-------------|------|
| 0000 | [0.00, 0.76] | [0.07, 4.56] | 第一帧有光晕问题 |
| 0001 | [3.71, inf] | [0.19, 7.07] | 正常帧 |
| 0002 | [3.71, inf] | [0.19, 7.65] | 正常帧 |

**观察**:
- DA3 深度范围 [0.07, 7.65] 米，与极地场景尺度一致
- 仿真深度使用 UE5 单位（可能是 cm 或 m），需要进一步对齐
- DA3 提供更丰富的近处细节（0.07m 近距离）

---

## 5. 已知问题与限制

### xformers 兼容性

**警告**:
```
xformers 0.0.29.post3 requires torch==2.6.0,
but you have torch 2.12.0.dev20260312+cu128
```

**影响**:
- xformers 是可选优化库，用于加速 attention 计算
- DA3 仍能正常工作，只是可能无法达到最高性能
- 可以等待 xformers nightly 版本发布

**解决方案**:
```bash
# 暂时不安装，或从源码编译
# 未来可用:
pip install --pre xformers --index-url https://download.pytorch.org/whl/nightly/cu128
```

### gsplat 可选依赖

**警告**:
```
Dependency `gsplat` is required for rendering 3DGS
```

**影响**:
- gsplat 仅用于 3D Gaussian Splatting 渲染
- 深度估计功能不受影响
- Phase 5 需要时再安装

---

## 6. 生成的文件

### 测试脚本

| 脚本 | 用途 | 状态 |
|------|------|------|
| `tools/verify_gpu_support.py` | GPU 支持验证 | ✅ 新增 |
| `tools/test_da3_official.py` | GPU 版本 DA3 测试 | ✅ 已验证 |
| `tools/test_da3_cpu.py` | CPU 版本 DA3 测试 | ✅ 备用 |

### 输出数据

```
test_output/
├── da3_cpu/                # CPU 测试结果
│   ├── 0000_depth.png
│   └── ...
└── da3_official/           # GPU 测试结果
    ├── 0000_depth.png
    ├── 0000_conf.png
    ├── 0000_comparison.png
    ├── 0001_*.png
    └── 0002_*.png
```

---

## 7. 下一步建议

### 短期 (今天)

1. **批量处理所有 8 张图像**
   - 使用 GPU 版本处理完整数据集
   - 对比 DA3 深度与仿真深度

2. **深度对齐与融合**
   - 分析 DA3 深度与仿真深度的尺度关系
   - 实现深度对齐算法

3. **位姿预测验证**
   - 对比 DA3 预测的 extrinsics 与仿真 poses.json
   - 评估位姿预测精度

### 中期 (本周)

4. **SAM 3 分割部署**
   - 等待 Hugging Face 权限批准
   - 实现海冰实例分割

5. **数据整合**
   - 融合深度、分割、位姿数据
   - 生成 Phase 5 (3DGS) 输入格式

### 长期 (下周)

6. **3DGS 初始化**
   - 使用 DA3 输出作为 3DGS 初始参数
   - 训练 3D Gaussian Splatting 模型

---

## 8. 参考命令

```bash
# 验证 GPU 支持
python tools/verify_gpu_support.py

# GPU 推理测试
python tools/test_da3_official.py

# 查看 PyTorch 版本
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

---

## 9. 关键发现

### DA3 输出格式确认

```python
prediction.depth          # [N, H, W] 深度图 (米)
prediction.conf           # [N, H, W] 置信度
prediction.extrinsics     # [N, 3, 4] 相机位姿 (OpenCV format)
prediction.intrinsics     # [N, 3, 3] 相机内参
prediction.processed_images  # [N, H, W, 3] 预处理后的图像
```

### 性能优化效果

- **GPU 加速**: 6 倍速度提升 (1.72s → 0.29s/张)
- **批处理能力**: 可同时处理多张图像
- **实时性**: 接近实时处理速度 (~3 FPS)

---

**完成时间**: 2026-03-13 03:15
**状态**: ✅ PyTorch Nightly 升级完成，GPU 加速已启用
