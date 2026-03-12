#!/usr/bin/env python3
"""
DA3 相机位姿验证分析
由于仿真位姿未保存，分析 DA3 预测位姿的合理性

分析内容:
1. 轨迹平滑性分析
2. 轨迹形状验证 (circle模式)
3. 位姿连续性检查
4. 相机运动参数估计
"""

import os
import sys
import glob
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 无GUI后端
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from scipy.spatial.transform import Rotation

# 配置
EXTRINSICS_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\tools\test_output\da3_batch_2026_03_13_01_50_19\extrinsics'
OUTPUT_DIR = r'C:\Users\zsh\Desktop\ASVSim_zsh\test_output\pose_analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_da3_poses():
    """加载 DA3 预测的位姿"""
    print('='*70)
    print('Loading DA3 Poses')
    print('='*70)

    pose_files = sorted(glob.glob(os.path.join(EXTRINSICS_DIR, '*.npy')))
    print(f'Found {len(pose_files)} pose files')

    poses = []
    for f in pose_files:
        # DA3 输出: [3, 4] 矩阵 (OpenCV format: [R | t])
        extrinsic = np.load(f)

        # 提取旋转和平移
        R = extrinsic[:3, :3]
        t = extrinsic[:3, 3]

        poses.append({
            'filename': os.path.basename(f),
            'rotation': R,
            'translation': t,
            'extrinsic': extrinsic
        })

    print(f'Loaded {len(poses)} poses')
    print(f'Pose shape: {extrinsic.shape}')
    print()

    return poses


def analyze_trajectory(poses):
    """分析相机轨迹"""
    print('='*70)
    print('Trajectory Analysis')
    print('='*70)

    # 提取位置
    positions = np.array([p['translation'] for p in poses])

    print(f'Position statistics:')
    print(f'  X range: [{positions[:, 0].min():.3f}, {positions[:, 0].max():.3f}]')
    print(f'  Y range: [{positions[:, 1].min():.3f}, {positions[:, 1].max():.3f}]')
    print(f'  Z range: [{positions[:, 2].min():.3f}, {positions[:, 2].max():.3f}]')
    print()

    # 计算相邻帧位移
    displacements = np.diff(positions, axis=0)
    step_sizes = np.linalg.norm(displacements, axis=1)

    print(f'Step size statistics:')
    print(f'  Mean: {step_sizes.mean():.4f} m')
    print(f'  Std: {step_sizes.std():.4f} m')
    print(f'  Min: {step_sizes.min():.4f} m')
    print(f'  Max: {step_sizes.max():.4f} m')
    print()

    # 计算总路径长度
    total_length = step_sizes.sum()
    print(f'Total trajectory length: {total_length:.2f} m')
    print()

    # 检查 Z 轴稳定性 (假设是水平运动)
    z_variance = positions[:, 2].var()
    print(f'Z-axis variance: {z_variance:.6f}')
    if z_variance < 0.01:
        print('  -> Z-axis is stable (horizontal motion)')
    else:
        print('  -> Z-axis has variation (vertical motion)')
    print()

    return positions, step_sizes


def analyze_rotation_smoothness(poses):
    """分析旋转平滑性"""
    print('='*70)
    print('Rotation Smoothness Analysis')
    print('='*70)

    # 提取旋转矩阵
    rotations = [p['rotation'] for p in poses]

    # 计算相邻帧旋转差异
    rotation_angles = []
    for i in range(1, len(rotations)):
        R1 = rotations[i-1]
        R2 = rotations[i]

        # 计算相对旋转
        R_rel = R1.T @ R2

        # 转换为旋转角度 (轴角表示)
        angle = np.arccos(np.clip((np.trace(R_rel) - 1) / 2, -1, 1))
        rotation_angles.append(np.degrees(angle))

    rotation_angles = np.array(rotation_angles)

    print(f'Rotation angle statistics (degrees):')
    print(f'  Mean: {rotation_angles.mean():.3f}°')
    print(f'  Std: {rotation_angles.std():.3f}°')
    print(f'  Min: {rotation_angles.min():.3f}°')
    print(f'  Max: {rotation_angles.max():.3f}°')
    print()

    # 检查旋转一致性
    if rotation_angles.std() < 5.0:
        print('  -> Rotation is smooth and consistent')
    else:
        print('  -> Rotation has large variations')
    print()

    return rotation_angles


