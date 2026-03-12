#!/usr/bin/env python3
"""
SAM 3 海冰实例分割 - 批量处理
使用 Ultralytics 接口加载 SAM 3 模型

使用方法:
    conda activate bishe
    python batch_segment_sam3.py --dataset dataset/2026_03_13_01_50_19
"""

import os
import sys
import time
import glob
import json
import argparse
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime

# 配置
MODEL_PATH = r'D:\ASVSim_models\sam3\sam3.pt'
DEVICE = 'cuda'  # 或 'cpu'
CONF_THRESH = 0.5  # 置信度阈值


def print_section(title):
    """打印章节标题"""
    print('\n' + '='*70)
    print(f'  {title}')
    print('='*70)


def check_model():
    """检查模型文件"""
    print_section('Checking SAM 3 Model')

    if not os.path.exists(MODEL_PATH):
        print(f'[ERROR] Model not found: {MODEL_PATH}')
        print('Please download SAM 3 from Hugging Face:')
        print('  https://huggingface.co/facebook/sam3')
        return False

    size_mb = os.path.getsize(MODEL_PATH) / (1024**2)
    print(f'[OK] Model found: {MODEL_PATH}')
    print(f'   Size: {size_mb:.1f} MB')
    return True


def load_model():
    """加载 SAM 3 模型"""
    print_section('Loading SAM 3 Model')

    try:
        # 尝试使用 Ultralytics
        from ultralytics import SAM

        print(f'Loading from: {MODEL_PATH}')
        print(f'Device: {DEVICE}')

        model = SAM(MODEL_PATH)
        model.to(device=DEVICE)

        print('[OK] SAM 3 loaded successfully')
        return model

    except ImportError:
        print('[ERROR] Ultralytics not installed.')
        print('Install with: pip install -U ultralytics>=8.3.237')
        return None

    except Exception as e:
        print(f'[ERROR] Failed to load model: {e}')
        return None


def load_images(dataset_dir):
    """加载图像列表"""
    rgb_dir = os.path.join(dataset_dir, 'rgb')
    image_files = sorted(glob.glob(os.path.join(rgb_dir, '*.png')))

    if not image_files:
        print(f'[ERROR] No images found in: {rgb_dir}')
        return None

    print(f'Found {len(image_files)} images')
    return image_files


def segment_image(model, image_path, output_dir):
    """分割单张图像"""
    try:
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            print(f'  [ERROR] Failed to load: {image_path}')
            return None

        basename = os.path.basename(image_path).replace('.png', '')

        # 运行分割
        start_time = time.time()
        results = model(image, verbose=False)
        inference_time = time.time() - start_time

        # 提取分割结果
        result = results[0]

        # 获取 masks
        if hasattr(result, 'masks') and result.masks is not None:
            masks = result.masks.data.cpu().numpy() if hasattr(result.masks.data, 'cpu') else result.masks.data.numpy()
        else:
            masks = np.array([])

        # 获取 boxes 和 scores
        if hasattr(result, 'boxes') and result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy() if hasattr(result.boxes.xyxy, 'cpu') else result.boxes.xyxy.numpy()
            scores = result.boxes.conf.cpu().numpy() if hasattr(result.boxes.conf, 'cpu') else result.boxes.conf.numpy()
        else:
            boxes = np.array([])
            scores = np.array([])

        # 过滤低置信度
        if len(scores) > 0:
            valid_idx = scores > CONF_THRESH
            masks = masks[valid_idx] if len(masks) > 0 else masks
            boxes = boxes[valid_idx] if len(boxes) > 0 else boxes
            scores = scores[valid_idx]

        num_instances = len(masks) if len(masks) > 0 else 0

        # 创建实例掩码图 (每个像素为实例ID)
        h, w = image.shape[:2]
        instance_mask = np.zeros((h, w), dtype=np.int32)

        if num_instances > 0:
            # 调整 mask 大小并合并
            for i, mask in enumerate(masks):
                if mask.shape != (h, w):
                    mask_resized = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
                else:
                    mask_resized = mask.astype(np.uint8)

                instance_mask[mask_resized > 0] = i + 1

        # 保存结果
        # 1. 实例掩码
        np.save(os.path.join(output_dir, 'segmentation', f'{basename}.npy'), instance_mask)

        # 2. 可视化
        vis_image = create_visualization(image, masks, boxes, scores)
        cv2.imwrite(os.path.join(output_dir, 'segmentation_vis', f'{basename}.png'), vis_image)

        return {
            'basename': basename,
            'num_instances': num_instances,
            'inference_time': inference_time,
            'mean_score': float(scores.mean()) if len(scores) > 0 else 0
        }

    except Exception as e:
        print(f'  [ERROR] Segmentation failed: {e}')
        import traceback
        traceback.print_exc()
        return None


