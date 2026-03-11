"""
Phase 3 — 实用采集版（接受较慢速度，但稳定可用）
=====================================================

现实情况：
- CosysAirSim 3.0.1 + UE5 的 SceneCapture 本来就很慢（每帧 30-60s）
- simPause 有 bug 不能用
- 多线程会导致 IOLoop 错误

解决方案：
- 去掉多线程和超时（避免 IOLoop 错误）
- 大幅降低分辨率到 320×240（减少渲染时间）
- 只采集必要数据（RGB + Depth，暂时跳过 Seg 和 LiDAR）
- 接受较慢的采集速度，但确保稳定

使用：
    python 3-collect_practical.py
"""

import cosysairsim as airsim
import numpy as np
import cv2
import json
import math
import time
import sys
from pathlib import Path
from datetime import datetime


# ============================================================
#  配置（大幅降低分辨率以换取速度）
# ============================================================

VESSEL_NAME = "Vessel1"
FRONT_CAM_IDX = 0

NUM_FRAMES = 100
MOVE_SECONDS = 0.5        # 运动间隔
DATASET_ROOT = Path("dataset")

THRUST = 0.3
ANGLE = 0.6

# 【关键】使用 320×240 大幅降低渲染时间
CAM_W, CAM_H, CAM_FOV = 320, 240, 90.0


def compute_intrinsics(w, h, fov_deg):
    fov_rad = math.radians(fov_deg)
    fx = w / (2 * math.tan(fov_rad / 2))
    return {"fx": fx, "fy": fx, "cx": w / 2.0, "cy": h / 2.0}


def create_output_dirs(root):
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    base = root / ts
    dirs = {"base": base, "rgb": base / "rgb", "depth": base / "depth"}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def main():
    print("=" * 60)
    print("  Phase 3 — 实用采集版（稳定优先）")
    print(f"  分辨率：{CAM_W}×{CAM_H}（大幅降低以换取速度）")
    print("  注意：每帧采集可能需要 10-30 秒，请耐心等待")
    print("=" * 60)

    # 连接
    client = airsim.VesselClient()
    client.confirmConnection()
    client.enableApiControl(True, VESSEL_NAME)
    client.armDisarm(True, VESSEL_NAME)
    print(f"\n[连接] 已连接 ASVSim")

    time.sleep(2.0)

    intrinsics = compute_intrinsics(CAM_W, CAM_H, CAM_FOV)
    print(f"[内参] fx={intrinsics['fx']:.2f}")

    dirs = create_output_dirs(DATASET_ROOT)
    print(f"[目录] {dirs['base']}\n")

    # 启动船
    client.setVesselControls(VESSEL_NAME, airsim.VesselControls(THRUST, ANGLE))
    print(f"[轨迹] 启动：thrust={THRUST}, angle={ANGLE}")
    print("[提示] 按 Ctrl+C 停止\n")

    all_poses = []
    collected = 0

    try:
        for i in range(NUM_FRAMES):
            time.sleep(MOVE_SECONDS)

            # 【简化】只采集 RGB + Depth（最快组合）
            print(f"[{i+1:3d}/{NUM_FRAMES}] 采集中...", end=" ", flush=True)
            start = time.time()

            try:
                # 只请求两张图，减少渲染压力
                responses = client.simGetImages([
                    airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Scene, False, False),
                    airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.DepthPlanar, True, False),
                ])

                state = client.getVesselState(VESSEL_NAME)

                elapsed = time.time() - start
                print(f"完成 ({elapsed:.1f}s)")

                # 解码
                r_rgb = responses[0]
                img = np.frombuffer(r_rgb.image_data_uint8, dtype=np.uint8)
                img = img.reshape(r_rgb.height, r_rgb.width, 3)

                r_dep = responses[1]
                depth = np.array(r_dep.image_data_float, dtype=np.float32)
                depth = depth.reshape(r_dep.height, r_dep.width)
                depth[depth > 1e4] = np.inf

                # 保存
                cv2.imwrite(str(dirs["rgb"] / f"{i:04d}.png"), img)
                np.save(str(dirs["depth"] / f"{i:04d}.npy"), depth)

                # 记录位姿
                pos = state.kinematics_estimated.position
                ori = state.kinematics_estimated.orientation
                all_poses.append({
                    "frame_id": i,
                    "position": {"x": pos.x_val, "y": pos.y_val, "z": pos.z_val},
                    "orientation": {"w": ori.w_val, "x": ori.x_val, "y": ori.y_val, "z": ori.z_val},
                })
                collected += 1

            except Exception as e:
                print(f"失败: {e}")
                continue

    except KeyboardInterrupt:
        print(f"\n[中断] 已采集 {collected} 帧")

    finally:
        client.setVesselControls(VESSEL_NAME, airsim.VesselControls(0.0, 0.5))
        client.armDisarm(False, VESSEL_NAME)
        client.enableApiControl(False, VESSEL_NAME)

        if all_poses:
            with open(dirs["base"] / "poses.json", "w") as f:
                json.dump(all_poses, f, indent=2)

    print(f"\n[完成] 采集 {collected} 帧，保存至 {dirs['base']}")


if __name__ == "__main__":
    main()