def fit_circle_trajectory(positions):
    """拟合圆形轨迹"""
    print('='*70)
    print('Circle Trajectory Fitting')
    print('='*70)

    # 使用 XY 平面投影拟合圆
    x = positions[:, 0]
    y = positions[:, 1]

    # 圆拟合 (最小二乘法)
    # 圆方程: (x - cx)^2 + (y - cy)^2 = r^2
    # 展开: x^2 + y^2 - 2cx*x - 2cy*y + cx^2 + cy^2 - r^2 = 0

    A = np.column_stack([x, y, np.ones_like(x)])
    b = x**2 + y**2

    # 求解: [2cx, 2cy, cx^2 + cy^2 - r^2]
    coeffs, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)

    cx = coeffs[0] / 2
    cy = coeffs[1] / 2
    r = np.sqrt(cx**2 + cy**2 - coeffs[2])

    print(f'Fitted circle:')
    print(f'  Center: ({cx:.3f}, {cy:.3f})')
    print(f'  Radius: {r:.3f} m')
    print()

    # 计算拟合误差
    distances = np.sqrt((x - cx)**2 + (y - cy)**2)
    fit_error = np.abs(distances - r).mean()

    print(f'Fit quality:')
    print(f'  Mean error: {fit_error:.4f} m')
    print(f'  Error/Radius ratio: {fit_error/r*100:.2f}%')
    print()

    if fit_error/r < 0.1:  # 误差小于半径的 10%
        print('  -> Good circle fit! Trajectory is circular.')
    else:
        print('  -> Poor circle fit. Trajectory may not be circular.')
    print()

    return cx, cy, r, fit_error


def compute_camera_velocity(poses, step_sizes):
    """估算相机速度"""
    print('='*70)
    print('Camera Velocity Estimation')
    print('='*70)

    # 假设采集帧率 (根据采集配置中的 move_seconds=0.3)
    fps = 1.0 / 0.3  # ~3.33 FPS
    time_per_frame = 0.3  # 秒

    velocities = step_sizes / time_per_frame

    print(f'Assumed frame interval: {time_per_frame}s (from config)')
    print(f'Velocity statistics:')
    print(f'  Mean: {velocities.mean():.3f} m/s')
    print(f'  Std: {velocities.std():.3f} m/s')
    print(f'  Min: {velocities.min():.3f} m/s')
    print(f'  Max: {velocities.max():.3f} m/s')
    print()

    # 估算角速度 (如果是圆周运动)
    # v = ω * r -> ω = v / r
    # 使用平均速度
    avg_velocity = velocities.mean()

    # 使用前面的圆拟合结果
    x = np.array([p['translation'][0] for p in poses])
    y = np.array([p['translation'][1] for p in poses])
    A = np.column_stack([x, y, np.ones_like(x)])
    b = x**2 + y**2
    coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    cx = coeffs[0] / 2
    cy = coeffs[1] / 2
    r = np.sqrt(cx**2 + cy**2 - coeffs[2])

    angular_velocity = avg_velocity / r  # rad/s
    angular_velocity_deg = np.degrees(angular_velocity)

    print(f'Circular motion estimation:')
    print(f'  Radius: {r:.3f} m')
    print(f'  Angular velocity: {angular_velocity_deg:.3f}°/s')
    print(f'  Period: {360/angular_velocity_deg:.2f}s per revolution')
    print()

    return velocities, angular_velocity_deg


