#!/usr/bin/env python3
"""
DA3 批量处理脚本 - GPU 版本
处理整个数据集的深度估计，并与仿真深度对比

使用方法:
    conda activate bishe
    python batch_process_da3.py --dataset dataset/2026_03_13_01_50_19
"""

import os
import sys
import time
import glob
import json
import argparse
import torch
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime

# 添加 DA3 到路径
sys.path.insert(0, r'D:\ASVSim_models\Depth-Anything-3\src')
os.environ['HF_HOME'] = r'D:\ASVSim_models\cache\hub'

from depth_anything_3.api import DepthAnything3

# 配置
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_NAME = "depth-anything/DA3-LARGE-1.1"
BATCH_SIZE = 8  # 每批处理图像数 (根据显存调整)


def print_section(title):
    """打印章节标题"""
    print('\n' + '='*70)
    print(f'  {title}')
    print('='*70)


def load_model():
    """加载 DA3 模型"""
    print_section('Loading DA3 Model (GPU)')
    print(f'Device: {DEVICE}')
    print(f'Model: {MODEL_NAME}')

    try:
        model = DepthAnything3.from_pretrained(MODEL_NAME)
        model = model.to(device=DEVICE)
        model.eval()

        total_params = sum(p.numel() for p in model.parameters())
        print(f'[OK] Model loaded: {total_params / 1e6:.1f}M parameters')

        return model
    except Exception as e:
        print(f'[ERROR] Failed to load model: {e}')
        return None


def load_image_list(dataset_dir):
    """加载图像列表"""
    rgb_dir = os.path.join(dataset_dir, 'rgb')
    depth_dir = os.path.join(dataset_dir, 'depth')

    image_files = sorted(glob.glob(os.path.join(rgb_dir, '*.png')))

    if not image_files:
        print(f'[ERROR] No images found in: {rgb_dir}')
        return None

    print(f'Found {len(image_files)} images')
    return image_files


def process_batch(model, image_files, output_dir):
    """处理一批图像"""
    batch_start = time.time()

    try:
        # 运行推理
        with torch.no_grad():
            prediction = model.inference(image_files)

        batch_time = time.time() - batch_start
        per_image_time = batch_time / len(image_files)

        print(f'  Batch completed in {batch_time:.2f}s ({per_image_time:.3f}s/image)')

        # 保存结果
        results = []
        for i, img_path in enumerate(image_files):
            basename = os.path.basename(img_path).replace('.png', '')

            # 提取数据
            depth = prediction.depth[i]  # [H, W]
            conf = prediction.conf[i]    # [H, W]
            extrinsics = prediction.extrinsics[i]  # [3, 4]
            intrinsics = prediction.intrinsics[i]  # [3, 3]

            # 保存深度图 (可视化)
            depth_normalized = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
            depth_uint8 = (depth_normalized * 255).astype(np.uint8)
            depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_PLASMA)
            cv2.imwrite(os.path.join(output_dir, 'depth_vis', f'{basename}.png'), depth_colored)

            # 保存置信度图
            conf_uint8 = (np.clip(conf, 0, 1) * 255).astype(np.uint8)
            conf_colored = cv2.applyColorMap(conf_uint8, cv2.COLORMAP_VIRIDIS)
            cv2.imwrite(os.path.join(output_dir, 'conf_vis', f'{basename}.png'), conf_colored)

            # 保存原始数据
            np.save(os.path.join(output_dir, 'depth', f'{basename}.npy'), depth)
            np.save(os.path.join(output_dir, 'conf', f'{basename}.npy'), conf)
            np.save(os.path.join(output_dir, 'extrinsics', f'{basename}.npy'), extrinsics)
            np.save(os.path.join(output_dir, 'intrinsics', f'{basename}.npy'), intrinsics)

            results.append({
                'basename': basename,
                'depth_range': [float(depth.min()), float(depth.max())],
                'conf_range': [float(conf.min()), float(conf.max())],
                'shape': depth.shape
            })

        return results, batch_time

    except Exception as e:
        print(f'[ERROR] Batch processing failed: {e}')
        import traceback
        traceback.print_exc()
        return None, 0


