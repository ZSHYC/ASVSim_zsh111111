"""
事后生成分割真值 — 离线渲染Segmentation图像
================================================

功能：
    利用ASVSim的实例分割功能，在采集完成后离线生成分割真值。
    避免实时采集时的性能开销。

原理：
    通过ASVSim的API，可以在不移动船只的情况下，只渲染Segmentation图像。
    这比实时采集时同时渲染RGB/Depth/Seg快得多。

使用：
    python generate_segmentation.py <dataset_path> [--start N] [--end M]

示例：
    python generate_segmentation.py dataset/2026_03_12_10_30_00
    python generate_segmentation.py dataset/2026_03_12_10_30_00 --start 0 --end 50

注意：
    - 需要ASVSim正在运行，且船只位置未被重置
    - 如果船只已移动，需要根据poses.json重新定位（高级功能，暂不支持）
    - 或者可以在采集过程中同时记录船只位置，事后重置到该位置

作者: Claude Code
日期: 2026-03-12
"""

import cosysairsim as airsim
import numpy as np
import cv2
import json
import argparse
import time
from pathlib import Path
from typing import Optional


def generate_seg_for_dataset(dataset_path: Path, start_idx: int = 0,
                              end_idx: Optional[int] = None) -> None:
    """为数据集生成分割真值"""

    # 检查目录结构
    rgb_dir = dataset_path / "rgb"
    seg_dir = dataset_path / "segmentation"
    seg_dir.mkdir(exist_ok=True)

    # 获取RGB文件列表
    rgb_files = sorted(list(rgb_dir.glob("*.png")))
    total = len(rgb_files)

    if total == 0:
        print(f"错误: 未找到RGB图像: {rgb_dir}")
        return

    # 确定范围
    end_idx = end_idx or total
    start_idx = max(0, start_idx)
    end_idx = min(total, end_idx)

    print(f"\n{'='*60}")
    print(f"  生成分割真值")
    print(f"{'='*60}")
    print(f"\n  数据集: {dataset_path}")
    print(f"  总帧数: {total}")
    print(f"  处理范围: [{start_idx}, {end_idx})")
    print(f"\n  [重要] 请确保ASVSim正在运行，且船只处于合适位置")
    print(f"  [提示] 按Enter继续，或Ctrl+C取消")
    input()

    # 连接ASVSim
    print("\n[连接] 正在连接ASVSim...")
    client = airsim.VesselClient()
    client.confirmConnection()
    print("[连接] 成功")

    # 读取配置（如果有）
    config_path = dataset_path / "meta" / "collection_config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        cam_idx = config.get("front_cam_idx", 0)
    else:
        cam_idx = 0

    # 生成分割图
    generated = 0
    failed = 0
    start_time = time.time()

    for i in range(start_idx, end_idx):
        rgb_file = rgb_files[i]
        seg_file = seg_dir / rgb_file.name

        print(f"[{i+1:3d}/{end_idx}] {rgb_file.name}...", end=" ", flush=True)

        try:
            # 只请求Segmentation图像
            responses = client.simGetImages([
                airsim.ImageRequest(cam_idx, airsim.ImageType.Segmentation, False, False),
            ])

            # 解码
            r_seg = responses[0]
            seg_img = np.frombuffer(r_seg.image_data_uint8, dtype=np.uint8)
            seg_img = seg_img.reshape(r_seg.height, r_seg.width, 3)

            # 保存
            cv2.imwrite(str(seg_file), seg_img)

            generated += 1
            print(f"完成")

            # 小延迟避免RPC过载
            time.sleep(0.1)

        except Exception as e:
            failed += 1
            print(f"失败: {e}")
            continue

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"  完成")
    print(f"{'='*60}")
    print(f"  成功: {generated} 帧")
    print(f"  失败: {failed} 帧")
    print(f"  耗时: {elapsed:.1f}s ({elapsed/generated:.1f}s/帧)")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="生成分割真值")
    parser.add_argument("dataset_path", type=Path, help="数据集路径")
    parser.add_argument("--start", type=int, default=0, help="起始帧索引")
    parser.add_argument("--end", type=int, default=None, help="结束帧索引")
    args = parser.parse_args()

    if not args.dataset_path.exists():
        print(f"错误: 路径不存在: {args.dataset_path}")
        return 1

    generate_seg_for_dataset(args.dataset_path, args.start, args.end)
    return 0


if __name__ == "__main__":
    exit(main())
