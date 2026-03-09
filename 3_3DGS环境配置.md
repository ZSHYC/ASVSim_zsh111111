# Windows 3D Gaussian Splatting 配置记录

**核心目标**: 在 Windows 10/11 环境下，使用 VS2019 和 CUDA 11.8 成功配置并运行 3DGS。

* **操作系统**: Windows 10/11 (64-bit)
* **编译器**: **Visual Studio 2022 Community** (必须安装“使用 C++ 的桌面开发”组件)
* **显卡驱动**: 支持 CUDA 11.8 的驱动
* **CUDA Toolkit**: 11.8 版本
* **Python**: 3.9 (比官方推荐的 3.7 更适合新硬件)
* **PyTorch**: 2.0.1 + cu118

---

## 1. 准备工作：下载与安装

在开始之前，请确保按照 `下载地址.txt` 和截图 `image_e5c397.png` 中的内容，准备好以下工具 。

| 工具名称                | 版本要求                 | 用途           | 关键注意点                                            |
| ----------------------- | ------------------------ | -------------- | ----------------------------------------------------- |
| **Visual Studio** | **2019 Community** | C++编译器      | 安装时必须勾选**"使用 C++ 的桌面开发"**               |
| **CUDA Toolkit**  | **11.8**           | GPU加速        | 安装后检查环境变量 `CUDA_PATH` 是否存在             |
| **Anaconda**      | 最新版                   | Python环境管理 | 用于创建虚拟环境                                      |
| **Git**           | 最新版                   | 代码下载       | 用于克隆项目仓库                                      |
| **Colmap**        | 3.8/3.9                  | 图像预处理     | 解压后需将目录添加到系统环境变量 `Path` 中          |
| **FFmpeg**        | 最新版                   | 视频转图片     | 解压后需将 `bin` 目录添加到系统环境变量 `Path` 中 |
| **Viewers**       | SIBR_viewers             | 结果查看器     | 官方提供的预编译二进制文件                            |

---

## 2. 环境配置（核心避坑版）

原教程提供的 `environment.yml` 可能较老，直接使用会导致依赖冲突。以下是我们在对话中验证过的**最稳健的手动配置方案**。

### 2.1 创建基础环境

打开 Anaconda Prompt，执行以下命令：

```bash
# 1. 创建环境 (推荐 Python 3.9，兼容性最好)
conda create -n 3dgs python=3.9 -y

# 2. 激活环境
conda activate 3dgs

# 3. 安装 PyTorch (对应 CUDA 11.8 的 2.0 版本)
conda install pytorch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 pytorch-cuda=11.8 -c pytorch -c nvidia

# 4. 安装基础依赖
conda install plyfile tqdm -c conda-forge
conda install -c conda-forge ninja
pip install joblib

```

### 2.2 修复 NumPy 兼容性问题

原教程未提及，但实测中最新的 NumPy 2.0 会导致 PyTorch 崩溃。

```bash
# 强制降级 NumPy 到 1.x 版本
pip install "numpy<2.0"

```

---

## 3. 编译核心子模块（最关键的一步）

这是教程中最容易报错的部分（如 `Access Denied` 或 `WinError 2`）。**请放弃普通 CMD，按照以下步骤操作** 。

1. **打开专用终端**：在 Windows 开始菜单搜索并打开 **"x64 Native Tools Command Prompt for VS 2019"**。
2. **依次执行编译命令**：

```cmd
:: 1. 激活环境
conda activate 3dgs

:: 2. 进入项目根目录 (假设在 D 盘)
d:
cd D:\gaussian-splatting

:: 3. 设置环境变量锁 (防止 Python 二次查找编译器导致冲突) - 这是成功的关键！
set DISTUTILS_USE_SDK=1
set MSSdk=1

:: 4. 编译安装三个子模块 (使用 --no-build-isolation 避免找不到 torch)
pip install submodules/diff-gaussian-rasterization --no-build-isolation
pip install submodules/simple-knn --no-build-isolation
pip install submodules/fused-ssim --no-build-isolation

```

*如果你看到三个 `Successfully installed`，恭喜你，环境配置完成了！*

---

## 4. 数据准备与预处理

参考 `image_e5c376.png` 和 `运行训练命令.txt`，数据结构应如下 ：

### 4.1 目录结构

```text
D:\gaussian-splatting\
├── data\               <-- 你的素材放这里
│   └── <场景名>\       <-- 例如 "my_scene"
│       └── input\      <-- 放入你拍摄的图片或视频帧
├── output\             <-- 训练结果会自动生成在这里
└── ...

```

### 4.2 视频转图片 (如果素材是视频)

如果你的素材是一个 `video.mp4`，可以使用 FFmpeg 提取帧：

```bash
ffmpeg -i video.mp4 -qscale:v 1 -r 2 data/my_scene/input/%04d.jpg

```

### 4.3 运行 COLMAP 预处理 (SfM)

3DGS 需要相机位姿才能训练。在 `3dgs` 环境下运行：

```bash
# 这会自动调用 COLMAP 计算相机参数
python convert.py -s data/my_scene

```

*注意：这步需要你电脑里安装了 COLMAP 并在环境变量路径中。*

---

## 5. 模型训练

完成数据预处理后，开始炼丹 ：

```bash
# 基础训练命令
python train.py -s data/my_scene

```

**常用参数技巧**：

* `--test_iterations -1`：如果显存较小（<8GB），加上这个参数可以禁用测试过程中的渲染，节省显存。
* `--save_iterations 7000 30000`：指定保存模型的迭代次数。

**预期输出**：
看到进度条跑动，并且最后显示 `Training complete.` 即为成功。

---

## 6. 查看结果

训练完成后，模型位于 `output/<随机ID>` 文件夹内。使用 SIBR Viewer 查看：

```cmd
# [cite_start]根据 运行训练命令.txt 和你的实际路径 [cite: 3]
.\viewers\bin\SIBR_gaussianViewer_app.exe -m output\<你的模型文件夹名>

```

**操作快捷键**：

* **鼠标左键**：旋转视角
* **鼠标右键**：平移
* **滚轮**：缩放
* **I / O / P**：切换渲染模式

---

## 7. 常见报错与解决方案总结 (FAQ)

这是我们在配置过程中遇到的所有实际问题及其解法：

| 错误现象                                                | 根本原因                    | 解决方案                                                     |
| ------------------------------------------------------- | --------------------------- | ------------------------------------------------------------ |
| **`Access Denied` / `WinError 2**`                  | 编译器路径有空格或权限不足  | 使用**VS2019 x64 Native Tools** 终端，不要用普通 CMD。 |
| **`UserWarning: DISTUTILS_USE_SDK`**            | Python 试图二次激活编译器   | 执行 `set DISTUTILS_USE_SDK=1` 和 `set MSSdk=1`。        |
| **`ModuleNotFoundError: torch`**                | pip 构建环境隔离导致        | 安装命令加上 `--no-build-isolation` 参数。                 |
| **`RuntimeError: Numpy is not available`**      | NumPy 2.0 与 PyTorch 不兼容 | 执行 `pip install "numpy<2.0"` 降级。                      |
| **`ImportError: cannot import name distCUDA2`** | 运行目录混淆或安装不完整    | `cd ..` 退出当前目录测试，或按上述步骤重装子模块。         |

这份指南涵盖了从安装到运行的全过程，只要严格按照其中的**“VS2019 开发终端 + 环境变量锁”**这一核心逻辑操作，即可在任何 Windows 机器上复现成功。