def compare_with_simulation(dataset_dir, output_dir, processed_files):
    """对比 DA3 深度与仿真深度"""
    print_section('Comparing with Simulation Depth')

    sim_depth_dir = os.path.join(dataset_dir, 'depth')
    da3_depth_dir = os.path.join(output_dir, 'depth')

    comparison_results = []

    for item in processed_files:
        basename = item['basename']
        sim_depth_file = os.path.join(sim_depth_dir, f'{basename}.npy')
        da3_depth_file = os.path.join(da3_depth_dir, f'{basename}.npy')

        if not os.path.exists(sim_depth_file):
            print(f'  [SKIP] Simulation depth not found: {basename}')
            continue

        # 加载深度图
        sim_depth = np.load(sim_depth_file)
        da3_depth = np.load(da3_depth_file)

        # 仿真深度信息
        sim_valid = sim_depth[np.isfinite(sim_depth) & (sim_depth > 0)]
        sim_min = float(sim_valid.min()) if len(sim_valid) > 0 else 0
        sim_max = float(sim_valid.max()) if len(sim_valid) > 0 else 0

        # DA3 深度信息
        da3_min = float(da3_depth.min())
        da3_max = float(da3_depth.max())

        # 调整 DA3 深度大小以匹配仿真深度
        if da3_depth.shape != sim_depth.shape:
            da3_depth_resized = cv2.resize(da3_depth, (sim_depth.shape[1], sim_depth.shape[0]))
        else:
            da3_depth_resized = da3_depth

        # 计算有效区域的误差 (排除 inf 和 0)
        valid_mask = np.isfinite(sim_depth) & (sim_depth > 0) & (sim_depth < 100)
        if valid_mask.sum() > 0:
            # 计算尺度比例 (DA3 是绝对深度，但需要验证尺度)
            sim_mean = sim_depth[valid_mask].mean()
            da3_mean = da3_depth_resized[valid_mask].mean()
            scale_ratio = da3_mean / (sim_mean + 1e-8)

            # 对齐尺度后计算误差
            da3_aligned = da3_depth_resized / scale_ratio
            errors = np.abs(da3_aligned[valid_mask] - sim_depth[valid_mask])
            mean_error = float(errors.mean())
            std_error = float(errors.std())
            max_error = float(errors.max())
        else:
            scale_ratio = 0
            mean_error = 0
            std_error = 0
            max_error = 0

        comparison_results.append({
            'basename': basename,
            'sim_depth_range': [sim_min, sim_max],
            'da3_depth_range': [da3_min, da3_max],
            'scale_ratio': float(scale_ratio),
            'mean_error': mean_error,
            'std_error': std_error,
            'max_error': max_error
        })

        print(f'  {basename}:')
        print(f'    Sim: [{sim_min:.2f}, {sim_max:.2f}]')
        print(f'    DA3: [{da3_min:.2f}, {da3_max:.2f}]')
        print(f'    Scale ratio: {scale_ratio:.3f}')
        print(f'    Mean error: {mean_error:.3f}m')

    return comparison_results


