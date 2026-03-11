"""
数据验证工具 — 检查采集的数据集质量
========================================

功能：
1. 验证文件完整性（RGB/Depth/LiDAR数量匹配）
2. 检查图像质量（分辨率、像素范围、损坏检测）
3. 验证深度图有效性（范围、NaN比例）
4. 检查位姿连续性（防止过大跳跃）
5. 生成质量报告

使用：
    python validate_dataset.py <dataset_path>

示例：
    python validate_dataset.py dataset/2026_03_12_10_30_00
"""

import numpy as np
import cv2
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def validate_file_counts(dataset_path: Path) -> Tuple[bool, Dict]:
    """验证文件数量匹配"""
    rgb_files = sorted(list((dataset_path / "rgb").glob("*.png")))
    depth_files = sorted(list((dataset_path / "depth").glob("*.npy")))
    lidar_files = sorted(list((dataset_path / "lidar").glob("*.json")))

    counts = {
        "rgb": len(rgb_files),
        "depth": len(depth_files),
        "lidar": len(lidar_files),
    }

    # 检查poses.json
    poses_path = dataset_path / "poses.json"
    if poses_path.exists():
        with open(poses_path, "r") as f:
            poses = json.load(f)
        counts["poses"] = len(poses)
    else:
        counts["poses"] = 0

    # 验证一致性
    values = [v for k, v in counts.items() if k != "poses"]
    is_valid = len(set(values)) == 1 and counts["poses"] == values[0]

    return is_valid, counts


def validate_image_quality(img_path: Path, expected_size: Tuple[int, int]) -> Dict:
    """验证单张图像质量"""
    img = cv2.imread(str(img_path))

    if img is None:
        return {"valid": False, "error": "无法读取图像"}

    h, w = img.shape[:2]
    eh, ew = expected_size

    issues = []

    # 尺寸检查
    if h != eh or w != ew:
        issues.append(f"尺寸不匹配: ({h},{w}) vs ({eh},{ew})")

    # 像素范围检查
    if img.min() < 0 or img.max() > 255:
        issues.append(f"像素值越界: [{img.min()}, {img.max()}]")

    # 全黑/全白检查
    if img.max() < 10:
        issues.append("图像接近全黑")
    if img.min() > 250:
        issues.append("图像接近全白")

    return {
        "valid": len(issues) == 0,
        "shape": (h, w),
        "range": (int(img.min()), int(img.max())),
        "issues": issues,
    }


def validate_depth_quality(depth_path: Path) -> Dict:
    """验证深度图质量"""
    try:
        depth = np.load(str(depth_path))
    except Exception as e:
        return {"valid": False, "error": f"无法读取: {e}"}

    issues = []

    # 统计
    total_pixels = depth.size
    valid_mask = np.isfinite(depth) & (depth > 0) & (depth < 1000)
    valid_pixels = np.sum(valid_mask)
    nan_ratio = 1 - (valid_pixels / total_pixels)

    if valid_pixels > 0:
        valid_depth = depth[valid_mask]
        depth_min = float(valid_depth.min())
        depth_max = float(valid_depth.max())
        depth_mean = float(valid_depth.mean())
    else:
        depth_min = depth_max = depth_mean = 0
        issues.append("无有效深度值")

    # 有效性检查
    if nan_ratio > 0.5:
        issues.append(f"NaN比例过高: {nan_ratio*100:.1f}%")

    if valid_pixels > 0:
        if depth_max > 200:  # 超过200m可能有问题
            issues.append(f"深度值过大: {depth_max:.1f}m")

    return {
        "valid": len(issues) == 0,
        "shape": depth.shape,
        "nan_ratio": nan_ratio,
        "depth_range": (depth_min, depth_max),
        "mean_depth": depth_mean,
        "issues": issues,
    }


def validate_pose_continuity(poses: List[Dict], max_jump: float = 10.0) -> Dict:
    """验证位姿连续性"""
    issues = []
    large_jumps = []

    for i in range(1, len(poses)):
        p0 = poses[i-1]["position"]
        p1 = poses[i]["position"]

        dist = np.sqrt(
            (p1["x"] - p0["x"])**2 +
            (p1["y"] - p0["y"])**2 +
            (p1["z"] - p0["z"])**2
        )

        if dist > max_jump:
            large_jumps.append((i, dist))
            if len(large_jumps) <= 3:  # 只记录前3个
                issues.append(f"帧{i-1}→{i}位姿跳跃过大: {dist:.2f}m")

    return {
        "valid": len(large_jumps) == 0,
        "total_jumps": len(large_jumps),
        "issues": issues,
    }


