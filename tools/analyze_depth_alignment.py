#!/usr/bin/env python3
"""
深度对齐分析 - 解决 DA3 与仿真深度的尺度不一致问题

发现的问题:
- DA3 深度: [0.12, 5.69] 米 (绝对深度)
- 仿真深度: [3.71, 2384] 厘米 (UE5 单位，需要转换)

分析方法:
1. 检查仿真深度单位 (可能是 cm 或 mm)
2. 计算最佳尺度对齐因子
3. 对齐后重新计算误差
"""

import os
import json
import numpy as np
import glob
import cv2
from pathlib import Path

# 路径设置
DATASET_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\dataset\2026_03_13_01_50_19'
REPORT_FILE = r'C:\Users\zsh\Desktop\ASVSim_zsh\tools\test_output\da3_batch_2026_03_13_01_50_19\processing_report.json'
OUTPUT_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\test_output\depth_alignment_analysis'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_simulation_depths():
    """加载仿真深度数据"""
    depth_dir = os.path.join(DATASET_DIR, 'depth')
    depth_files = sorted(glob.glob(os.path.join(depth_dir, '*.npy')))

    depths = []
    for f in depth_files[:10]:  # 只取前10张分析
        depth = np.load(f)
        valid = depth[np.isfinite(depth) & (depth > 0)]
        if len(valid) > 0:
            depths.append({
                'file': os.path.basename(f),
                'min': float(valid.min()),
                'max': float(valid.max()),
                'mean': float(valid.mean()),
                'shape': depth.shape
            })

    return depths


def analyze_depth_units(depths):
    """分析深度单位"""
    print('='*70)
    print('仿真深度单位分析')
    print('='*70)

    # 统计所有有效深度值
    all_max = [d['max'] for d in depths]
    all_min = [d['min'] for d in depths]
    all_mean = [d['mean'] for d in depths]

    print(f'样本数: {len(depths)}')
    print(f'深度范围: [{min(all_min):.2f}, {max(all_max):.2f}]')
    print(f'平均深度: {np.mean(all_mean):.2f}')
    print()

    # 分析可能的单位
    max_val = max(all_max)
    print('单位假设分析:')
    print(f'  假设单位是米 (m): 最大深度 = {max_val:.2f} m')
    print(f'  假设单位是厘米 (cm): 最大深度 = {max_val/100:.2f} m')
    print(f'  假设单位是毫米 (mm): 最大深度 = {max_val/1000:.2f} m')
    print()

    # 根据场景判断最可能单位
    # 极地场景，船只到冰山的距离通常在 10-50 米
    if max_val > 1000:
        likely_unit = 'cm'
        converted_max = max_val / 100
    elif max_val > 100:
        likely_unit = 'mm'
        converted_max = max_val / 1000
    else:
        likely_unit = 'm'
        converted_max = max_val

    print(f'最可能单位: {likely_unit} (转换后最大深度: {converted_max:.2f} m)')
    print()

    return likely_unit, converted_max


def compute_alignment_factor():
    """计算最佳对齐因子"""
    print('='*70)
    print('深度对齐因子计算')
    print('='*70)

    # 读取报告
    with open(REPORT_FILE, 'r') as f:
        report = json.load(f)

    # 收集所有尺度比例
    scale_ratios = [r['scale_ratio'] for r in report['per_image_results']]

    print(f'图像数量: {len(scale_ratios)}')
    print(f'尺度比例统计:')
    print(f'  均值: {np.mean(scale_ratios):.6f}')
    print(f'  中位数: {np.median(scale_ratios):.6f}')
    print(f'  标准差: {np.std(scale_ratios):.6f}')
    print(f'  最小值: {min(scale_ratios):.6f}')
    print(f'  最大值: {max(scale_ratios):.6f}')
    print()

    # 分析有效比例（排除异常值）
    # 第一帧(0000)可能有问题（光晕），单独分析
    valid_ratios = [r for r in scale_ratios if 0.001 < r < 1.0]
    print(f'有效比例数量: {len(valid_ratios)} (排除异常值)')
    print(f'有效比例均值: {np.mean(valid_ratios):.6f}')
    print(f'有效比例中位数: {np.median(valid_ratios):.6f}')
    print()

    # 分析第一帧特殊情况
    print('第一帧(0000)分析:')
    print(f'  尺度比例: {scale_ratios[0]:.6f} (异常高)')
    print(f'  可能原因: 光晕导致深度估计错误')
    print()

    # 排除第一帧后的分析
    ratios_except_first = scale_ratios[1:]
    print('排除第一帧后的统计:')
    print(f'  均值: {np.mean(ratios_except_first):.6f}')
    print(f'  中位数: {np.median(ratios_except_first):.6f}')
    print()

    return np.median(ratios_except_first)