def create_visualizations(dataset_dir, output_dir, num_samples=5):
    """创建对比可视化"""
    print_section('Creating Visualizations')

    rgb_dir = os.path.join(dataset_dir, 'rgb')
    sim_depth_dir = os.path.join(dataset_dir, 'depth')
    da3_depth_dir = os.path.join(output_dir, 'depth')
    vis_dir = os.path.join(output_dir, 'comparisons')
    os.makedirs(vis_dir, exist_ok=True)

    # 获取前 N 张图像
    image_files = sorted(glob.glob(os.path.join(rgb_dir, '*.png')))[:num_samples]

    for img_path in image_files:
        basename = os.path.basename(img_path).replace('.png', '')
        sim_depth_file = os.path.join(sim_depth_dir, f'{basename}.npy')
        da3_depth_file = os.path.join(da3_depth_dir, f'{basename}.npy')

        if not os.path.exists(sim_depth_file) or not os.path.exists(da3_depth_file):
            continue

        # 加载数据
        rgb = cv2.imread(img_path)
        sim_depth = np.load(sim_depth_file)
        da3_depth = np.load(da3_depth_file)

        # 调整 DA3 深度大小
        if da3_depth.shape != sim_depth.shape:
            da3_depth = cv2.resize(da3_depth, (sim_depth.shape[1], sim_depth.shape[0]))

        # 归一化仿真深度
        sim_valid = sim_depth[np.isfinite(sim_depth) & (sim_depth > 0)]
        if len(sim_valid) > 0:
            sim_norm = (sim_depth - sim_valid.min()) / (sim_valid.max() - sim_valid.min() + 1e-8)
        else:
            sim_norm = np.zeros_like(sim_depth)

        # 归一化 DA3 深度
        da3_norm = (da3_depth - da3_depth.min()) / (da3_depth.max() - da3_depth.min() + 1e-8)

        # 创建对比图
        h, w = sim_depth.shape
        comparison = np.zeros((h, w*3, 3), dtype=np.uint8)

        # RGB
        comparison[:, :w] = rgb

        # 仿真深度
        sim_colored = cv2.applyColorMap((np.clip(sim_norm, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        comparison[:, w:2*w] = sim_colored

        # DA3 深度
        da3_colored = cv2.applyColorMap((da3_norm * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        comparison[:, 2*w:3*w] = da3_colored

        # 添加标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison, 'RGB', (10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, 'Simulation', (w + 10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, 'DA3', (2*w + 10, 30), font, 1, (255, 255, 255), 2)

        # 保存
        cv2.imwrite(os.path.join(vis_dir, f'{basename}_comparison.png'), comparison)
        print(f'  Saved: {basename}_comparison.png')


def generate_report(output_dir, all_results, comparison_results, total_time):
    """生成处理报告"""
    print_section('Generating Report')

    report = {
        'timestamp': datetime.now().isoformat(),
        'device': str(DEVICE),
        'model': MODEL_NAME,
        'total_images': len(all_results),
        'total_time_seconds': total_time,
        'average_time_per_image': total_time / len(all_results) if all_results else 0,
        'depth_statistics': {
            'mean_min_depth': sum(r['depth_range'][0] for r in all_results) / len(all_results),
            'mean_max_depth': sum(r['depth_range'][1] for r in all_results) / len(all_results),
        },
        'comparison_statistics': {
            'mean_scale_ratio': sum(r['scale_ratio'] for r in comparison_results) / len(comparison_results) if comparison_results else 0,
            'mean_error': sum(r['mean_error'] for r in comparison_results) / len(comparison_results) if comparison_results else 0,
            'mean_std_error': sum(r['std_error'] for r in comparison_results) / len(comparison_results) if comparison_results else 0,
        },
        'per_image_results': comparison_results
    }

    report_file = os.path.join(output_dir, 'processing_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f'[OK] Report saved: {report_file}')
    return report


def main():
    parser = argparse.ArgumentParser(description='DA3 Batch Processing')
    parser.add_argument('--dataset', type=str, default='dataset/2026_03_13_01_50_19',
                        help='Path to dataset directory')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                        help='Batch size for processing')
    args = parser.parse_args()

    dataset_dir = args.dataset
    dataset_name = os.path.basename(dataset_dir)
    output_dir = os.path.join('test_output', f'da3_batch_{dataset_name}')

    # 创建输出目录
    for subdir in ['depth', 'depth_vis', 'conf', 'conf_vis', 'extrinsics', 'intrinsics', 'comparisons']:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    print('='*70)
    print(f'DA3 Batch Processing - {dataset_name}')
    print('='*70)
    print(f'Dataset: {dataset_dir}')
    print(f'Output: {output_dir}')
    print(f'Device: {DEVICE}')
    print(f'Batch size: {args.batch_size}')

    # 加载模型
    model = load_model()
    if model is None:
        return 1

    # 加载图像列表
    image_files = load_image_list(dataset_dir)
    if image_files is None:
        return 1

    # 批量处理
    print_section('Processing Images')
    all_results = []
    total_inference_time = 0

    num_batches = (len(image_files) + args.batch_size - 1) // args.batch_size
    for i in range(num_batches):
        start_idx = i * args.batch_size
        end_idx = min((i + 1) * args.batch_size, len(image_files))
        batch_files = image_files[start_idx:end_idx]

        print(f'\nBatch {i+1}/{num_batches} ({len(batch_files)} images)...')
        results, batch_time = process_batch(model, batch_files, output_dir)

        if results:
            all_results.extend(results)
            total_inference_time += batch_time

    print(f'\n[OK] Processed {len(all_results)} images in {total_inference_time:.2f}s')
    print(f'    Average: {total_inference_time/len(all_results):.3f}s/image')

    # 与仿真深度对比
    comparison_results = compare_with_simulation(dataset_dir, output_dir, all_results)

    # 创建可视化
    create_visualizations(dataset_dir, output_dir, num_samples=10)

    # 生成报告
    report = generate_report(output_dir, all_results, comparison_results, total_inference_time)

    # 总结
    print_section('Processing Summary')
    print(f'[SUCCESS] Batch processing completed!')
    print(f'  Dataset: {dataset_name}')
    print(f'  Images processed: {len(all_results)}')
    print(f'  Total time: {total_inference_time:.2f}s')
    print(f'  Average speed: {total_inference_time/len(all_results):.3f}s/image')
    print()
    print('Output directories:')
    print(f'  {output_dir}/depth/          - Raw depth maps (.npy)')
    print(f'  {output_dir}/depth_vis/       - Depth visualizations (.png)')
    print(f'  {output_dir}/conf/            - Confidence maps (.npy)')
    print(f'  {output_dir}/conf_vis/        - Confidence visualizations (.png)')
    print(f'  {output_dir}/extrinsics/      - Camera poses (.npy)')
    print(f'  {output_dir}/intrinsics/      - Camera intrinsics (.npy)')
    print(f'  {output_dir}/comparisons/     - Side-by-side comparisons (.png)')
    print(f'  {output_dir}/processing_report.json - Full report')

    return 0


if __name__ == '__main__':
    sys.exit(main())
