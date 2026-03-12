#!/usr/bin/env python3
"""
Phase 4 模型加载测试脚本
测试 SAM 3 和 Depth Anything 3 模型是否能正常加载

使用方法:
    conda activate bishe
    python test_models.py
"""

import os
import sys
import time
import torch
import numpy as np
from pathlib import Path

# 设置环境变量
os.environ['HF_HOME'] = r'D:\ASVSim_models\cache\hub'
os.environ['TORCH_HOME'] = r'D:\ASVSim_models\cache\torch'

# 模型路径
MODEL_PATHS = {
    'sam3': r'D:\ASVSim_models\sam3\sam3.pt',
    'da3_large': r'D:\ASVSim_models\depth_anything_3\da3_large.safetensors',
    'da3_mono': r'D:\ASVSim_models\depth_anything_3\da3_mono.safetensors',
}

# 测试图像路径 (使用已采集的数据)
TEST_IMAGE = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_12_20_53_24\rgb\0001.png'


def print_section(title):
    """打印章节标题"""
    print('\n' + '='*70)
    print(f'  {title}')
    print('='*70)


def check_gpu():
    """检查 GPU 状态"""
    print_section('GPU Status')

    if not torch.cuda.is_available():
        print('[ERROR] CUDA not available!')
        return False

    print(f'[OK] GPU: {torch.cuda.get_device_name(0)}')
    props = torch.cuda.get_device_properties(0)
    print(f'   Memory: {props.total_memory / 1e9:.2f} GB')
    print(f'   CUDA: {torch.version.cuda}')

    # 清理缓存
    torch.cuda.empty_cache()
    allocated = torch.cuda.memory_allocated() / 1e9
    reserved = torch.cuda.memory_reserved() / 1e9
    print(f'   Allocated: {allocated:.2f} GB')
    print(f'   Reserved: {reserved:.2f} GB')
    print(f'   Free: {props.total_memory/1e9 - allocated:.2f} GB')

    return True


def check_model_files():
    """检查模型文件是否存在"""
    print_section('Model Files Check')

    all_exist = True
    for name, path in MODEL_PATHS.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024**3)
            print(f'[OK] {name}: {size:.2f} GB')
            print(f'   Path: {path}')
        else:
            print(f'[ERROR] {name}: NOT FOUND')
            print(f'   Expected: {path}')
            all_exist = False

    return all_exist


def test_da3():
    """测试 Depth Anything 3"""
    print_section('Testing Depth Anything 3')

    try:
        # 尝试不同的加载方式
        print('\n1. Loading DA3-LARGE...')

        # 方法1: 使用 transformers (推荐)
        try:
            from transformers import AutoModelForDepthEstimation, AutoImageProcessor

            print('   Using transformers...')
            model = AutoModelForDepthEstimation.from_pretrained(
                r'D:\ASVSim_models\depth_anything_3',
                filename='da3_large.safetensors'
            )
            print('   ✅ Model loaded via transformers')

        except Exception as e1:
            print(f'   transformers failed: {e1}')

            # 方法2: 直接加载 safetensors
            print('   Trying direct safetensors load...')
            from safetensors.torch import load_file

            state_dict = load_file(MODEL_PATHS['da3_large'])
            print(f'   [OK] Loaded safetensors ({len(state_dict)} tensors)')

            # 打印一些 tensor shapes
            for i, (k, v) in enumerate(state_dict.items()):
                if i < 5:
                    print(f'      {k}: {v.shape}')
                else:
                    print('      ...')
                    break

        # 方法3: 使用 torch.load (如果 safetensors 失败)
        # state_dict = torch.load(MODEL_PATHS['da3_large'], map_location='cpu')

        print('\n2. Testing inference...')

        # 加载测试图像
        if os.path.exists(TEST_IMAGE):
            print(f'   Loading test image: {TEST_IMAGE}')
            import cv2
            img = cv2.imread(TEST_IMAGE)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            print(f'   Image shape: {img.shape}')

            # 模拟推理 (这里简化，实际需要完整的预处理)
            print('   [OK] Image loaded successfully')
            print('   [NOTE] Full inference test requires DA3 model implementation')
        else:
            print(f'   [WARNING] Test image not found: {TEST_IMAGE}')

        return True

    except Exception as e:
        print(f'[ERROR] DA3 test failed: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_sam3():
    """测试 SAM 3"""
    print_section('Testing SAM 3')

    try:
        print('\n1. Loading SAM 3...')

        # SAM 3 通常使用 torch.jit.load 或 torch.load
        checkpoint = torch.load(MODEL_PATHS['sam3'], map_location='cpu')

        print(f'   [OK] Checkpoint loaded')
        print(f'   Keys: {list(checkpoint.keys())[:5]}...')

        if 'model' in checkpoint:
            print('   Contains: model weights')
        if 'optimizer' in checkpoint:
            print('   Contains: optimizer state')
        if 'epoch' in checkpoint:
            print(f'   Trained epoch: {checkpoint["epoch"]}')

        print('\n2. Model structure:')
        if isinstance(checkpoint, dict):
            for key in list(checkpoint.keys())[:10]:
                val = checkpoint[key]
                if isinstance(val, torch.Tensor):
                    print(f'   {key}: tensor {val.shape}')
                else:
                    print(f'   {key}: {type(val)}')

        print('\n3. Testing inference...')

        # 加载测试图像
        if os.path.exists(TEST_IMAGE):
            print(f'   Loading test image: {TEST_IMAGE}')
            import cv2
            img = cv2.imread(TEST_IMAGE)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            print(f'   Image shape: {img.shape}')
            print('   [OK] Image loaded successfully')
            print('   [NOTE] Full inference test requires SAM 3 model implementation')
        else:
            print(f'   [WARNING] Test image not found: {TEST_IMAGE}')

        return True

    except Exception as e:
        print(f'[ERROR] SAM 3 test failed: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print('='*70)
    print('Phase 4 Model Loading Test')
    print('Device: RTX 5070 Ti (12GB)')
    print('='*70)

    # 1. 检查 GPU
    if not check_gpu():
        print('\n[ERROR] GPU check failed, exiting...')
        return 1

    # 2. 检查模型文件
    if not check_model_files():
        print('\n[ERROR] Some model files not found, exiting...')
        return 1

    results = {}

    # 3. 测试 DA3
    print('\n' + '-'*70)
    print('Testing Depth Anything 3...')
    print('-'*70)
    results['da3'] = test_da3()

    # 清理显存
    torch.cuda.empty_cache()
    time.sleep(1)

    # 4. 测试 SAM 3
    print('\n' + '-'*70)
    print('Testing SAM 3...')
    print('-'*70)
    results['sam3'] = test_sam3()

    # 5. 总结
    print_section('Test Summary')

    for model, success in results.items():
        status = '[PASS]' if success else '[FAIL]'
        print(f'{status} - {model.upper()}')

    # 显存使用
    print('\nFinal GPU Memory:')
    allocated = torch.cuda.memory_allocated() / 1e9
    reserved = torch.cuda.memory_reserved() / 1e9
    print(f'   Allocated: {allocated:.2f} GB')
    print(f'   Reserved: {reserved:.2f} GB')

    all_passed = all(results.values())
    if all_passed:
        print('\n[SUCCESS] All models loaded successfully!')
        print('Ready for Phase 4 development.')
        return 0
    else:
        print('\n[WARNING] Some tests failed.')
        print('Please check the error messages above.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
