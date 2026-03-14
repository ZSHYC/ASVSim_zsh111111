# InstantSplat 完整配置指南（RTX 50 系显卡专用）

**文档版本**: v3.0
**创建时间**: 2026-03-15
**适用平台**: Windows 10/11
**适用显卡**: NVIDIA RTX 50 系列 (5070/5080/5090)
**CUDA版本**: 12.8
**Python版本**: 3.10.13
**PyTorch版本**: 2.7.0+cu128

---

## 目录

1. [前言与重要说明](#1-前言与重要说明)
2. [环境准备](#2-环境准备)
3. [CUDA Toolkit 12.8 安装](#3-cuda-toolkit-128-安装)
4. [Conda 环境创建](#4-conda-环境创建)
5. [PyTorch 2.7 安装](#5-pytorch-27-安装)
6. [InstantSplat 依赖安装](#6-instantsplat-依赖安装)
7. [CUDA 子模块编译](#7-cuda-子模块编译)
8. [RoPE CUDA Kernels 编译](#8-rope-cuda-kernels-编译)
9. [模型下载](#9-模型下载)
10. [最终验证](#10-最终验证)
11. [故障排除](#11-故障排除)
12. [附录：完整命令汇总](#12-附录完整命令汇总)

---

## 1. 前言与重要说明

### 1.1 为什么 RTX 50 系需要特殊配置？

#### 计算能力 (Compute Capability)

NVIDIA GPU 使用**计算能力**（Compute Capability）来标识其架构版本：

| 显卡系列 | 架构名称 | 计算能力 | 最低 CUDA 版本 |
|---------|---------|---------|--------------|
| RTX 30 系 | Ampere | sm_86 | CUDA 11.1+ |
| RTX 40 系 | Ada Lovelace | sm_89 | CUDA 11.8+ |
| **RTX 50 系** | **Blackwell** | **sm_120** | **CUDA 12.8+** |

**关键问题**：RTX 5070/5080/5090 使用 **sm_120** 计算能力，这个架构在 **CUDA 12.8** 中才首次加入支持。

如果使用 CUDA 12.1 + PyTorch 2.5，会出现以下错误：
```
NVIDIA GeForce RTX 5070 with CUDA capability sm_120 is not compatible
with the current PyTorch installation.
```

#### PyTorch 2.7 的必要性

| PyTorch 版本 | 支持的最高 CUDA | 是否支持 sm_120 |
|-------------|----------------|---------------|
| 2.4.x - 2.6.x | CUDA 12.1/12.4 | ❌ 不支持 |
| **2.7.x** | **CUDA 12.8** | ✅ **支持** |

PyTorch 2.7（2025年4月发布）是第一个原生支持 RTX 50 系的版本。

### 1.2 本文档记录的所有修复

在配置过程中，我们遇到了以下问题并修复：

1. **simple-knn.cu 缺少头文件** → 添加 `#include <float.h>`
2. **RoPE kernels.cu PyTorch 2.7 不兼容** → `tokens.type()` 改为 `tokens.scalar_type()`
3. **RoPE Windows DLL 加载失败** → 修改 `curope2d.py` 添加 DLL 路径
4. **Visual Studio 版本不兼容** → 设置 `NVCC_APPEND_FLAGS=-allow-unsupported-compiler`

---

## 2. 环境准备

### 2.1 检查显卡驱动

```bash
nvidia-smi
```

**预期输出**：
- Driver Version: 550.xx 或更高（推荐 570+）
- GPU 显示为 NVIDIA GeForce RTX 5070/5080/5090
- CUDA Version: 12.8 或更高

### 2.2 检查 Conda 安装

```bash
conda --version
```

**预期输出**：`conda 24.x.x`

**如果未安装**：
下载 Miniconda：https://docs.anaconda.com/miniconda/

### 2.3 克隆 InstantSplat 仓库

```bash
cd C:\Users\zsh\Desktop\ASVSim_zsh
git clone --recursive https://github.com/NVlabs/InstantSplat.git
cd InstantSplat
```

**注意**：`--recursive` 参数必须加，用于下载子模块。

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

#### 步骤 3：自定义安装选项

**必须勾选的组件**：

| 组件 | 是否必须 | 说明 |
|------|---------|------|
| CUDA > Development > Compiler | ✅ 必须 | nvcc 编译器 |
| CUDA > Development > CUDA Visual Studio Integration | ✅ 必须 | VS 集成 |
| CUDA > Runtime > CUDA Runtime | ✅ 必须 | 运行时库 |
| CUDA > Libraries | ✅ 必须 | CUDA 库文件 |
| Driver components | ⚠️ 可选 | 如果驱动已是最新版可不选 |

**可以取消的组件**（节省空间）：
- GeForce Experience
- PhysX
- HD Audio
- Documentation
- Samples（可选）

#### 步骤 4：选择安装路径

**推荐路径**：
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
```

**不建议更改路径**，因为：
1. PyTorch 会自动搜索这个路径
2. 大多数教程和脚本都假设这个路径
3. 避免中文路径导致的编译问题

### 3.3 验证 CUDA Toolkit 安装

打开新的终端窗口（**必须新开窗口**），运行：

```bash
nvcc --version
```

**预期输出**：
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2025 NVIDIA Corporation
Built on Wed_Jan_15_19:38:46_Pacific_Standard_Time_2025
Cuda compilation tools, release 12.8, V12.8.61
```

### 3.4 设置环境变量

**方法：在 PowerShell 中临时设置（推荐用于测试）**

```powershell
$env:CUDA_HOME = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
$env:PATH = "$env:CUDA_HOME\bin;$env:PATH"
```

**验证设置**：
```bash
python -c "import os; print(os.environ.get('CUDA_HOME'))"
```

---

## 4. Conda 环境创建

### 4.1 创建 Python 3.10.13 环境

```bash
conda create -n instantsplat python=3.10.13 cmake=3.14.0 -y
```

**参数说明**：
- `-n instantsplat`：环境名称
- `python=3.10.13`：Python 版本
- `cmake=3.14.0`：CMake 版本（编译子模块需要）

**为什么选择 Python 3.10？**
- PyTorch 2.7 官方支持 Python 3.9-3.12
- 3.10 是稳定且兼容性好的版本

### 4.2 激活环境

```bash
conda activate instantsplat
```

**验证**：
```bash
python --version
```

预期输出：`Python 3.10.13`

### 4.3 升级基础工具

```bash
pip install --upgrade pip setuptools wheel
```

---

## 5. PyTorch 2.7 安装

### 5.1 安装 PyTorch 2.7 with CUDA 12.8

```bash
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
```

**参数详解**：

| 参数 | 说明 |
|------|------|
| `torch==2.7.0` | PyTorch 主库 2.7.0 |
| `torchvision==0.22.0` | 与 PyTorch 2.7 配套的视觉库 |
| `--index-url https://download.pytorch.org/whl/cu128` | CUDA 12.8 版本的源 |

**为什么是 cu128？**
- `cu128` = CUDA 12.8
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
1. 版本显示 `2.7.0+cu128`
2. `CUDA available: True`
3. GPU 名称正确显示

### 5.3 验证计算能力

```bash
python -c "import torch; print('CUDA capabilities:', torch.cuda.get_device_capability())"
```

**预期输出**：
```
CUDA capabilities: (12, 0)
```

这表示 PyTorch 正确识别了 sm_120。

---

## 6. InstantSplat 依赖安装

### 6.1 安装 Python 依赖

确保你在 `InstantSplat` 目录下：

```bash
cd C:\Users\zsh\Desktop\ASVSim_zsh\InstantSplat
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

### 6.2 安装额外依赖

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
2. 针对 RTX 50 系（sm_120）优化

### 7.2 设置环境变量

在 PowerShell 中设置：

```powershell
$env:CUDA_HOME = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
$env:PATH = "$env:CUDA_HOME\bin;$env:PATH"
$env:TORCH_CUDA_ARCH_LIST = "8.0;8.6;8.9;9.0;12.0"
$env:NVCC_APPEND_FLAGS = "-allow-unsupported-compiler"
```

**原理说明**：
- `TORCH_CUDA_ARCH_LIST`：指定要编译的 GPU 架构
- `NVCC_APPEND_FLAGS`：允许使用不支持的 Visual Studio 版本（Windows 常见）

### 7.3 修改 simple-knn.cu（RTX 50 系必需）

**问题**：`simple-knn` 模块使用了 `FLT_MAX` 宏，需要显式包含头文件。

**文件路径**：
```
InstantSplat/submodules/simple-knn/simple-knn.cu
```

**修改步骤**：

1. 打开文件
```bash
notepad submodules/simple-knn/simple-knn.cu
```

2. 在文件**第一行**添加：
```cpp
#include <float.h>
```

3. 保存文件

### 7.4 编译安装三个子模块

#### 安装 simple-knn

```bash
pip install submodules/simple-knn --no-build-isolation --force-reinstall
```

**参数说明**：
- `--no-build-isolation`：**关键参数**，允许 setup.py 访问已安装的 torch
- `--force-reinstall`：强制重新安装

**预期输出**：
```
Successfully installed simple-knn-0.0.0
```

#### 安装 diff-gaussian-rasterization

```bash
pip install submodules/diff-gaussian-rasterization --no-build-isolation
```

**预期输出**：
```
Successfully installed diff-gaussian-rasterization-0.0.0
```

#### 安装 fused-ssim

```bash
pip install submodules/fused-ssim --no-build-isolation
```

**预期输出**：
```
Successfully installed fused-ssim-0.0.0
```

### 7.5 验证子模块安装

```bash
python -c "import diff_gaussian_rasterization; import simple_knn; from fused_ssim import fused_ssim; print('✓ 所有子模块导入成功')"
```

---

## 8. RoPE CUDA Kernels 编译

### 8.1 什么是 RoPE？

**RoPE** = Rotary Position Embedding（旋转位置编码）

这是 MASt3R/DUSt3R 使用的一种位置编码方式：
- 用于处理图像特征的位置信息
- 编译 CUDA 内核后，GPU 计算加速明显
- 官方标记为 "Optional but highly suggested"

### 8.2 进入目录并编译

```bash
cd croco/models/curope/
python setup.py build_ext --inplace
```

### 8.3 修复 PyTorch 2.7 兼容性问题

**问题**：编译时会出现以下错误：
```
error: no suitable conversion function from "const at::DeprecatedTypeProperties" to "c10::ScalarType" exists
```

**原因**：PyTorch 2.7 中 `tokens.type()` 的返回类型变了。

**修复方法**：

1. 打开文件：
```
croco/models/curope/kernels.cu
```

2. 找到第 101 行：
```cpp
AT_DISPATCH_FLOATING_TYPES_AND_HALF(tokens.type(), "rope_2d_cuda", ([&] {
```

3. 修改为：
```cpp
AT_DISPATCH_FLOATING_TYPES_AND_HALF(tokens.scalar_type(), "rope_2d_cuda", ([&] {
```

4. 保存文件并重新编译：
```bash
python setup.py build_ext --inplace
```

### 8.4 修复 Windows DLL 加载问题

**问题**：编译成功后，导入时出现：
```
ImportError: DLL load failed while importing curope: 找不到指定的模块
```

**原因**：Windows 找不到 torch 和 CUDA 的 DLL 文件。

**修复方法**：

1. 打开文件：
```
croco/models/curope/curope2d.py
```

2. 在文件开头添加：

```python
import os
import sys

# Fix for Windows DLL loading issue with RTX 50 series
if sys.platform == 'win32':
    try:
        import ctypes
        from pathlib import Path
        # Add PyTorch lib directory
        torch_lib = Path(torch.__file__).parent / 'lib'
        if torch_lib.exists():
            os.add_dll_directory(str(torch_lib))
        # Add CUDA bin directory
        cuda_home = os.environ.get('CUDA_HOME', r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8')
        cuda_bin = Path(cuda_home) / 'bin'
        if cuda_bin.exists():
            os.add_dll_directory(str(cuda_bin))
    except Exception:
        pass
```

3. 保存文件

### 8.5 验证 RoPE 安装

返回项目根目录：

```bash
cd ../../../..
python -c "from croco.models.curope.curope2d import cuRoPE2D; print('✓ cuRoPE2D 导入成功')"
```

**预期输出**：
```
✓ cuRoPE2D 导入成功
```

---

## 9. 模型下载

### 9.1 创建模型目录

```bash
mkdir -p mast3r/checkpoints
```

### 9.2 下载 MASt3R 预训练模型

**方法 1：使用 curl**

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

### 9.3 验证模型下载

```bash
dir mast3r\checkpoints\
```

**预期输出**：
```
MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth    2,627 MB
```

---

## 10. 最终验证

### 10.1 完整功能验证

运行以下命令验证所有组件：

```bash
python -c "
import torch
print('='*60)
print('InstantSplat 安装验证')
print('='*60)
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.version.cuda}')
print(f'GPU: {torch.cuda.get_device_name(0)}')

# 验证子模块
import diff_gaussian_rasterization
import simple_knn
from fused_ssim import fused_ssim

print('✓ diff_gaussian_rasterization')
print('✓ simple_knn')
print('✓ fused_ssim')

# 验证 CUDA 内核
from simple_knn._C import distCUDA2
points = torch.randn(100, 3).cuda()
dist = distCUDA2(points)
print(f'✓ CUDA 内核测试通过')

# 验证 RoPE
from croco.models.curope.curope2d import cuRoPE2D
print('✓ cuRoPE2D')

# 验证模型
import os
model_path = 'mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth'
if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f'✓ MASt3R 模型: {size_mb:.1f} MB')

print('='*60)
print('🎉 InstantSplat 安装成功！')
print('='*60)
"
```

**预期完整输出**：
```
============================================================
InstantSplat 安装验证
============================================================
PyTorch: 2.7.0+cu128
CUDA: 12.8
GPU: NVIDIA GeForce RTX 5070 Ti Laptop GPU
✓ diff_gaussian_rasterization
✓ simple_knn
✓ fused_ssim
✓ CUDA 内核测试通过
✓ cuRoPE2D
✓ MASt3R 模型: 2627.3 MB
============================================================
🎉 InstantSplat 安装成功！
============================================================
```

---

## 11. 故障排除

### 11.1 CUDA_HOME 环境变量未设置

**错误**：
```
OSError: CUDA_HOME environment variable is not set.
```

**解决**：
```powershell
$env:CUDA_HOME = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
$env:PATH = "$env:CUDA_HOME\bin;$env:PATH"
```

### 11.2 Visual Studio 版本不兼容

**错误**：
```
unsupported Microsoft Visual Studio version!
```

**解决**：
```powershell
$env:NVCC_APPEND_FLAGS = "-allow-unsupported-compiler"
```

### 11.3 ModuleNotFoundError: No module named 'torch'

**原因**：使用了 `--no-build-isolation` 但 torch 未安装

**解决**：先安装 PyTorch 再编译子模块

### 11.4 DLL load failed

**错误**：
```
ImportError: DLL load failed while importing curope
```

**解决**：按照 8.4 节修改 `curope2d.py` 添加 DLL 路径

### 11.5 PyTorch CUDA 版本不匹配

**错误**：
```
RuntimeError: CUDA error: no kernel image is available for execution on the device
```

**解决**：重新安装 PyTorch 2.7 with CUDA 12.8
```bash
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128 --force-reinstall
```

---

## 12. 附录：完整命令汇总

### 12.1 一键安装脚本

创建 `install_instantsplat.ps1`：

```powershell
# InstantSplat RTX 50 Series Installation Script
# Run this in PowerShell with conda available

# Step 1: Create Conda environment
conda create -n instantsplat python=3.10.13 cmake=3.14.0 -y

# Step 2: Activate environment
conda activate instantsplat

# Step 3: Upgrade pip
pip install --upgrade pip setuptools wheel

# Step 4: Install PyTorch 2.7 with CUDA 12.8
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

# Step 5: Install dependencies
pip install -r requirements.txt
pip install einops transformers

# Step 6: Set environment variables
$env:CUDA_HOME = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
$env:PATH = "$env:CUDA_HOME\bin;$env:PATH"
$env:TORCH_CUDA_ARCH_LIST = "8.0;8.6;8.9;9.0;12.0"
$env:NVCC_APPEND_FLAGS = "-allow-unsupported-compiler"

# Step 7: Modify simple-knn.cu (add #include <float.h> at top)
# Manual step: edit submodules/simple-knn/simple-knn.cu

# Step 8: Compile submodules
pip install submodules/simple-knn --no-build-isolation --force-reinstall
pip install submodules/diff-gaussian-rasterization --no-build-isolation
pip install submodules/fused-ssim --no-build-isolation

# Step 9: Compile RoPE (with fixes)
cd croco/models/curope
python setup.py build_ext --inplace
cd ../../../..

# Step 10: Download model
mkdir -p mast3r/checkpoints
# Manual: Download from https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth

Write-Host "Installation complete! Run verification script to confirm."
```

### 12.2 日常启动脚本

创建 `start_instantsplat.bat`：

```batch
@echo off
chcp 65001

:: 激活 Conda 环境
call conda activate instantsplat

:: 设置 CUDA 路径
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set PATH=%CUDA_HOME%\bin;%PATH%

:: 设置编译器标志（RTX 50 系必需）
set TORCH_CUDA_ARCH_LIST=8.0;8.6;8.9;9.0;12.0
set NVCC_APPEND_FLAGS=-allow-unsupported-compiler

:: 进入项目目录
cd /d C:\Users\zsh\Desktop\ASVSim_zsh\InstantSplat

:: 显示状态
python -c "import torch; print('='*60); print('PyTorch:', torch.__version__); print('CUDA:', torch.version.cuda); print('GPU:', torch.cuda.get_device_name(0)); print('='*60)"

echo.
echo InstantSplat 环境已就绪！
echo.
cmd /k
```

### 12.3 运行重建命令

```bash
python train.py \
  -s assets/examples/your_scene \
  -m output/your_scene \
  --iterations 30000 \
  --save_iterations 7000 15000 30000
```

---

## 13. 参考资源

| 资源 | 链接 |
|------|------|
| InstantSplat GitHub | https://github.com/NVlabs/InstantSplat |
| MASt3R GitHub | https://github.com/naver/mast3r |
| PyTorch 安装指南 | https://pytorch.org/get-started/locally/ |
| NVIDIA CUDA 文档 | https://docs.nvidia.com/cuda/ |
| CUDA Toolkit 12.8 | https://developer.nvidia.com/cuda-12-8-0-download-archive |

---

*文档版本: v3.0*
*最后更新: 2026-03-15*
*作者: ASVSim Project*
*特别说明: 本文档专门针对 RTX 50 系列显卡配置*
