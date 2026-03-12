#!/usr/bin/env python3
"""
验证 PyTorch Nightly GPU 支持 (RTX 5070 Ti sm_120)
"""

import sys
import torch

print('='*70)
print('PyTorch GPU Support Verification')
print('='*70)
print()

# 1. PyTorch 版本
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print()

if not torch.cuda.is_available():
    print('[ERROR] CUDA not available!')
    sys.exit(1)

# 2. CUDA 版本
print(f'CUDA version: {torch.version.cuda}')
print(f'cuDNN version: {torch.backends.cudnn.version()}')
print()

# 3. GPU 信息
device_count = torch.cuda.device_count()
print(f'GPU count: {device_count}')
for i in range(device_count):
    props = torch.cuda.get_device_properties(i)
    print(f'  GPU {i}: {props.name}')
    print(f'    Total memory: {props.total_memory / 1024**3:.2f} GB')
    print(f'    Compute capability: {props.major}.{props.minor}')
    print(f'    Multi-processors: {props.multi_processor_count}')
print()

# 4. 测试简单 GPU 运算
print('Testing GPU operations...')
try:
    # 创建张量
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()

    # 矩阵乘法
    z = torch.matmul(x, y)

    print(f'  Matrix multiplication test: PASS')
    print(f'    Result shape: {z.shape}')
    print(f'    Result device: {z.device}')

    # 清理
    del x, y, z
    torch.cuda.empty_cache()

    print()
    print('[SUCCESS] GPU support is working!')
    print('RTX 5070 Ti (sm_120) is now supported by PyTorch Nightly.')

except Exception as e:
    print(f'  [ERROR] GPU operation failed: {e}')
    sys.exit(1)

print()
print('='*70)
print('Next step: Test DA3 with GPU acceleration')
print('='*70)
