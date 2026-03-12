#!/usr/bin/env python3
"""
DA3 官方 API 推理测试
使用 ByteDance 官方 Depth Anything 3 进行深度估计

使用方法:
    conda activate bishe
    python test_da3_official.py
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
from PIL import Image

# 从官方 API 导入
from depth_anything_3.api import DepthAnything3

# 配置
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = r'D:\ASVSim_models\depth_anything_3'  # 本地模型路径
TEST_IMAGE_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_12_20_53_24\rgb'
OUTPUT_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\test_output\da3_official'

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


def print_section(title):
    """打印章节标题"""
    print('\n' + '='*70)
    print(f'  {title}')
    print('='*70)


def load_model():
    """加载 DA3 模型"""
    print_section('Loading DA3 Model')

    try:
        print(f'Device: {DEVICE}')
        print(f'Model path: {MODEL_PATH}')

        # 检查本地模型文件
        model_file = os.path.join(MODEL_PATH, 'da3_large.safetensors')
        if os.path.exists(model_file):
            print(f'[OK] Found local model: {model_file}')
            print(f'   Size: {os.path.getsize(model_file) / (1024**3):.2f} GB')

        # 加载模型
        # 方法1: 使用 Hugging Face 模型名
        # model = DepthAnything3.from_pretrained("depth-anything/DA3-LARGE-1.1")

        # 方法2: 使用本地路径（需要正确配置）
        # 注意：DA3 需要从 Hugging Face 加载配置，本地只提供权重
        print('\nLoading from Hugging Face...')
        print('(Using depth-anything/DA3-LARGE-1.1)')

        model = DepthAnything3.from_pretrained("depth-anything/DA3-LARGE-1.1")
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

    # 使用前几张图像进行测试
    test_files = image_files[:3]  # 测试前3张
    print(f'Using first {len(test_files)} images for testing:')
    for f in test_files:
        print(f'   - {os.path.basename(f)}')

    return test_files


def run_inference(model, image_files):
    """运行推理"""
    print_section('Running DA3 Inference')

    try:
        print(f'Processing {len(image_files)} images...')
        print(f'Device: {DEVICE}')

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

    num_images = len(image_files)

    for i in range(num_images):
        basename = os.path.basename(image_files[i]).replace('.png', '')

        # 获取数据
        depth = prediction.depth[i]  # [H, W]
        conf = prediction.conf[i]    # [H, W]
        extrinsics = prediction.extrinsics[i]  # [3, 4]
        intrinsics = prediction.intrinsics[i]  # [3, 3]

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
        np.save(os.path.join(output_dir, f'{basename}_extrinsics.npy'), extrinsics)
        np.save(os.path.join(output_dir, f'{basename}_intrinsics.npy'), intrinsics)

        print(f'   Saved: {basename}_depth.png, {basename}_conf.png')

    print(f'[OK] All results saved to: {output_dir}')


def compare_with_simulation(prediction, image_files, output_dir):
    """与仿真深度对比"""
    print_section('Comparing with Simulation Depth')

    sim_depth_dir = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_12_20_53_24\depth'

    for i in range(len(image_files)):
        basename = os.path.basename(image_files[i]).replace('.png', '')
        sim_depth_file = os.path.join(sim_depth_dir, f'{basename}.npy')

        if not os.path.exists(sim_depth_file):
            print(f'   [SKIP] Simulation depth not found: {basename}')
            continue

        # 加载仿真深度
        sim_depth = np.load(sim_depth_file)

        # 获取预测深度
        pred_depth = prediction.depth[i]

        print(f'\n   {basename}:')
        print(f'      Sim depth: {sim_depth.shape}, range: [{sim_depth.min():.2f}, {sim_depth.max():.2f}]')
        print(f'      Pred depth: {pred_depth.shape}, range: [{pred_depth.min():.2f}, {pred_depth.max():.2f}]')

        # 创建对比图
        # 归一化两者
        sim_valid = sim_depth[np.isfinite(sim_depth)]
        if len(sim_valid) > 0:
            sim_norm = (sim_depth - sim_valid.min()) / (sim_valid.max() - sim_valid.min() + 1e-8)
        else:
            sim_norm = np.zeros_like(sim_depth)

        pred_norm = (pred_depth - pred_depth.min()) / (pred_depth.max() - pred_depth.min() + 1e-8)

        # 调整大小匹配
        if pred_norm.shape != sim_norm.shape:
            pred_norm_resized = cv2.resize(pred_norm, (sim_norm.shape[1], sim_norm.shape[0]))
        else:
            pred_norm_resized = pred_norm

        # 创建对比图
        h, w = sim_norm.shape
        comparison = np.zeros((h, w*2, 3), dtype=np.uint8)

        sim_colored = cv2.applyColorMap((sim_norm * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        pred_colored = cv2.applyColorMap((pred_norm_resized * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)

        comparison[:, :w] = sim_colored
        comparison[:, w:] = pred_colored

        # 添加标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison, 'Simulation', (10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, 'DA3', (w + 10, 30), font, 1, (255, 255, 255), 2)

        # 保存
        comp_file = os.path.join(output_dir, f'{basename}_comparison.png')
        cv2.imwrite(comp_file, comparison)
        print(f'      Saved comparison: {basename}_comparison.png')


def main():
    """主函数"""
    print('='*70)
    print('DA3 Official API Inference Test')
    print('='*70)

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

    # 5. 与仿真对比
    compare_with_simulation(prediction, image_files, OUTPUT_DIR)

    # 6. 总结
    print_section('Test Summary')
    print('[SUCCESS] DA3 official API test completed!')
    print(f'   Processed: {len(image_files)} images')
    print(f'   Output: {OUTPUT_DIR}')
    print(f'   Generated files:')
    print(f'      - *_depth.png (depth visualization)')
    print(f'      - *_conf.png (confidence visualization)')
    print(f'      - *_depth.npy (raw depth values)')
    print(f'      - *_extrinsics.npy (camera pose)')
    print(f'      - *_intrinsics.npy (camera intrinsics)')
    print(f'      - *_comparison.png (vs simulation)')

    return 0


if __name__ == '__main__':
    sys.exit(main())