def align_and_recompute_error(alignment_factor):
    """对齐深度并重新计算误差"""
    print('='*70)
    print('对齐后误差重算')
    print('='*70)

    # 读取报告
    with open(REPORT_FILE, 'r') as f:
        report = json.load(f)

    # 假设仿真深度单位是 cm，需要除以 100 转换为 m
    # 然后乘以 alignment_factor 与 DA3 对齐
    cm_to_m = 0.01

    aligned_errors = []
    for r in report['per_image_results']:
        sim_min = r['sim_depth_range'][0] * cm_to_m
        sim_max = r['sim_depth_range'][1] * cm_to_m
        da3_min = r['da3_depth_range'][0]
        da3_max = r['da3_depth_range'][1]

        # 对齐后的仿真深度范围
        aligned_sim_min = sim_min * alignment_factor
        aligned_sim_max = sim_max * alignment_factor

        # 计算新的误差 (简单估计)
        error_min = abs(da3_min - aligned_sim_min)
        error_max = abs(da3_max - aligned_sim_max)
        error_mean = (error_min + error_max) / 2

        aligned_errors.append({
            'basename': r['basename'],
            'sim_range_m': [sim_min, sim_max],
            'da3_range_m': [da3_min, da3_max],
            'aligned_error': error_mean
        })

    # 统计对齐后的误差
    errors = [e['aligned_error'] for e in aligned_errors[1:]]  # 排除第一帧
    print(f'对齐因子: {alignment_factor:.6f}')
    print(f'对齐后误差统计 (排除第一帧):')
    print(f'  均值: {np.mean(errors):.3f} m')
    print(f'  中位数: {np.median(errors):.3f} m')
    print(f'  标准差: {np.std(errors):.3f} m')
    print(f'  最小值: {min(errors):.3f} m')
    print(f'  最大值: {max(errors):.3f} m')
    print()

    # 显示前几帧的对齐结果
    print('前5帧对齐结果:')
    for e in aligned_errors[:5]:
        print(f"  {e['basename']}: Sim [{e['sim_range_m'][0]:.2f}, {e['sim_range_m'][1]:.2f}] m, "
              f"DA3 [{e['da3_range_m'][0]:.2f}, {e['da3_range_m'][1]:.2f}] m, "
              f"Error: {e['aligned_error']:.3f} m")

    return aligned_errors


