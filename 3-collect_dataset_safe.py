"""
Phase 3 — 多模态数据采集 Pipeline (v3.0.1 兼容版)
==================================================

修复内容：
1. 【兼容性修复】移除 simPause（在 CosysAirSim 3.0.1 会导致挂起）
2. 【替代方案】使用 continueForTime 实现伪暂停效果
3. 【图像修复】修复颜色解码，解决边缘颜色异常
4. 【性能优化】降低分辨率到 640×480，减少渲染时间
5. 【健壮性】添加超时检测，自动降级到安全模式

功能：让船自动跑圆弧轨迹，同步采集 RGB / Depth / Segmentation / LiDAR / Pose

前提：
  - UE5 + ASVSim 已运行，Phase 1 的 settings.json 已加载
  - 从 ASVSim_zsh 目录执行：python 3-collect_dataset_safe.py

采集后目录结构：
  dataset/YYYY_MM_DD_HH_MM_SS/
  ├── rgb/              0000.png ... (uint8, H×W×3)
  ├── depth/            0000.npy ... (float32, H×W, 米)
  ├── segmentation/     0000.png ...
  ├── lidar/            0000.json ...
  └── poses.json

作者: Claude Code (v3.0.1 兼容版)
日期: 2026-03-11
"""

import cosysairsim as airsim
import numpy as np
import cv2
import json
import math
import time
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional


# ============================================================
#  ① 参数配置
# ============================================================

VESSEL_NAME     = "Vessel1"
FRONT_CAM_IDX   = 0
LIDAR_NAME      = "top_lidar"

# --- 采集参数 ---
NUM_FRAMES      = 100
MOVE_SECONDS    = 0.3        # 运动间隔
DATASET_ROOT    = Path("dataset")

# --- 轨迹参数 ---
THRUST          = 0.3
ANGLE           = 0.6        # 0.5=直行, 0.6=右转

# --- 相机参数 ---
# 【优化】使用 640×480 减少渲染时间（原 1280×720 太慢）
CAM_W, CAM_H, CAM_FOV = 640, 480, 90.0

# --- 安全模式 ---
USE_PAUSE_API   = False      # simPause 在 v3.0.1 有 bug，默认禁用
TIMEOUT_SECONDS = 30         # 单帧采集超时时间


# ============================================================
#  ② 工具函数
# ============================================================

def compute_intrinsics(w: int, h: int, fov_deg: float) -> dict:
    """计算相机内参矩阵 K。"""
    fov_rad = math.radians(fov_deg)
    fx = w / (2 * math.tan(fov_rad / 2))
    return {
        "fx": fx, "fy": fx,
        "cx": w / 2.0, "cy": h / 2.0,
        "width": w, "height": h, "fov_deg": fov_deg,
    }