def create_visualization(image, masks, boxes, scores):
    """创建分割可视化"""
    vis = image.copy()
    h, w = image.shape[:2]

    # 生成随机颜色
    np.random.seed(42)
    colors = np.random.randint(0, 255, (100, 3), dtype=np.uint8)

    if len(masks) == 0:
        return vis

    # 创建彩色掩码叠加
    overlay = np.zeros_like(vis)

    for i, mask in enumerate(masks):
        if mask.shape != (h, w):
            mask_resized = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            mask_resized = mask.astype(np.uint8)

        color = colors[i % len(colors)].tolist()
        overlay[mask_resized > 0] = color

        # 绘制边界框
        if i < len(boxes):
            x1, y1, x2, y2 = boxes[i].astype(int)
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

            # 绘制置信度
            if i < len(scores):
                score = scores[i]
                label = f'{score:.2f}'
                cv2.putText(vis, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # 混合原图和掩码
    vis = cv2.addWeighted(vis, 0.6, overlay, 0.4, 0)

    return vis


def process_batch(model, image_files, output_dir):
    """批量处理图像"""
    print_section('Segmenting Images')

    results = []
    total_time = 0

    for i, img_path in enumerate(image_files):
        print(f'  [{i+1}/{len(image_files)}] {os.path.basename(img_path)}...', end=' ')

        result = segment_image(model, img_path, output_dir)

        if result:
            results.append(result)
            total_time += result['inference_time']
            print(f'{result["num_instances"]} instances, {result["inference_time"]:.3f}s')
        else:
            print('FAILED')

    return results, total_time


def generate_report(results, total_time, output_dir):
    """生成处理报告"""
    print_section('Generating Report')

    if not results:
        print('[ERROR] No successful segmentations')
        return

    num_instances = [r['num_instances'] for r in results]
    inference_times = [r['inference_time'] for r in results]

    report = {
        'timestamp': datetime.now().isoformat(),
        'model': MODEL_PATH,
        'device': DEVICE,
        'total_images': len(results),
        'total_time_seconds': total_time,
        'average_time_per_image': total_time / len(results),
        'instance_statistics': {
            'total_instances': sum(num_instances),
            'mean_per_image': sum(num_instances) / len(num_instances),
            'max_per_image': max(num_instances),
            'min_per_image': min(num_instances)
        },
        'per_image_results': results
    }

    report_path = os.path.join(output_dir, 'segmentation_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f'[OK] Report saved: {report_path}')
    return report


def print_summary(report):
    """打印总结"""
    print_section('Segmentation Summary')

    print(f'[SUCCESS] Segmentation completed!')
    print(f'  Images processed: {report["total_images"]}')
    print(f'  Total instances: {report["instance_statistics"]["total_instances"]}')
    print(f'  Instances per image: {report["instance_statistics"]["mean_per_image"]:.1f}')
    print(f'  Total time: {report["total_time_seconds"]:.2f}s')
    print(f'  Average speed: {report["average_time_per_image"]:.3f}s/image')
    print()
    print('Output directories:')
    print(f'  {report["output_dir"]}/segmentation/       - Instance masks (.npy)')
    print(f'  {report["output_dir"]}/segmentation_vis/   - Visualizations (.png)')


def main():
    parser = argparse.ArgumentParser(description='SAM 3 Batch Segmentation')
    parser.add_argument('--dataset', type=str, default='dataset/2026_03_13_01_50_19',
                        help='Path to dataset directory')
    parser.add_argument('--conf', type=float, default=CONF_THRESH,
                        help='Confidence threshold')
    args = parser.parse_args()

    dataset_dir = args.dataset
    dataset_name = os.path.basename(dataset_dir)
    output_dir = os.path.join('test_output', f'sam3_batch_{dataset_name}')

    # 创建输出目录
    os.makedirs(os.path.join(output_dir, 'segmentation'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'segmentation_vis'), exist_ok=True)

    print('='*70)
    print(f'SAM 3 Batch Segmentation - {dataset_name}')
    print('='*70)
    print(f'Dataset: {dataset_dir}')
    print(f'Output: {output_dir}')
    print(f'Model: {MODEL_PATH}')
    print(f'Confidence threshold: {args.conf}')

    # 检查模型
    if not check_model():
        return 1

    # 加载模型
    model = load_model()
    if model is None:
        return 1

    # 加载图像
    image_files = load_images(dataset_dir)
    if image_files is None:
        return 1

    # 只处理前20张（快速测试）
    image_files = image_files[:20]
    print(f'Using first {len(image_files)} images for quick test')

    # 批量处理
    results, total_time = process_batch(model, image_files, output_dir)

    if not results:
        print('[ERROR] No images processed successfully')
        return 1

    # 生成报告
    report = generate_report(results, total_time, output_dir)
    report['output_dir'] = output_dir

    # 打印总结
    print_summary(report)

    return 0


if __name__ == '__main__':
    sys.exit(main())
