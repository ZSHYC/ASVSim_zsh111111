@echo off
chcp 65001 >nul
cls
echo ==========================================
echo  ASVSim Phase 4 环境部署脚本
echo  RTX 5070 Ti 优化版 (D盘存储)
echo ==========================================
echo.
echo 本脚本将：
echo  1. 在 D 盘创建模型存储目录
echo  2. 创建 bishe Conda 环境
echo  3. 安装 PyTorch 2.6 + CUDA 12.6
echo  4. 安装其他依赖
echo  5. 配置环境变量（指向D盘）
echo  6. 验证安装
echo.
echo 按任意键开始部署...
pause >nul
cls

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本!
    echo.
    echo 操作步骤：
    echo  1. 右键点击此脚本
echo  2. 选择"以管理员身份运行"
echo.
    pause
    exit /b 1
)

:: ===== 第1步：创建 D 盘目录 =====
echo [1/6] 创建 D 盘模型目录...
if not exist "D:\ASVSim_models" (
    mkdir "D:\ASVSim_models"
    echo  创建: D:\ASVSim_models
)
if not exist "D:\ASVSim_models\sam3" (
    mkdir "D:\ASVSim_models\sam3"
    echo  创建: D:\ASVSim_models\sam3
)
if not exist "D:\ASVSim_models\depth_anything_3" (
    mkdir "D:\ASVSim_models\depth_anything_3"
    echo  创建: D:\ASVSim_models\depth_anything_3
)
if not exist "D:\ASVSim_models\cache" (
    mkdir "D:\ASVSim_models\cache"
    echo  创建: D:\ASVSim_models\cache
)
if not exist "D:\ASVSim_models\cache\hub" (
    mkdir "D:\ASVSim_models\cache\hub"
    echo  创建: D:\ASVSim_models\cache\hub
)
if not exist "D:\ASVSim_models\cache\torch" (
    mkdir "D:\ASVSim_models\cache\torch"
    echo  创建: D:\ASVSim_models\cache\torch
)
if not exist "D:\ASVSim_models\datasets" (
    mkdir "D:\ASVSim_models\datasets"
    echo  创建: D:\ASVSim_models\datasets
)
echo [OK] 目录创建完成
echo.

:: ===== 第2步：创建 Conda 环境 =====
echo [2/6] 创建 bishe Conda 环境...
echo  这可能需要几分钟，请耐心等待...
call conda create -n bishe python=3.12 -y 2>&1
if errorlevel 1 (
    echo [错误] Conda 环境创建失败!
    echo.
    echo 可能的解决方案：
    echo  1. 检查 Conda/Miniforge 是否正确安装
echo  2. 运行: conda update conda
echo  3. 手动创建: conda create -n bishe python=3.12
echo.
    pause
    exit /b 1
)
echo [OK] bishe 环境创建完成
echo.

:: ===== 第3步：安装 PyTorch =====
echo [3/6] 安装 PyTorch 2.6 + CUDA 12.6...
echo  下载约 2GB，请耐心等待...
call conda activate bishe
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126 2>&1
if errorlevel 1 (
    echo [错误] PyTorch 安装失败!
    echo.
    echo 可能的解决方案：
    echo  1. 检查网络连接
echo  2. 尝试使用镜像: -i https://pypi.tuna.tsinghua.edu.cn/simple
echo  3. 手动安装: pip install torch torchvision torchaudio
echo.
    pause
    exit /b 1
)
echo [OK] PyTorch 安装完成
echo.

:: ===== 第4步：安装其他依赖 =====
echo [4/6] 安装其他依赖...
pip install numpy scipy scikit-learn scikit-image matplotlib tqdm -q 2>&1
pip install opencv-python Pillow imageio pyyaml tensorboard -q 2>&1
pip install huggingface_hub -q 2>&1
if errorlevel 1 (
    echo [警告] 部分依赖安装可能失败，继续尝试...
)
echo [OK] 依赖安装完成
echo.

:: ===== 第5步：配置环境变量 =====
echo [5/6] 配置环境变量...
call conda env config vars set HF_HOME="D:\ASVSim_models\cache\hub" 2>&1
call conda env config vars set TORCH_HOME="D:\ASVSim_models\cache\torch" 2>&1
call conda env config vars set PYTHONPATH="C:\Users\zsh\Desktop\ASVSim_zsh" 2>&1

:: 设置系统环境变量（永久）
setx HF_HOME "D:\ASVSim_models\cache\hub" /M 2>nul
setx TORCH_HOME "D:\ASVSim_models\cache\torch" /M 2>nul

echo [OK] 环境变量配置完成
echo  HF_HOME = D:\ASVSim_models\cache\hub
echo  TORCH_HOME = D:\ASVSim_models\cache\torch
echo.

:: ===== 第6步：验证安装 =====
echo [6/6] 验证安装...
python -c "
import torch
import os

print('='*50)
print('PyTorch 版本:', torch.__version__)
print('CUDA 版本:', torch.version.cuda)
print('cuDNN 版本:', torch.backends.cudnn.version())
print('GPU 可用:', torch.cuda.is_available())

if torch.cuda.is_available():
    print('GPU 名称:', torch.cuda.get_device_name(0))
    props = torch.cuda.get_device_properties(0)
    print(f'显存总量: {props.total_memory / 1e9:.2f} GB')

    # CUDA 测试
    x = torch.rand(1000, 1000).cuda()
    y = torch.matmul(x, x)
    print('CUDA 运算测试: ✅ 通过')

print()
print('环境变量:')
print(f'  HF_HOME: {os.environ.get(\"HF_HOME\", \"Not set\")}')
print(f'  TORCH_HOME: {os.environ.get(\"TORCH_HOME\", \"Not set\")}')
print('='*50)
" 2>&1

if errorlevel 1 (
    echo [错误] 验证失败!
    echo.
    pause
    exit /b 1
)

:: ===== 完成 =====
echo.
echo ==========================================
echo  部署完成！🎉
echo ==========================================
echo.
echo 目录结构：
echo  C盘 - 代码: C:\Users\zsh\Desktop\ASVSim_zsh\
echo  D盘 - 模型: D:\ASVSim_models\
echo.
echo 下一步：
echo  1. 激活环境: conda activate bishe
echo  2. 下载 SAM 3: 访问 https://huggingface.co/facebook/sam3
echo  3. 下载 DA3: 访问 https://huggingface.co/depth-anything
echo  4. 开始 Phase 4 开发！
echo.
pause