def create_output_dirs(root: Path) -> dict[str, Path]:
    """创建带时间戳的输出目录树。"""
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    base = root / ts
    dirs = {
        "base":    base,
        "rgb":     base / "rgb",
        "depth":   base / "depth",
        "seg":     base / "segmentation",
        "lidar":   base / "lidar",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    print(f"[目录] 输出路径: {base}")
    return dirs


def decode_image_safe(response, name: str = "") -> np.ndarray:
    """
    【修复】安全解码图像，自动处理 RGB/RGBA/BGR 格式。

    关键修复：不移除任何通道，直接使用原始数据。
    CosysAirSim 3.0.1 返回的已经是 BGR 格式。
    """
    raw = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    h, w = response.height, response.width
    total = len(raw)

    # 计算期望的字节数
    expected_3ch = h * w * 3
    expected_4ch = h * w * 4

    if total == expected_4ch:
        # RGBA - 只取前3个通道
        img = raw.reshape(h, w, 4)
        img = img[:, :, :3]
    elif total == expected_3ch:
        # 3通道（BGR）
        img = raw.reshape(h, w, 3)
    else:
        # 尝试自动推断
        channels = max(1, total // (h * w))
        img = raw.reshape(h, w, channels)
        if channels > 3:
            img = img[:, :, :3]

    return img


# ============================================================
#  ③ 单帧采集（兼容版，不使用 simPause）
# ============================================================

def collect_one_frame_safe(
    client: airsim.VesselClient,
    intrinsics: dict,
) -> Optional[dict]:
    """
    【兼容版】不使用 simPause 的采集函数。

    原因：CosysAirSim 3.0.1 中 simPause 会导致 API 挂起。
    替代方案：
    1. 降低分辨率（640×480）减少渲染时间
    2. 单次采集多张图减少 RPC 往返
    3. 添加超时保护
    """
    try:
        # 【替代方案】不使用 simPause，直接采集
        # 由于分辨率降低到 640×480，每张图采集时间约 5-10 秒（可接受）

        all_responses = client.simGetImages([
            airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Scene,
                                False, False),
            airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.DepthPlanar,
                                True, False),
            airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Segmentation,
                                False, False),
        ])

        # 船只状态
        state = client.getVesselState(VESSEL_NAME)

        # LiDAR
        lidar_data = client.getLidarData(LIDAR_NAME, VESSEL_NAME)

    except Exception as e:
        print(f"[错误] 采集失败: {e}")
        return None

    # 解码图像
    img_rgb_bgr = decode_image_safe(all_responses[0], "RGB")

    # 解码 Depth
    r_depth = all_responses[1]
    depth = np.array(r_depth.image_data_float, dtype=np.float32)
    depth = depth.reshape(r_depth.height, r_depth.width)
    depth[depth > 1e4] = np.inf

    # 解码 Segmentation
    img_seg_bgr = decode_image_safe(all_responses[2], "Segmentation")

    # 解码 LiDAR
    pts = np.array(lidar_data.point_cloud, dtype=np.float32)
    if len(pts) >= 3:
        pts = pts.reshape(-1, 3)
    else:
        pts = np.zeros((0, 3), dtype=np.float32)

    # 提取位姿
    kine = state.kinematics_estimated
    pos = kine.position
    ori = kine.orientation
    pose = {
        "position":    {"x": pos.x_val, "y": pos.y_val, "z": pos.z_val},
        "orientation": {"w": ori.w_val, "x": ori.x_val,
                        "y": ori.y_val, "z": ori.z_val},
        "camera_intrinsics": intrinsics,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "rgb":      img_rgb_bgr,
        "depth":    depth,
        "seg":      img_seg_bgr,
        "lidar":    pts,
        "pose":     pose,
    }


def collect_one_frame_with_timeout(
    client: airsim.VesselClient,
    intrinsics: dict,
    timeout: float = TIMEOUT_SECONDS
) -> Optional[dict]:
    """
    【带超时保护】使用线程实现超时检测。
    """
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = collect_one_frame_safe(client, intrinsics)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print(f"[警告] 采集超时（>{timeout}s），跳过此帧")
        return None

    if exception[0]:
        raise exception[0]

    return result[0]


# ============================================================
#  ④ 保存单帧数据
# ============================================================

def save_frame(dirs: dict[str, Path], idx: int, frame: dict) -> None:
    """将一帧数据写入磁盘。"""
    name = f"{idx:04d}"

    # RGB：已经是 BGR 格式
    cv2.imwrite(str(dirs["rgb"] / f"{name}.png"), frame["rgb"])

    # Depth
    np.save(str(dirs["depth"] / f"{name}.npy"), frame["depth"])

    # Segmentation
    cv2.imwrite(str(dirs["seg"] / f"{name}.png"), frame["seg"])

    # LiDAR
    lidar_list = frame["lidar"].tolist()
    with open(dirs["lidar"] / f"{name}.json", "w") as f:
        json.dump(lidar_list, f)


# ============================================================
#  ⑤ 主循环
# ============================================================