def validate_dataset(dataset_path: Path) -> Dict:
    """完整数据集验证"""
    print(f"\n{'='*60}")
    print(f"  数据集验证: {dataset_path.name}")
    print(f"{'='*60}\n")

    results = {
        "path": str(dataset_path),
        "valid": True,
        "checks": {},
    }

    # 1. 文件数量检查
    print("[1/4] 文件数量检查...")
    file_valid, counts = validate_file_counts(dataset_path)
    results["checks"]["file_counts"] = {"valid": file_valid, "counts": counts}
    print(f"      RGB: {counts.get('rgb', 0)}")
    print(f"      Depth: {counts.get('depth', 0)}")
    print(f"      LiDAR: {counts.get('lidar', 0)}")
    print(f"      Poses: {counts.get('poses', 0)}")
    print(f"      状态: {'通过 ✓' if file_valid else '失败 ✗'}")

    if not file_valid:
        results["valid"] = False

    # 2. 图像质量检查（抽检前5帧）
    print("\n[2/4] 图像质量检查（抽检前5帧）...")
    rgb_dir = dataset_path / "rgb"
    rgb_files = sorted(list(rgb_dir.glob("*.png")))[:5]

    # 从配置或poses获取期望尺寸
    expected_h, expected_w = 480, 640  # 默认
    poses_path = dataset_path / "poses.json"
    if poses_path.exists():
        with open(poses_path, "r") as f:
            poses = json.load(f)
        if poses and "camera_intrinsics" in poses[0]:
            intr = poses[0]["camera_intrinsics"]
            expected_h = intr.get("height", 480)
            expected_w = intr.get("width", 640)

    img_results = []
    for img_path in rgb_files:
        result = validate_image_quality(img_path, (expected_h, expected_w))
        img_results.append(result)
        status = "✓" if result["valid"] else "✗"
        print(f"      {img_path.name}: {status}")
        if not result["valid"]:
            for issue in result.get("issues", []):
                print(f"        ! {issue}")

    all_img_valid = all(r["valid"] for r in img_results)
    results["checks"]["image_quality"] = {"valid": all_img_valid, "samples": len(img_results)}
    if not all_img_valid:
        results["valid"] = False

    # 3. 深度图质量检查（抽检前5帧）
    print("\n[3/4] 深度图质量检查（抽检前5帧）...")
    depth_dir = dataset_path / "depth"
    depth_files = sorted(list(depth_dir.glob("*.npy")))[:5]

    depth_results = []
    for depth_path in depth_files:
        result = validate_depth_quality(depth_path)
        depth_results.append(result)
        status = "✓" if result["valid"] else "✗"
        nan_pct = result.get("nan_ratio", 0) * 100
        print(f"      {depth_path.name}: {status} (NaN:{nan_pct:.1f}%, "
              f"范围:{result.get('depth_range', (0,0))})")
        if not result["valid"]:
            for issue in result.get("issues", []):
                print(f"        ! {issue}")

    all_depth_valid = all(r["valid"] for r in depth_results)
    results["checks"]["depth_quality"] = {"valid": all_depth_valid, "samples": len(depth_results)}
    if not all_depth_valid:
        results["valid"] = False

    # 4. 位姿连续性检查
    print("\n[4/4] 位姿连续性检查...")
    if poses_path.exists():
        with open(poses_path, "r") as f:
            poses = json.load(f)
        pose_result = validate_pose_continuity(poses)
        results["checks"]["pose_continuity"] = pose_result
        print(f"      总帧数: {len(poses)}")
        print(f"      大跳跃: {pose_result.get('total_jumps', 0)} 处")
        print(f"      状态: {'通过 ✓' if pose_result['valid'] else '警告 ⚠'}")
        if not pose_result["valid"]:
            for issue in pose_result.get("issues", [])[:3]:
                print(f"        ! {issue}")

    # 总结
    print(f"\n{'='*60}")
    print(f"  验证结果: {'通过 ✓' if results['valid'] else '失败 ✗'}")
    print(f"{'='*60}\n")

    # 保存报告
    report_path = dataset_path / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[保存] 验证报告已保存至: {report_path}")

    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_dataset.py <dataset_path>")
        print("示例: python validate_dataset.py dataset/2026_03_12_10_30_00")
        sys.exit(1)

    dataset_path = Path(sys.argv[1])

    if not dataset_path.exists():
        print(f"错误: 路径不存在: {dataset_path}")
        sys.exit(1)

    results = validate_dataset(dataset_path)
    sys.exit(0 if results["valid"] else 1)


if __name__ == "__main__":
    main()