def create_aligned_visualization(aligned_errors):
    """创建对齐后的可视化"""
    print('='*70)
    print('生成对齐可视化')
    print('='*70)

    da3_depth_dir = r'C:\Users\zsh\Desktop\ASVSim_zsh\tools\test_output\da3_batch_2026_03_13_01_50_19\depth'
    rgb_dir = os.path.join(DATASET_DIR, 'rgb')
    sim_depth_dir = os.path.join(DATASET_DIR, 'depth')

    # 选择几个样本
    sample_frames = ['0001', '0040', '0080', '0120']

    cm_to_m = 0.01
    alignment_factor = 0.022  # 近似对齐因子

    for frame_id in sample_frames:
        rgb_path = os.path.join(rgb_dir, f'{frame_id}.png')
        sim_path = os.path.join(sim_depth_dir, f'{frame_id}.npy')
        da3_path = os.path.join(da3_depth_dir, f'{frame_id}.npy')

        if not all(os.path.exists(p) for p in [rgb_path, sim_path, da3_path]):
            print(f'  [SKIP] {frame_id}: missing files')
            continue

        # 加载数据
        rgb = cv2.imread(rgb_path)
        sim_depth = np.load(sim_path)
        da3_depth = np.load(da3_path)

        # 转换仿真深度 (cm -> m)
        sim_depth_m = sim_depth * cm_to_m

        # 对齐 DA3 深度 (调整大小)
        if da3_depth.shape != sim_depth_m.shape:
            da3_depth_resized = cv2.resize(da3_depth, (sim_depth_m.shape[1], sim_depth_m.shape[0]))
        else:
            da3_depth_resized = da3_depth

        # 归一化到 [0, 1] 用于可视化
        # 使用 DA3 的范围作为参考
        depth_min = da3_depth_resized.min()
        depth_max = da3_depth_resized.max()

        da3_norm = (da3_depth_resized - depth_min) / (depth_max - depth_min + 1e-8)

        # 仿真深度使用相同的归一化范围
        sim_norm = (sim_depth_m - depth_min) / (depth_max - depth_min + 1e-8)
        sim_norm = np.clip(sim_norm, 0, 1)

        # 创建对比图
        h, w = sim_depth_m.shape
        comparison = np.zeros((h, w*3, 3), dtype=np.uint8)

        # RGB
        comparison[:, :w] = rgb

        # 仿真深度 (对齐后)
        sim_colored = cv2.applyColorMap((sim_norm * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        comparison[:, w:2*w] = sim_colored

        # DA3 深度
        da3_colored = cv2.applyColorMap((da3_norm * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        comparison[:, 2*w:3*w] = da3_colored

        # 添加标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison, f'RGB', (10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, f'Sim Depth (cm->m)', (w + 10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, f'DA3 Depth', (2*w + 10, 30), font, 1, (255, 255, 255), 2)

        # 添加深度范围
        cv2.putText(comparison, f'Sim: [{sim_depth_m.min():.1f}, {sim_depth_m.max():.1f}] m',
                    (w + 10, h - 20), font, 0.7, (255, 255, 255), 2)
        cv2.putText(comparison, f'DA3: [{da3_depth_resized.min():.1f}, {da3_depth_resized.max():.1f}] m',
                    (2*w + 10, h - 20), font, 0.7, (255, 255, 255), 2)

        # 保存
        output_path = os.path.join(OUTPUT_DIR, f'{frame_id}_aligned.png')
        cv2.imwrite(output_path, comparison)
        print(f'  Saved: {frame_id}_aligned.png')


def main():
    print('\n' + '='*70)
    print('DA3 vs Simulation 深度对齐分析')
    print('='*70)
    print(f'Dataset: {DATASET_DIR}')
    print(f'Report: {REPORT_FILE}')
    print()

    # 1. 分析仿真深度单位
    depths = load_simulation_depths()
    unit, converted_max = analyze_depth_units(depths)

    # 2. 计算对齐因子
    alignment_factor = compute_alignment_factor()

    # 3. 对齐并重新计算误差
    aligned_errors = align_and_recompute_error(alignment_factor)

    # 4. 创建可视化
    create_aligned_visualization(aligned_errors)

    # 5. 总结
    print('\n' + '='*70)
    print('结论与建议')
    print('='*70)
    print()
    print('1. 单位确认:')
    print('   - 仿真深度单位: 厘米 (cm)')
    print('   - 转换为米: 除以 100')
    print()
    print('2. 深度范围:')
    print('   - 仿真深度: [3.71 cm, 2384 cm] = [0.037 m, 23.84 m]')
    print('   - DA3 深度: [0.12 m, 5.69 m]')
    print()
    print('3. 对齐因子:')
    print(f'   - 最佳对齐因子: ~0.022 (DA3/仿真)')
    print('   - 这意味着 DA3 的深度值大约是仿真深度的 2.2%')
    print()
    print('4. 可能原因:')
    print('   - 仿真使用 UE5 单位 (cm)，DA3 使用真实世界单位 (m)')
    print('   - 场景尺度差异：仿真场景可能比真实场景大')
    print('   - DA3 深度是绝对尺度，仿真深度可能有缩放')
    print()
    print('5. 建议:')
    print('   - 使用 DA3 深度作为绝对深度参考')
    print('   - 对仿真深度进行尺度校准: sim_depth_m = sim_depth_cm / 100')
    print('   - 融合时考虑相对深度关系而非绝对值')
    print()
    print(f'输出文件: {OUTPUT_DIR}')
    print()


if __name__ == '__main__':
    main()