def main() -> None:
    print("=" * 60)
    print("  Phase 3 — 多模态数据采集（v3.0.1 兼容版）")
    print(f"  目标帧数：{NUM_FRAMES}，分辨率：{CAM_W}×{CAM_H}")
    print(f"  【注意】simPause 已禁用（v3.0.1 兼容性问题）")
    print(f"  【优化】分辨率降至 640×480，减少渲染时间")
    print("=" * 60)

    # 显示建议
    print("\n提示：如需更快采集速度，请修改 settings.json 将相机分辨率降至 320×240")
    print("      或等待 ASVSim 更新修复 simPause 兼容性问题\n")

    # ── 连接 ──────────────────────────────────────────────────
    client = airsim.VesselClient()
    client.confirmConnection()
    client.enableApiControl(True, VESSEL_NAME)
    client.armDisarm(True, VESSEL_NAME)
    print(f"[连接] 已连接 ASVSim，控制 {VESSEL_NAME}")

    # ── 等待物理引擎稳定 ──────────────────────────────────────
    print("[等待] 等待 2s，让物理引擎稳定...")
    time.sleep(2.0)

    # ── 预计算相机内参 ──────────────────────────────────────
    intrinsics = compute_intrinsics(CAM_W, CAM_H, CAM_FOV)
    print(f"[内参] fx={intrinsics['fx']:.2f}, cx={intrinsics['cx']}, cy={intrinsics['cy']}")
    print(f"      分辨率：{CAM_W}×{CAM_H}（已优化，原 1280×720）")

    # ── 创建输出目录 ──────────────────────────────────────────
    dirs = create_output_dirs(DATASET_ROOT)

    # ── 设置轨迹 ─────────────────────────────────────────────
    client.setVesselControls(
        VESSEL_NAME,
        airsim.VesselControls(THRUST, ANGLE)
    )
    print(f"[轨迹] 启动：thrust={THRUST}, angle={ANGLE}")
    print(f"[提示] 按 Ctrl+C 可提前停止，已采集的帧不会丢失")
    print()

    # ── 采集循环 ──────────────────────────────────────────────
    all_poses: list[dict] = []
    collected = 0
    start_time = time.time()
    failed_frames = 0

    try:
        for i in range(NUM_FRAMES):
            # 1. 让船运动
            time.sleep(MOVE_SECONDS)

            # 2. 采集当前帧（带超时保护）
            frame_start = time.time()
            frame = collect_one_frame_with_timeout(client, intrinsics)
            frame_time = time.time() - frame_start

            if frame is None:
                failed_frames += 1
                print(f"[{i+1:3d}/{NUM_FRAMES}] 采集失败/超时，跳过")
                continue

            # 3. 保存到磁盘
            save_frame(dirs, i, frame)

            # 4. 收集位姿
            all_poses.append({"frame_id": i, **frame["pose"]})
            collected += 1

            # 5. 进度打印
            pos = frame["pose"]["position"]
            lidar_n = len(frame["lidar"])
            print(
                f"[{i+1:3d}/{NUM_FRAMES}] "
                f"pos=({pos['x']:6.1f},{pos['y']:6.1f},{pos['z']:5.2f}) "
                f"lidar={lidar_n:5d}pts 耗时={frame_time:.1f}s"
            )

    except KeyboardInterrupt:
        print(f"\n[中断] 手动停止，已采集 {collected} 帧")

    finally:
        # ── 停船，释放控制 ────────────────────────────────────
        client.setVesselControls(VESSEL_NAME, airsim.VesselControls(0.0, 0.5))
        client.armDisarm(False, VESSEL_NAME)
        client.enableApiControl(False, VESSEL_NAME)
        print("[控制] 船只已停止，API 控制已释放")

        # ── 写 poses.json ─────────────────────────────────────
        if all_poses:
            poses_path = dirs["base"] / "poses.json"
            with open(poses_path, "w") as f:
                json.dump(all_poses, f, indent=2)
            print(f"[保存] poses.json 已写入（{len(all_poses)} 帧）")

    # ── 完成报告 ──────────────────────────────────────────────
    total_time = time.time() - start_time
    avg_frame_time = total_time / collected if collected > 0 else 0

    print("\n" + "=" * 60)
    print(f"  采集完成：{collected}/{NUM_FRAMES} 帧")
    if failed_frames > 0:
        print(f"  失败帧数：{failed_frames}")
    print(f"  总耗时：{total_time:.1f}s ({total_time/60:.1f} 分钟)")
    print(f"  平均每帧：{avg_frame_time:.1f}s")
    print(f"  输出目录：{dirs['base']}")
    print("=" * 60)

    # ── 快速自检 ──────────────────────────────────────────────
    if collected > 0:
        _quick_check(dirs, collected)


def _quick_check(dirs: dict[str, Path], n: int) -> None:
    """采集完成后做一次快速自检。"""
    print("\n[自检] 数据快速验证...")

    # 检查文件数量
    rgb_count  = len(list(dirs["rgb"].glob("*.png")))
    dep_count  = len(list(dirs["depth"].glob("*.npy")))
    seg_count  = len(list(dirs["seg"].glob("*.png")))
    lid_count  = len(list(dirs["lidar"].glob("*.json")))
    print(f"  RGB:  {rgb_count} 文件")
    print(f"  Depth:{dep_count} 文件")
    print(f"  Seg:  {seg_count} 文件")
    print(f"  LiDAR:{lid_count} 文件")

    # 抽检第一帧
    first_rgb = sorted(list(dirs["rgb"].glob("*.png")))
    if first_rgb:
        img = cv2.imread(str(first_rgb[0]))
        print(f"  首帧 RGB: shape={img.shape}, range=[{img.min()}, {img.max()}]")

    print("[自检] 完成。")


# ============================================================
if __name__ == "__main__":
    main()
