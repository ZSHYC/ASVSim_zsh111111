# InstantSplat + RTX 50 系显卡完整配置指南

**文档版本**: v2.0
**创建时间**: 2026-03-15
**适用平台**: Windows 10/11
**适用显卡**: NVIDIA RTX 50 系列 (5070/5080/5090)
**CUDA版本**: 12.8
**Python版本**: 3.10.13
**PyTorch版本**: 2.7.0+cu128

---

## 目录

1. [前置知识](#1-前置知识)
2. [环境准备](#2-环境准备)
3. [CUDA Toolkit 12.8 安装](#3-cuda-toolkit-128-安装)
4. [Conda 环境创建](#4-conda-环境创建)
5. [PyTorch 2.7 安装](#5-pytorch-27-安装)
6. [InstantSplat 依赖安装](#6-instantsplat-依赖安装)
7. [CUDA 子模块编译](#7-cuda-子模块编译)
8. [RTX 50 系特殊修改](#8-rtx-50-系特殊修改)
9. [模型下载](#9-模型下载)
10. [验证安装](#10-验证安装)
11. [故障排除](#11-故障排除)

---

## 1. 前置知识

### 1.1 为什么 RTX 50 系需要特殊配置？

#### 计算能力 (Compute Capability)

NVIDIA GPU 使用**计算能力**（Compute Capability）来标识其架构版本：

| 显卡系列 | 架构名称 | 计算能力 | 最低 CUDA 版本 |
|---------|---------|---------|--------------|
| RTX 30 系 | Ampere | sm_86 | CUDA 11.1+ |
| RTX 40 系 | Ada Lovelace | sm_89 | CUDA 11.8+ |
| **RTX 50 系** | **Blackwell** | **sm_120** | **CUDA 12.8+** |

#### 关键问题

RTX 5070/5080/5090 使用 **sm_120** 计算能力，这个架构在 **CUDA 12.8** 中才首次加入支持。

如果你使用 CUDA 12.1 + PyTorch 2.5，会出现以下错误：

```
NVIDIA GeForce RTX 5070 with CUDA capability sm_120 is not compatible
with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_70 sm_75 sm_80 sm_86 sm_89 sm_90.
```

**翻译**：你的 PyTorch 只认识老架构（sm_50 到 sm_90），不认识新的 sm_120。

### 1.2 什么是 CUDA Toolkit？

CUDA Toolkit 是 NVIDIA 提供的**完整开发工具包**，包含：

| 组件 | 作用 | 类比 |
|------|------|------|
| **nvcc** | CUDA 编译器 | 就像 C++ 的 gcc/clang |
| **CUDA Runtime** | 运行时库 | 就像 Java 的 JRE |
| **cuDNN** | 深度神经网络库 | PyTorch/TensorFlow 的底层加速 |
| **头文件和库** | 编译时需要的文件 | 就像 C++ 的 .h 和 .lib |

#### 为什么需要 nvcc？

InstantSplat 包含三个需要编译的 CUDA 扩展：

1. **simple-knn** - K近邻搜索加速
2. **diff-gaussian-rasterization** - 可微高斯光栅化（核心）
3. **fused-ssim** - 融合 SSIM 损失函数

这些扩展包含 `.cu` 文件（CUDA C++ 代码），必须用 **nvcc** 编译成 GPU 能执行的二进制代码。

### 1.3 nvidia-smi 显示的 CUDA 版本 vs CUDA Toolkit 版本

```bash
nvidia-smi
```

输出示例：
```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 591.74                 Driver Version: 591.74         CUDA Version: 13.1     |
+-----------------------------------------------------------------------------------------+
```

**这里的 "CUDA Version: 13.1" 是什么意思？**

这是驱动**支持的最高 CUDA 版本**，不是已安装的 CUDA Toolkit 版本。

- 驱动 591.74 可以运行 CUDA 13.1 及以下的所有程序
- 但你仍然需要**单独安装 CUDA Toolkit** 来获得 nvcc 编译器
- 我们安装 CUDA 12.8，驱动完全兼容

### 1.4 PyTorch 版本与 CUDA 版本的对应关系

| PyTorch 版本 | 支持的最高 CUDA | 是否支持 sm_120 |
|-------------|----------------|---------------|
| 2.4.x | CUDA 12.1 | ❌ 不支持 |
| 2.5.x | CUDA 12.1 | ❌ 不支持 |
| 2.6.x | CUDA 12.4 | ❌ 不支持 |
| **2.7.x** | **CUDA 12.8** | ✅ **支持** |

PyTorch 2.7（2025年3月发布）是第一个原生支持 RTX 50 系的版本。

---

## 2. 环境准备

### 2.1 检查显卡驱动

```bash
nvidia-smi
```

**预期输出**：
- Driver Version: 550.xx 或更高（推荐 570+）
- GPU 显示为 NVIDIA GeForce RTX 5070/5080/5090

**如果驱动过旧**：
访问 https://www.nvidia.cn/drivers/ 下载最新驱动。

### 2.2 检查 Conda 安装

```bash
conda --version
```

**预期输出**：
```
conda 24.x.x
```

**如果未安装**：
下载 Miniconda：https://docs.anaconda.com/miniconda/

### 2.3 检查 Git 安装

```bash
git --version
```

**预期输出**：
```
git version 2.40+
```

---

## 3. CUDA Toolkit 12.8 安装

### 3.1 下载 CUDA Toolkit 12.8

**官方下载地址**：
```
https://developer.nvidia.com/cuda-downloads
```

**Windows 直接下载链接**：
```
https://developer.download.nvidia.com/compute/cuda/12.8.0/local_installers/cuda_12.8.0_571.96_windows.exe
```

### 3.2 安装步骤详解

#### 步骤 1：运行安装程序

双击下载的 `cuda_12.8.0_571.96_windows.exe`

#### 步骤 2：选择安装选项

选择 **"自定义（高级）"**（不要选"精简"）

**原因**：
- "精简"安装可能缺少开发所需的组件
- 自定义安装可以确保所有工具都装上

#### 步骤 3：自定义安装选项

**必须勾选的组件**：

| 组件 | 是否必须 | 说明 |
|------|---------|------|
| CUDA > Development > Compiler | ✅ 必须 | nvcc 编译器 |
| CUDA > Development > CUDA Visual Studio Integration | ✅ 必须 | VS 集成（如果用 VS） |
| CUDA > Runtime > CUDA Runtime | ✅ 必须 | 运行时库 |
| CUDA > Libraries | ✅ 必须 | CUDA 库文件 |
| Driver components | ⚠️ 可选 | 如果驱动已是最新版可不选 |

**可以取消的组件**（节省空间）：
- GeForce Experience
- PhysX
- HD Audio
- Documentation
- Samples（示例代码，可选）

#### 步骤 4：选择安装路径

**推荐路径**：
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
```

**不建议更改路径**，因为：
1. PyTorch 会自动搜索这个路径
2. 大多数教程和脚本都假设这个路径
3. 避免中文路径导致的编译问题

#### 步骤 5：完成安装

等待安装完成，可能需要几分钟。

### 3.3 验证 CUDA Toolkit 安装

打开新的终端窗口（**必须新开窗口**），运行：

```bash
nvcc --version
```

**预期输出**：
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2024 NVIDIA Corporation
Built on Tue_Oct_29_23:18:44_Pacific_Daylight_Time_2024
Cuda compilation tools, release 12.8, V12.8.89
```

**关键点**：显示 `release 12.8` 表示安装成功。

### 3.4 设置环境变量

#### 自动设置

CUDA 安装程序通常会自动添加环境变量，检查是否成功：

```bash
echo %CUDA_HOME%
```

**预期输出**：
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
```

#### 手动设置（如果自动设置失败）

**步骤 1**：打开环境变量设置
1. 右键"此电脑" → 属性
2. 高级系统设置 → 环境变量

**步骤 2**：添加系统变量

新建系统变量：
- 变量名：`CUDA_HOME`
- 变量值：`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8`

**步骤 3**：修改 Path 变量

在系统变量 Path 中添加：
```
%CUDA_HOME%\bin
```

**步骤 4**：验证

新开终端窗口，运行：
```bash
python -c "import os; print(os.environ.get('CUDA_HOME'))"
```

应输出 CUDA 12.8 的路径。

---

## 4. Conda 环境创建

### 4.1 创建 Python 3.10.13 环境

```bash
conda create -n instantsplat python=3.10.13 cmake=3.14.0 -y
```

**参数说明**：
- `-n instantsplat`：环境名称
- `python=3.10.13`：Python 版本（InstantSplat 推荐 3.10）
- `cmake=3.14.0`：CMake 版本（编译子模块需要）

**为什么选择 Python 3.10？**
- PyTorch 2.7 官方支持 Python 3.9-3.12
- 3.10 是稳定且兼容性好的版本
- 许多深度学习库优先支持 3.10

### 4.2 激活环境

```bash
conda activate instantsplat
```

**验证**：
```bash
python --version
```

预期输出：`Python 3.10.13`

### 4.3 安装基础工具

```bash
pip install --upgrade pip setuptools wheel
```

**作用**：
- `pip`：Python 包管理器
- `setuptools`：构建 Python 包的工具
- `wheel`：二进制包格式，加快安装速度

---

## 5. PyTorch 2.7 安装

### 5.1 安装 PyTorch 2.7 with CUDA 12.8

```bash
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
```

**参数详解**：

| 参数 | 说明 |
|------|------|
| `torch==2.7.0` | PyTorch 主库，版本 2.7.0 |
| `torchvision==0.22.0` | PyTorch 视觉库，与 torch 2.7 配套 |
| `--index-url https://download.pytorch.org/whl/cu128` | 指定 CUDA 12.8 版本的源 |

**为什么是 cu128？**
- `cu128` = CUDA 12.8
- PyTorch 官网提供多个 CUDA 版本：`cu118` (CUDA 11.8)、`cu121` (CUDA 12.1)、`cu124` (CUDA 12.4)、`cu128` (CUDA 12.8)
- RTX 50 系必须使用 `cu128`

### 5.2 验证 PyTorch 安装

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

**预期输出**：
```
PyTorch: 2.7.0+cu128
CUDA available: True
CUDA version: 12.8
GPU: NVIDIA GeForce RTX 5070 Ti
```

**关键检查点**：
1. PyTorch 版本显示 `2.7.0+cu128`（不是 cu121）
2. `CUDA available: True`（GPU 可用）
3. GPU 名称正确显示

### 5.3 验证 PyTorch 支持 sm_120

```bash
python -c "import torch; print('CUDA capabilities:', torch.cuda.get_device_capability())"
```

**预期输出**：
```
CUDA capabilities: (12, 0)
```

这表示 PyTorch 正确识别了你的 GPU 计算能力为 sm_120。

---

## 6. InstantSplat 依赖安装

### 6.1 进入 InstantSplat 目录

```bash
cd C:\Users\zsh\Desktop\ASVSim_zsh\InstantSplat
```

### 6.2 安装 Python 依赖

```bash
pip install -r requirements.txt
```

**requirements.txt 主要内容**：

| 包名 | 用途 |
|------|------|
| `torch` / `torchvision` | 深度学习框架（已安装） |
| `roma` | 旋转矩阵运算库 |
| `gradio` | Web 界面 |
| `open3d` | 3D 可视化 |
| `trimesh` | 网格处理 |
| `plyfile` | PLY 文件读写 |
| `huggingface-hub` | 模型下载 |
| `scipy` | 科学计算 |
| `scikit-learn` | 机器学习工具 |
| `pillow` | 图像处理 |
| `tqdm` | 进度条 |
| `matplotlib` | 绘图 |

### 6.3 安装额外依赖

```bash
pip install einops transformers
```

**作用**：
- `einops`：张量操作工具（MASt3R 需要）
- `transformers`：Hugging Face 模型库（MASt3R 需要）

---

## 7. CUDA 子模块编译

### 7.1 什么是子模块？

InstantSplat 使用 Git 子模块引入三个关键组件：

```
InstantSplat/
├── submodules/
│   ├── simple-knn/          # K近邻搜索
│   ├── diff-gaussian-rasterization/  # 高斯光栅化
│   └── fused-ssim/          # SSIM 损失函数
```

**为什么需要编译？**

这些模块包含 `.cu` 文件（CUDA C++ 代码），需要：
1. 用 `nvcc` 编译成 GPU 二进制代码
2. 生成 Python 可调用的接口
3. 针对特定 GPU 架构（sm_120）优化

### 7.2 编译前准备

#### 确保环境变量正确

```bash
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set PATH=%CUDA_HOME%\bin;%PATH%
```

#### 验证 nvcc 可用

```bash
nvcc --version
```

### 7.3 安装 simple-knn

```bash
pip install submodules/simple-knn --no-build-isolation
```

**参数说明**：
- `--no-build-isolation`：**关键参数**
- 原因：`setup.py` 需要导入 `torch`，但隔离构建环境里没有 torch
- 不加这个参数会报错：`ModuleNotFoundError: No module named 'torch'`

**编译过程说明**：

1. pip 读取 `submodules/simple-knn/setup.py`
2. `setup.py` 调用 `torch.utils.cpp_extension` 来编译 CUDA 代码
3. `cpp_extension` 使用 `nvcc` 编译 `.cu` 文件
4. 生成 Python 扩展模块（`.pyd` 文件在 Windows 上）
5. 安装到 Python 环境中

**预期输出**：
```
Successfully installed simple-knn-0.0.0
```

### 7.4 安装 diff-gaussian-rasterization

```bash
pip install submodules/diff-gaussian-rasterization --no-build-isolation
```

**这个模块的作用**：
- 将 3D 高斯点投影到 2D 图像平面
- 计算光栅化（将点变成像素）
- 支持梯度回传（可微分，用于训练）

**预期输出**：
```
Successfully installed diff-gaussian-rasterization-0.0.0
```

### 7.5 安装 fused-ssim

```bash
pip install submodules/fused-ssim --no-build-isolation
```

**这个模块的作用**：
- 计算 SSIM（结构相似性）损失函数
- 融合 CUDA 实现，比 Python 实现快 10 倍以上
- 用于评估渲染图像与真实图像的相似度

**预期输出**：
```
Successfully installed fused-ssim-0.0.0
```

### 7.6 编译失败的常见原因

#### 错误 1：CUDA_HOME 未设置

```
OSError: CUDA_HOME environment variable is not set.
Please set it to your CUDA install root.
```

**解决**：
```bash
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
```

#### 错误 2：找不到 cl.exe（Visual C++ 编译器）

```
error: Microsoft Visual C++ 14.0 or greater is required.
Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**解决**：
1. 下载 Visual Studio Build Tools：https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 安装 "使用 C++ 的桌面开发" 工作负载
3. 或安装完整版 Visual Studio 2022 Community

#### 错误 3：nvcc 与 Visual Studio 版本不兼容

```
error: unsupported Microsoft Visual Studio version
```

**解决**：
- CUDA 12.8 支持 Visual Studio 2017-2022
- 确保安装了较新版本的 VS

---

## 8. RTX 50 系特殊修改

### 8.1 为什么需要修改？

RTX 50 系（Blackwell 架构）太新了，InstantSplat 的某些 CUDA 代码可能使用了旧的语法或缺少必要的头文件。

### 8.2 修改 simple-knn.cu

#### 问题

`simple-knn` 模块使用了 `FLT_MAX` 宏，但在某些 CUDA 版本中需要显式包含头文件。

#### 修改步骤

**步骤 1**：打开文件

```
InstantSplat/submodules/simple-knn/simple-knn.cu
```

**步骤 2**：在文件顶部添加头文件

找到文件开头，在第一个 `#include` 之前添加：

```cpp
#include <float.h>
```

修改后的文件开头应该像这样：

```cpp
#include <float.h>  // 添加这一行
#include "simple_knn.h"
#include <cuda_runtime.h>
#include <cuda_runtime_api.h>
// ... 其他代码
```

**步骤 3**：保存文件

**步骤 4**：重新编译

```bash
pip install submodules/simple-knn --no-build-isolation --force-reinstall
```

#### 原理说明

- `FLT_MAX` 定义在 `<float.h>` 中，表示 float 类型的最大值
- 旧版 CUDA 可能隐式包含了这个头文件
- 新版 CUDA 或某些编译器配置需要显式包含
- RTX 50 系的编译器更严格，所以需要显式声明

### 8.3 验证所有子模块正常工作

```bash
python -c "
from submodules.diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
from submodules.simple_knn._C import distCUDA2
from submodules.fused_ssim import ssim
print('✓ simple-knn 导入成功')
print('✓ diff-gaussian-rasterization 导入成功')
print('✓ fused-ssim 导入成功')
print('✓ 所有子模块安装完成！')
"
```

**预期输出**：
```
✓ simple-knn 导入成功
✓ diff-gaussian-rasterization 导入成功
✓ fused-ssim 导入成功
✓ 所有子模块安装完成！
```

---

## 9. 模型下载

### 9.1 创建模型目录

```bash
mkdir -p mast3r/checkpoints
```

### 9.2 下载 MASt3R 预训练模型

**方法 1：使用 curl（Windows 10+ 自带）**

```bash
curl -o mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth ^
  https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth
```

**方法 2：使用浏览器下载**

直接访问：
```
https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth
```

下载完成后移动到 `mast3r/checkpoints/` 目录。

**方法 3：使用 Python**

```bash
python -c "
from huggingface_hub import hf_hub_download
import os

os.makedirs('mast3r/checkpoints', exist_ok=True)
filepath = hf_hub_download(
    repo_id='naver/MASt3R',
    filename='MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth',
    local_dir='mast3r/checkpoints',
    local_dir_use_symlinks=False
)
print(f'Model downloaded to: {filepath}')
"
```

### 9.3 验证模型下载

```bash
dir mast3r\checkpoints\
```

**预期输出**：
```
MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth    2,447,793 KB
```

文件大小约 2.4GB。

---

## 10. 验证安装

### 10.1 完整功能验证脚本

创建 `verify_installation.py`：

```python
import sys
import torch
import torchvision

def check_pytorch():
    print("=" * 60)
    print("1. PyTorch 检查")
    print("=" * 60)
    print(f"PyTorch 版本: {torch.__version__}")
    print(f"CUDA 可用: {torch.cuda.is_available()}")
    print(f"CUDA 版本: {torch.version.cuda}")

    if torch.cuda.is_available():
        print(f"GPU 数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            cap = torch.cuda.get_device_capability(i)
            print(f"  计算能力: sm_{cap[0]}{cap[1]}")
    else:
        print("❌ CUDA 不可用！")
        return False
    return True

def check_submodules():
    print("\n" + "=" * 60)
    print("2. 子模块检查")
    print("=" * 60)

    try:
        from submodules.diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
        print("✓ diff-gaussian-rasterization")
    except ImportError as e:
        print(f"❌ diff-gaussian-rasterization: {e}")
        return False

    try:
        from submodules.simple_knn._C import distCUDA2
        print("✓ simple-knn")
    except ImportError as e:
        print(f"❌ simple-knn: {e}")
        return False

    try:
        from submodules.fused_ssim import ssim
        print("✓ fused-ssim")
    except ImportError as e:
        print(f"❌ fused-ssim: {e}")
        return False

    return True

def check_model():
    print("\n" + "=" * 60)
    print("3. 模型文件检查")
    print("=" * 60)
    import os
    model_path = "mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth"
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✓ MASt3R 模型存在 ({size_mb:.1f} MB)")
        return True
    else:
        print(f"❌ MASt3R 模型不存在: {model_path}")
        return False

def check_cuda_kernels():
    print("\n" + "=" * 60)
    print("4. CUDA 内核测试")
    print("=" * 60)

    try:
        # 测试 simple-knn
        import torch
        from submodules.simple_knn._C import distCUDA2

        # 创建随机点云
        points = torch.randn(100, 3).cuda()
        mean_dists = distCUDA2(points)
        print(f"✓ simple-knn CUDA 内核工作正常")
        print(f"  测试点云: {points.shape}")
        print(f"  平均距离: {mean_dists.mean().item():.4f}")

        return True
    except Exception as e:
        print(f"❌ CUDA 内核测试失败: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("InstantSplat 安装验证")
    print("=" * 60)

    results = []
    results.append(("PyTorch", check_pytorch()))
    results.append(("子模块", check_submodules()))
    results.append(("模型文件", check_model()))
    results.append(("CUDA 内核", check_cuda_kernels()))

    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n🎉 所有检查通过！InstantSplat 安装成功！")
        return 0
    else:
        print("\n⚠️ 部分检查未通过，请查看上方错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

运行验证：

```bash
python verify_installation.py
```

**预期输出**：
```
============================================================
InstantSplat 安装验证
============================================================
============================================================
1. PyTorch 检查
============================================================
PyTorch 版本: 2.7.0+cu128
CUDA 可用: True
CUDA 版本: 12.8
GPU 数量: 1
GPU 0: NVIDIA GeForce RTX 5070 Ti
  计算能力: sm_120

============================================================
2. 子模块检查
============================================================
✓ diff-gaussian-rasterization
✓ simple-knn
✓ fused-ssim

============================================================
3. 模型文件检查
============================================================
✓ MASt3R 模型存在 (2447.8 MB)

============================================================
4. CUDA 内核测试
============================================================
✓ simple-knn CUDA 内核工作正常
  测试点云: torch.Size([100, 3])
  平均距离: 1.2345

============================================================
验证结果总结
============================================================
PyTorch: ✅ 通过
子模块: ✅ 通过
模型文件: ✅ 通过
CUDA 内核: ✅ 通过

🎉 所有检查通过！InstantSplat 安装成功！
```

---

## 11. 故障排除

### 11.1 安装检查清单

如果验证失败，按以下顺序检查：

- [ ] **Conda 环境激活**：`conda activate instantsplat`
- [ ] **CUDA_HOME 设置**：`echo %CUDA_HOME%` 显示正确路径
- [ ] **nvcc 可用**：`nvcc --version` 显示 12.8
- [ ] **PyTorch CUDA 支持**：`python -c "import torch; print(torch.version.cuda)"` 输出 12.8
- [ ] **Visual C++ 编译器**：已安装 VS Build Tools
- [ ] **模型文件存在**：`dir mast3r\checkpoints\` 显示模型

### 11.2 常见错误及解决

#### 错误：CUDA out of memory

```
RuntimeError: CUDA out of memory.
```

**解决**：
- 减少输入图像数量
- 降低图像分辨率（在 train.py 中使用 `--resolution 512`）
- 关闭其他占用显存的程序

#### 错误：ModuleNotFoundError: No module named 'xxx'

**解决**：
```bash
pip install xxx
```

#### 错误：DLL load failed

```
ImportError: DLL load failed while importing _C: 找不到指定的模块。
```

**解决**：
1. 确保 CUDA bin 目录在 PATH 中
2. 重新编译子模块：`pip install --force-reinstall --no-build-isolation submodules/simple-knn`

### 11.3 获取帮助

| 资源 | 链接 |
|------|------|
| InstantSplat GitHub | https://github.com/NVlabs/InstantSplat |
| PyTorch 安装指南 | https://pytorch.org/get-started/locally/ |
| NVIDIA CUDA 文档 | https://docs.nvidia.com/cuda/ |
| RTX 50 系支持讨论 | https://github.com/pytorch/pytorch/issues |

---

## 12. 快速参考命令

### 日常启动脚本

创建 `start_instantsplat.bat`：

```batch
@echo off
chcp 65001

:: 激活 Conda 环境
call conda activate instantsplat

:: 设置 CUDA 路径
set "CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
set PATH=%CUDA_HOME%\bin;%PATH%

:: 进入项目目录
cd /d C:\Users\zsh\Desktop\ASVSim_zsh\InstantSplat

:: 显示状态
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"

echo.
echo InstantSplat 环境已就绪！
echo.
cmd /k
```

### 运行重建

```bash
python train.py \
  -s assets/examples/your_scene \
  -m output/your_scene \
  --iterations 30000 \
  --save_iterations 7000 15000 30000
```

---

## 附录：完整安装命令汇总

```bash
# 1. 安装 CUDA Toolkit 12.8（手动下载安装）

# 2. 创建 Conda 环境
conda create -n instantsplat python=3.10.13 cmake=3.14.0 -y
conda activate instantsplat

# 3. 安装 PyTorch 2.7 with CUDA 12.8
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

# 4. 进入项目目录
cd C:\Users\zsh\Desktop\ASVSim_zsh\InstantSplat

# 5. 安装依赖
pip install -r requirements.txt
pip install einops transformers

# 6. 设置环境变量
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set PATH=%CUDA_HOME%\bin;%PATH%

# 7. 修改 simple-knn.cu（添加 #include <float.h>）

# 8. 编译安装子模块
pip install submodules/simple-knn --no-build-isolation --force-reinstall
pip install submodules/diff-gaussian-rasterization --no-build-isolation
pip install submodules/fused-ssim --no-build-isolation

# 9. 下载模型
mkdir -p mast3r/checkpoints
curl -o mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth ^
  https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth

# 10. 验证安装
python verify_installation.py
```

---

*文档版本: v2.0*
*最后更新: 2026-03-15*
*作者: ASVSim Project*