def visualize_trajectory(positions, poses):
    """可视化轨迹"""
    print('='*70)
    print('Generating Visualizations')
    print('='*70)

    # 1. 3D 轨迹图
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制轨迹
    ax.plot(positions[:, 0], positions[:, 1], positions[:, 2],
            'b-', linewidth=2, label='Trajectory')

    # 绘制起点和终点
    ax.scatter(*positions[0], c='green', s=100, marker='o', label='Start')
    ax.scatter(*positions[-1], c='red', s=100, marker='s', label='End')

    # 绘制相机方向 (每 10 帧)
    for i in range(0, len(poses), 10):
        pos = poses[i]['translation']
        R = poses[i]['rotation']
        # 相机朝向 (Z轴)
        direction = R[:, 2] * 0.5  # 缩放箭头长度
        ax.quiver(pos[0], pos[1], pos[2],
                  direction[0], direction[1], direction[2],
                  color='orange', alpha=0.5)

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title('DA3 Predicted Camera Trajectory (3D)')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'trajectory_3d.png'), dpi=150)
    print(f'  Saved: trajectory_3d.png')
    plt.close()

    # 2. 2D 俯视图
    fig, ax = plt.subplots(figsize=(10, 10))

    # 绘制 XY 平面轨迹
    ax.plot(positions[:, 0], positions[:, 1], 'b-', linewidth=2, label='Trajectory')
    ax.scatter(positions[0, 0], positions[0, 1], c='green', s=100, marker='o', label='Start')
    ax.scatter(positions[-1, 0], positions[-1, 1], c='red', s=100, marker='s', label='End')

    # 拟合圆
    x = positions[:, 0]
    y = positions[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    b = x**2 + y**2
    coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    cx = coeffs[0] / 2
    cy = coeffs[1] / 2
    r = np.sqrt(cx**2 + cy**2 - coeffs[2])

    # 绘制拟合圆
    theta = np.linspace(0, 2*np.pi, 100)
    ax.plot(cx + r*np.cos(theta), cy + r*np.sin(theta), 'r--', linewidth=2, label='Fitted Circle')
    ax.plot(cx, cy, 'r+', markersize=10, label='Circle Center')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Camera Trajectory (Top View)')
    ax.legend()
    ax.grid(True)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'trajectory_2d.png'), dpi=150)
    print(f'  Saved: trajectory_2d.png')
    plt.close()

    # 3. 各轴位置随时间变化
    fig, axes = plt.subplots(3, 1, figsize=(12, 8))

    frames = np.arange(len(positions))

    axes[0].plot(frames, positions[:, 0], 'b-', linewidth=1.5)
    axes[0].set_ylabel('X (m)')
    axes[0].set_title('Position vs Frame')
    axes[0].grid(True)

    axes[1].plot(frames, positions[:, 1], 'g-', linewidth=1.5)
    axes[1].set_ylabel('Y (m)')
    axes[1].grid(True)

    axes[2].plot(frames, positions[:, 2], 'r-', linewidth=1.5)
    axes[2].set_ylabel('Z (m)')
    axes[2].set_xlabel('Frame')
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'position_timeline.png'), dpi=150)
    print(f'  Saved: position_timeline.png')
    plt.close()

    # 4. 步长和旋转角度
    step_sizes = np.linalg.norm(np.diff(positions, axis=0), axis=1)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    axes[0].plot(step_sizes, 'b-', linewidth=1.5)
    axes[0].axhline(y=step_sizes.mean(), color='r', linestyle='--', label=f'Mean: {step_sizes.mean():.4f}m')
    axes[0].set_ylabel('Step Size (m)')
    axes[0].set_title('Motion Analysis')
    axes[0].legend()
    axes[0].grid(True)

    # 计算旋转角度
    rotation_angles = []
    for i in range(1, len(poses)):
        R1 = poses[i-1]['rotation']
        R2 = poses[i]['rotation']
        R_rel = R1.T @ R2
        angle = np.arccos(np.clip((np.trace(R_rel) - 1) / 2, -1, 1))
        rotation_angles.append(np.degrees(angle))

    axes[1].plot(rotation_angles, 'g-', linewidth=1.5)
    axes[1].axhline(y=np.mean(rotation_angles), color='r', linestyle='--',
                    label=f'Mean: {np.mean(rotation_angles):.3f}°')
    axes[1].set_ylabel('Rotation Angle (°)')
    axes[1].set_xlabel('Frame')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'motion_analysis.png'), dpi=150)
    print(f'  Saved: motion_analysis.png')
    plt.close()

    print()


