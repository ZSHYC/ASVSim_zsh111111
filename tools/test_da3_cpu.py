#!/usr/bin/env python3
"""
DA3 官方 API 推理测试 - CPU 版本
由于 PyTorch 2.6 不完全支持 RTX 5070 Ti (sm_120)，使用 CPU 进行测试

使用方法:
    conda activate bishe
    python test_da3_cpu.py
"""

import os
import sys
import time
import glob
import torch
import numpy as np
from pathlib import Path

# 添加 DA3 到路径
sys.path.insert(0, r'D:\ASVSim_models\Depth-Anything-3\src')
os.environ['HF_HOME'] = r'D:\ASVSim_models\cache\hub'

import cv2

# 从官方 API 导入
from depth_anything_3.api import DepthAnything3

# 配置 - 使用 CPU
DEVICE = torch.device("cpu")  # 改用 CPU
MODEL_NAME = "depth-anything/DA3-LARGE-1.1"  # Hugging Face 模型名
TEST_IMAGE_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_12_20_53_24\rgb'
OUTPUT_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\test_output\da3_cpu'

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


def print_section(title):
    """打印章节标题"""
    print('\n' + '='*70)
    print(f'  {title}')
    print('='*70)


def load_model():
    """加载 DA3 模型"""
    print_section('Loading DA3 Model (CPU Mode)')

    try:
        print(f'Device: {DEVICE}')
        print(f'Model: {MODEL_NAME}')
        print('[NOTE] Using CPU due to CUDA compatibility issues with RTX 5070 Ti')
        print('       PyTorch 2.6 does not fully support sm_120 architecture')
        print()

        # 加载模型
        print('Loading from Hugging Face...')
        print('(This will download ~1.5GB model if not cached)')

        model = DepthAnything3.from_pretrained(MODEL_NAME)
        model = model.to(device=DEVICE)
        model.eval()

        print('[OK] Model loaded successfully')

        # 打印模型信息
        total_params = sum(p.numel() for p in model.parameters())
        print(f'   Total parameters: {total_params / 1e6:.1f}M')

        return model

    except Exception as e:
        print(f'[ERROR] Failed to load model: {e}')
        import traceback
        traceback.print_exc()
        return None


def load_test_images():
    """加载测试图像"""
    print_section('Loading Test Images')

    # 获取所有图像
    image_files = sorted(glob.glob(os.path.join(TEST_IMAGE_DIR, '*.png')))

    if not image_files:
        print(f'[ERROR] No images found in: {TEST_IMAGE_DIR}')
        return None

    print(f'Found {len(image_files)} images')

    # 只使用第一张图像进行测试（CPU 较慢）
    test_files = image_files[:1]  # 只测试1张
    print(f'Using first image for CPU testing:')
    for f in test_files:
        print(f'   - {os.path.basename(f)}')

    return test_files


def run_inference(model, image_files):
    """运行推理"""
    print_section('Running DA3 Inference (CPU)')

    try:
        print(f'Processing {len(image_files)} images...')
        print(f'Device: {DEVICE}')
        print('[WARNING] CPU inference is slow (~30-60s per image)')
        print()

        # 记录时间
        start_time = time.time()

        # 运行推理
        with torch.no_grad():
            prediction = model.inference(image_files)

        inference_time = time.time() - start_time
        print(f'[OK] Inference completed in {inference_time:.2f}s')

        # 检查输出
        print('\nOutput shapes:')
        print(f'   processed_images: {prediction.processed_images.shape}')
        print(f'   depth: {prediction.depth.shape}')
        print(f'   conf: {prediction.conf.shape}')
        print(f'   extrinsics: {prediction.extrinsics.shape}')
        print(f'   intrinsics: {prediction.intrinsics.shape}')

        # 输出数据范围
        print('\nOutput ranges:')
        print(f'   depth: [{prediction.depth.min():.2f}, {prediction.depth.max():.2f}]')
        print(f'   conf: [{prediction.conf.min():.2f}, {prediction.conf.max():.2f}]')

        return prediction

    except Exception as e:
        print(f'[ERROR] Inference failed: {e}')
        import traceback
        traceback.print_exc()
        return None


def visualize_results(prediction, image_files, output_dir):
    """可视化结果"""
    print_section('Visualizing Results')

    for i in range(len(image_files)):
        basename = os.path.basename(image_files[i]).replace('.png', '')

        # 获取数据
        depth = prediction.depth[i]  # [H, W]
        conf = prediction.conf[i]    # [H, W]

        # 保存深度图
        depth_normalized = (depth - depth.min()) / (depth.max() - depth.min())
        depth_uint8 = (depth_normalized * 255).astype(np.uint8)
        depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_PLASMA)

        depth_file = os.path.join(output_dir, f'{basename}_depth.png')
        cv2.imwrite(depth_file, depth_colored)

        # 保存置信度图
        conf_uint8 = (conf * 255).astype(np.uint8)
        conf_colored = cv2.applyColorMap(conf_uint8, cv2.COLORMAP_VIRIDIS)

        conf_file = os.path.join(output_dir, f'{basename}_conf.png')
        cv2.imwrite(conf_file, conf_colored)

        # 保存原始数据
        np.save(os.path.join(output_dir, f'{basename}_depth.npy'), depth)
        np.save(os.path.join(output_dir, f'{basename}_conf.npy'), conf)

        print(f'   Saved: {basename}_depth.png ({depth.shape})')

    print(f'[OK] All results saved to: {output_dir}')


def main():
    """主函数"""
    print('='*70)
    print('DA3 Official API Inference Test - CPU Mode')
    print('='*70)
    print()
    print('NOTE: This test uses CPU because PyTorch 2.6 does not fully')
    print('      support RTX 5070 Ti (sm_120) CUDA architecture.')
    print()
    print('To enable GPU acceleration, upgrade to PyTorch Nightly:')
    print('  pip uninstall torch torchvision torchaudio')
    print('  pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128')

    # 1. 加载模型
    model = load_model()
    if model is None:
        return 1

    # 2. 加载测试图像
    image_files = load_test_images()
    if image_files is None:
        return 1

    # 3. 运行推理
    prediction = run_inference(model, image_files)
    if prediction is None:
        return 1

    # 4. 可视化结果
    visualize_results(prediction, image_files, OUTPUT_DIR)

    # 5. 总结
    print_section('Test Summary')
    print('[SUCCESS] DA3 official API test completed (CPU mode)!')
    print()
    print('Results:')
    print(f'   Processed: {len(image_files)} images')
    print(f'   Output directory: {OUTPUT_DIR}')
    print()
    print('Generated files:')
    print(f'   - *_depth.png (depth visualization)')
    print(f'   - *_conf.png (confidence visualization)')
    print(f'   - *_depth.npy (raw depth values)')
    print()
    print('Next steps:')
    print('   1. Check the generated depth images')
    print('   2. Compare with simulation depth')
    print('   3. For GPU acceleration, upgrade PyTorch to Nightly version')

    return 0


if __name__ == '__main__':
    sys.exit(main())
