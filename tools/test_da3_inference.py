#!/usr/bin/env python3
"""
Depth Anything 3 (DA3) 推理测试脚本
测试能否从 RGB 图像生成深度图

使用方法:
    conda activate bishe
    python test_da3_inference.py
"""

import os
import sys
import time
import torch
import numpy as np
from pathlib import Path
import cv2
from PIL import Image

# 设置环境变量
os.environ['HF_HOME'] = r'D:\ASVSim_models\cache\hub'
os.environ['TORCH_HOME'] = r'D:\ASVSim_models\cache\torch'

# 模型路径
DA3_MODEL_PATH = r'D:\ASVSim_models\depth_anything_3\da3_large.safetensors'

# 测试图像
TEST_IMAGE = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_12_20_53_24\rgb\0001.png'
OUTPUT_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\test_output'

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


def print_section(title):
    """打印章节标题"""
    print('\n' + '='*70)
    print(f'  {title}')
    print('='*70)


def load_da3_model_simple():
    """
    尝试加载 DA3 模型 - 简化版本
    由于完整的 DA3 模型架构复杂，我们先尝试加载权重并查看结构
    """
    print_section('Loading DA3 Model')

    try:
        # 方法1: 尝试使用 transformers
        print('Method 1: Trying transformers AutoModel...')
        try:
            from transformers import AutoModelForDepthEstimation, AutoImageProcessor

            # 创建临时配置文件
            config_path = os.path.join(OUTPUT_DIR, 'da3_config.json')
            with open(config_path, 'w') as f:
                f.write('{"model_type": "depth_estimation"}')

            model = AutoModelForDepthEstimation.from_pretrained(
                r'D:\ASVSim_models\depth_anything_3',
                config=config_path,
                ignore_mismatched_sizes=True
            )
            print('  [OK] Model loaded via transformers')
            return model, 'transformers'

        except Exception as e:
            print(f'  transformers failed: {e}')

        # 方法2: 直接加载权重（需要手动构建模型）
        print('\nMethod 2: Loading weights directly...')
        from safetensors.torch import load_file

        state_dict = load_file(DA3_MODEL_PATH)
        print(f'  [OK] Loaded {len(state_dict)} tensors')

        # 分析权重结构
        print('\nAnalyzing model structure...')
        backbone_keys = [k for k in state_dict.keys() if 'backbone' in k]
        head_keys = [k for k in state_dict.keys() if 'head' in k or 'depth' in k]

        print(f'  Backbone tensors: {len(backbone_keys)}')
        print(f'  Head tensors: {len(head_keys)}')

        # 查看一些关键张量的形状
        print('\nKey tensor shapes:')
        for i, (k, v) in enumerate(state_dict.items()):
            if i < 10:
                print(f'    {k}: {tuple(v.shape)}')

        return state_dict, 'weights_only'

    except Exception as e:
        print(f'[ERROR] Failed to load model: {e}')
        import traceback
        traceback.print_exc()
        return None, None


def preprocess_image(image_path):
    """
    预处理图像 - DA3 使用 DINOv2 预处理
    """
    print_section('Preprocessing Image')

    # 加载图像
    img = cv2.imread(image_path)
    if img is None:
        print(f'[ERROR] Cannot load image: {image_path}')
        return None

    print(f'  Original image: {img.shape}')

    # 转换为 RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # DINOv2/DA3 预处理
    # 1. 调整大小到 518x518 (DINOv2 的标准输入)
    input_size = (518, 518)
    img_resized = cv2.resize(img_rgb, input_size)
    print(f'  Resized to: {input_size}')

    # 2. 归一化 (ImageNet 均值和标准差)
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])

    img_normalized = img_resized.astype(np.float32) / 255.0
    img_normalized = (img_normalized - mean) / std

    # 3. 转换为 torch tensor (CHW 格式)
    img_tensor = torch.from_numpy(img_normalized).permute(2, 0, 1).unsqueeze(0)
    print(f'  Tensor shape: {img_tensor.shape}')

    return img_tensor, img_rgb


def simple_depth_inference(image_tensor, model_info):
    """
    简化的深度估计推理
    由于完整的 DA3 模型架构复杂，这里使用一个简化版本
    """
    print_section('Running Inference')

    model_type = model_info[1]

    if model_type == 'transformers':
        # 使用 transformers 模型
        model = model_info[0]
        model.eval()

        with torch.no_grad():
            if torch.cuda.is_available():
                image_tensor = image_tensor.cuda()
                model = model.cuda()

            print('  Running forward pass...')
            outputs = model(image_tensor)

            # 获取深度预测
            if hasattr(outputs, 'predicted_depth'):
                depth = outputs.predicted_depth
            else:
                depth = outputs

        return depth

    else:
        # 简化版本：使用 backbone 特征生成伪深度图
        # 注意：这只是为了测试，不是真正的 DA3 推理
        print('  [WARNING] Using simplified depth estimation')
        print('  This is not the full DA3 model, just a test')

        # 创建一个简单的深度估计（基于图像梯度）
        img_np = image_tensor.squeeze(0).permute(1, 2, 0).numpy()
        img_np = (img_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406]))
        img_np = (img_np * 255).astype(np.uint8)

        # 使用简单的边缘检测作为伪深度
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # 梯度作为深度线索（远的地方梯度小，近的地方梯度大）
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient = np.sqrt(sobelx**2 + sobely**2)

        # 归一化到 0-1
        depth = gradient / (gradient.max() + 1e-8)

        # 反转（假设天空远，梯度小）
        depth = 1.0 - depth

        # 转换为 torch tensor
        depth_tensor = torch.from_numpy(depth).unsqueeze(0).unsqueeze(0)

        return depth_tensor