def generate_report(poses, positions, step_sizes, rotation_angles, cx, cy, r, fit_error):
    """生成验证报告"""
    print('='*70)
    print('Generating Validation Report')
    print('='*70)

    # 计算统计指标
    report = {
        'total_frames': len(poses),
        'trajectory_analysis': {
            'position_range': {
                'x': [float(positions[:, 0].min()), float(positions[:, 0].max())],
                'y': [float(positions[:, 1].min()), float(positions[:, 1].max())],
                'z': [float(positions[:, 2].min()), float(positions[:, 2].max())],
            },
            'step_size': {
                'mean': float(step_sizes.mean()),
                'std': float(step_sizes.std()),
                'min': float(step_sizes.min()),
                'max': float(step_sizes.max())
            },
            'total_length': float(step_sizes.sum()),
            'z_variance': float(positions[:, 2].var())
        },
        'rotation_analysis': {
            'mean_angle': float(rotation_angles.mean()),
            'std_angle': float(rotation_angles.std()),
            'max_angle': float(rotation_angles.max())
        },
        'circle_fitting': {
            'center': [float(cx), float(cy)],
            'radius': float(r),
            'mean_error': float(fit_error),
            'error_ratio': float(fit_error / r * 100)
        },
        'quality_assessment': {
            'trajectory_smoothness': 'good' if step_sizes.std() / step_sizes.mean() < 0.5 else 'fair',
            'rotation_consistency': 'good' if rotation_angles.std() < 5.0 else 'fair',
            'circle_fit_quality': 'good' if fit_error / r < 0.1 else 'fair'
        }
    }

    # 保存报告
    report_path = os.path.join(OUTPUT_DIR, 'pose_validation_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f'[OK] Report saved: {report_path}')
    print()

    return report


def print_summary(report):
    """打印总结"""
    print('='*70)
    print('DA3 Pose Validation Summary')
    print('='*70)
    print()

    print('1. Trajectory Statistics:')
    print(f'   Total frames: {report["total_frames"]}')
    print(f'   Trajectory length: {report["trajectory_analysis"]["total_length"]:.2f} m')
    print(f'   Step size: {report["trajectory_analysis"]["step_size"]["mean"]:.4f} ± '
          f'{report["trajectory_analysis"]["step_size"]["std"]:.4f} m')
    print()

    print('2. Circle Fitting:')
    print(f'   Center: ({report["circle_fitting"]["center"][0]:.3f}, '
          f'{report["circle_fitting"]["center"][1]:.3f})')
    print(f'   Radius: {report["circle_fitting"]["radius"]:.3f} m')
    print(f'   Fit error: {report["circle_fitting"]["mean_error"]:.4f} m '
          f'({report["circle_fitting"]["error_ratio"]:.2f}%)')
    print()

    print('3. Quality Assessment:')
    print(f'   Trajectory smoothness: {report["quality_assessment"]["trajectory_smoothness"]}')
    print(f'   Rotation consistency: {report["quality_assessment"]["rotation_consistency"]}')
    print(f'   Circle fit quality: {report["quality_assessment"]["circle_fit_quality"]}')
    print()

    print('4. Conclusion:')
    qualities = report['quality_assessment']
    good_count = sum(1 for v in qualities.values() if v == 'good')
    if good_count == 3:
        print('   [OK] DA3 predicted poses are HIGH QUALITY')
        print('      - Smooth trajectory')
        print('      - Consistent rotation')
        print('      - Matches expected circle pattern')
    elif good_count >= 2:
        print('   [OK] DA3 predicted poses are ACCEPTABLE')
        print('      - Minor issues but usable')
    else:
        print('   [WARN] DA3 predicted poses have ISSUES')
        print('      - Recommend using simulation poses instead')
    print()

    print(f'5. Output files:')
    print(f'   {OUTPUT_DIR}/')
    print(f'   ├── trajectory_3d.png')
    print(f'   ├── trajectory_2d.png')
    print(f'   ├── position_timeline.png')
    print(f'   ├── motion_analysis.png')
    print(f'   └── pose_validation_report.json')
    print()


def main():
    print('\n' + '='*70)
    print('DA3 Camera Pose Validation')
    print('='*70)
    print()

    # 1. 加载位姿
    poses = load_da3_poses()

    # 2. 分析轨迹
    positions, step_sizes = analyze_trajectory(poses)

    # 3. 分析旋转平滑性
    rotation_angles = analyze_rotation_smoothness(poses)

    # 4. 拟合圆形轨迹
    cx, cy, r, fit_error = fit_circle_trajectory(positions)

    # 5. 估算速度
    velocities, angular_velocity = compute_camera_velocity(poses, step_sizes)

    # 6. 可视化
    visualize_trajectory(positions, poses)

    # 7. 生成报告
    report = generate_report(poses, positions, step_sizes, rotation_angles, cx, cy, r, fit_error)

    # 8. 打印总结
    print_summary(report)


if __name__ == '__main__':
    main()