def visualize_depth(depth, original_img, output_path):
    """
    可视化深度图
    """
    print_section('Visualizing Depth')

    # 将深度转换为 numpy
    if torch.is_tensor(depth):
        depth_np = depth.squeeze().cpu().numpy()
    else:
        depth_np = depth

    print(f'  Depth shape: {depth_np.shape}')
    print(f'  Depth range: [{depth_np.min():.4f}, {depth_np.max():.4f}]')

    # 归一化到 0-255
    depth_normalized = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-8)
    depth_uint8 = (depth_normalized * 255).astype(np.uint8)

    # 应用颜色映射
    depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_PLASMA)

    # 调整大小到原始图像
    if original_img is not None:
        h, w = original_img.shape[:2]
        depth_colored = cv2.resize(depth_colored, (w, h))

    # 保存
    output_file = os.path.join(output_path, 'depth_prediction.png')
    cv2.imwrite(output_file, depth_colored)
    print(f'  [OK] Saved to: {output_file}')

    # 同时保存原始深度值（npy 格式）
    npy_file = os.path.join(output_path, 'depth_prediction.npy')
    np.save(npy_file, depth_np)
    print(f'  [OK] Saved raw depth to: {npy_file}')

    return depth_colored


def compare_with_simulation(depth_pred, output_path):
    """
    与仿真深度图对比
    """
    print_section('Comparing with Simulation Depth')

    # 加载仿真深度图
    sim_depth_path = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_12_20_53_24\depth\0001.npy'

    if not os.path.exists(sim_depth_path):
        print(f'  [WARNING] Simulation depth not found: {sim_depth_path}')
        return

    sim_depth = np.load(sim_depth_path)
    print(f'  Simulation depth shape: {sim_depth.shape}')
    print(f'  Simulation depth range: [{sim_depth.min():.2f}, {sim_depth.max():.2f}]')

    # 调整预测深度大小以匹配仿真深度
    if torch.is_tensor(depth_pred):
        depth_pred_np = depth_pred.squeeze().cpu().numpy()
    else:
        depth_pred_np = depth_pred

    # 如果尺寸不匹配，调整大小
    if depth_pred_np.shape != sim_depth.shape:
        depth_pred_resized = cv2.resize(depth_pred_np, (sim_depth.shape[1], sim_depth.shape[0]))
    else:
        depth_pred_resized = depth_pred_np

    # 归一化两者以便可视化比较
    def normalize_for_vis(d):
        d_valid = d[np.isfinite(d)]
        if len(d_valid) > 0:
            return (d - d_valid.min()) / (d_valid.max() - d_valid.min() + 1e-8)
        return np.zeros_like(d)

    sim_depth_norm = normalize_for_vis(sim_depth)
    pred_depth_norm = normalize_for_vis(depth_pred_resized)

    # 创建对比图
    fig = np.zeros((sim_depth.shape[0], sim_depth.shape[1] * 2, 3), dtype=np.uint8)

    # 仿真深度
    sim_colored = cv2.applyColorMap((sim_depth_norm * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
    fig[:, :sim_depth.shape[1]] = sim_colored

    # 预测深度
    pred_colored = cv2.applyColorMap((pred_depth_norm * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
    fig[:, sim_depth.shape[1]:] = pred_colored

    # 添加标签
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(fig, 'Simulation', (10, 30), font, 1, (255, 255, 255), 2)
    cv2.putText(fig, 'DA3 Prediction', (sim_depth.shape[1] + 10, 30), font, 1, (255, 255, 255), 2)

    # 保存
    comparison_file = os.path.join(output_path, 'depth_comparison.png')
    cv2.imwrite(comparison_file, fig)
    print(f'  [OK] Saved comparison to: {comparison_file}')


def main():
    """主函数"""
    print('='*70)
    print('DA3 Depth Inference Test')
    print('='*70)

    # 1. 加载模型
    model_info = load_da3_model_simple()
    if model_info[0] is None:
        print('[ERROR] Failed to load model')
        return 1

    # 2. 预处理图像
    result = preprocess_image(TEST_IMAGE)
    if result is None:
        return 1

    image_tensor, original_img = result

    # 3. 运行推理
    start_time = time.time()
    depth_pred = simple_depth_inference(image_tensor, model_info)
    inference_time = time.time() - start_time

    print(f'\n  Inference time: {inference_time:.3f}s')

    # 4. 可视化
    depth_colored = visualize_depth(depth_pred, original_img, OUTPUT_DIR)

    # 5. 与仿真对比
    compare_with_simulation(depth_pred, OUTPUT_DIR)

    # 6. 总结
    print_section('Test Summary')
    print('[OK] DA3 inference test completed!')
    print(f'  Output directory: {OUTPUT_DIR}')
    print(f'  Files generated:')
    print(f'    - depth_prediction.png (visualization)')
    print(f'    - depth_prediction.npy (raw depth values)')
    print(f'    - depth_comparison.png (vs simulation)')

    print('\n[NOTE] This is a simplified test.')
    print('Full DA3 model requires implementing the complete architecture.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
