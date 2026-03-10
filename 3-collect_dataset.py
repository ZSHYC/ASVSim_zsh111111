"""
Phase 3 — 多模态数据采集 Pipeline
====================================

功能：让船自动跑圆弧轨迹，每隔固定距离冻结仿真，同步采集
      RGB / Depth / Segmentation / LiDAR / Pose，保存成标准目录结构。

前提：
  - UE5 + ASVSim 已运行，Phase 1 的 settings.json 已加载
  - 从 ASVSim_zsh 目录执行：python 3-collect_dataset.py

采集后目录结构：
  dataset/YYYY_MM_DD_HH_MM_SS/
  ├── rgb/              0000.png, 0001.png ...   (uint8, H×W×3, BGR)
  ├── depth/            0000.npy, 0001.npy ...   (float32, H×W, 单位: 米)
  ├── segmentation/     0000.png, 0001.png ...   (uint8, H×W×3, BGR)
  ├── lidar/            0000.json ...            (N×3 列表, SensorLocalFrame)
  └── poses.json        每帧的位姿 + 相机内参

注意：本脚本只存原始数据，坐标系变换（ASVSim→COLMAP）由后续
      4-convert_poses.py 完成。先跑通，再对齐格式。
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
#  ① 参数配置 — 修改这里来调整采集行为
# ============================================================

VESSEL_NAME     = "Vessel1"
FRONT_CAM_IDX   = 0          # front_camera 在 simGetImages 里的整数索引
# DOWN_CAM_IDX  = 1          # down_camera 已暂时移除（采集但未保存，多占一个 render pass）
LIDAR_NAME      = "top_lidar"

# --- 采集参数 ---
NUM_FRAMES      = 100        # 总采集帧数（100 帧约够一个完整圆圈）
MOVE_SECONDS    = 0.3        # 每帧之间船运动的秒数（原 1.0，缩短提速）
DATASET_ROOT    = Path("dataset")

# --- 轨迹参数 ---
# 官方文档（vessel_api）确认：
#   angle 范围 0.0~1.0，0.5 = 直行，< 0.5 = 左转，> 0.5 = 右转
# 示例：VesselControls(thrust=0.7, angle=0.6) = 70% 推力 + 轻微右转
# 0.3 推力 + 0.6 角度 → 缓慢右圆弧，约 50~100 帧走完一圈
THRUST          = 0.3
ANGLE           = 0.6        # 0.5=直行, 0.6=右转, 0.4=左转

# --- 相机内参（由 settings.json 参数离线计算，无需调用 API）---
CAM_W, CAM_H, CAM_FOV = 1280, 720, 90.0


# ============================================================
#  ② 工具函数
# ============================================================

def compute_intrinsics(w: int, h: int, fov_deg: float) -> dict:
    """
    从 settings.json 的 Width / Height / FOV_Degrees 计算相机内参矩阵 K。

    公式：fx = W / (2 * tan(FOV/2))
    原因：simGetCameraInfo() 对 SensorType:1 的传感器相机无效（会使 UE5 崩溃），
    只能用已知设置值离线推算。
    """
    fov_rad = math.radians(fov_deg)
    fx = w / (2 * math.tan(fov_rad / 2))
    return {
        "fx": fx, "fy": fx,
        "cx": w / 2.0, "cy": h / 2.0,
        "width": w, "height": h, "fov_deg": fov_deg,
    }


def create_output_dirs(root: Path) -> dict[str, Path]:
    """
    创建带时间戳的输出目录树，返回各子目录路径。
    时间戳格式：YYYY_MM_DD_HH_MM_SS
    """
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


# ============================================================
#  ③ 单帧采集 — 核心函数
# ============================================================

def collect_one_frame(
    client: airsim.VesselClient,
    intrinsics: dict,
) -> dict:
    """
    冻结仿真，采集所有传感器数据，恢复仿真，返回结构化字典。

    关键设计：
    1. simPause(True)  → 物理引擎暂停，所有传感器此后返回同一时刻的状态
    2. 先采图像，再采 LiDAR，再采 Pose → 顺序无所谓，因为物理已冻结
    3. simPause(False) → 恢复，船继续前进

    返回字典包含：
      rgb       : np.ndarray (H, W, 3) uint8，BGR 格式（cv2 默认）
      depth     : np.ndarray (H, W)    float32，单位米，无效点为 inf
      seg       : np.ndarray (H, W, 3) uint8，BGR 格式
      lidar_pts : np.ndarray (N, 3)    float32，SensorLocalFrame 坐标
      pose      : dict，包含 position(x,y,z) 和 orientation(w,x,y,z)
    """
    # ── 冻结仿真 ──────────────────────────────────────────────
    # 注意：simPause 在某些 CosysAirSim 版本 + 控制初始化组合下
    # 可能导致后续 API 请求挂起，暂时禁用，先跑通采集流程。
    # 后续确认无问题后再重新启用（取消注释下面这行）。
    # client.simPause(True)

    try:
        # ── 2. 一次请求拿全部 3 张图（front: RGB / Depth / Seg）────
        # 注意：down_camera 已从请求中移除——官方文档确认 UE5 Lumen
        # 每个 SceneCapture 都要渲染一遍，down_camera 虽然采集但从未保存，
        # 白白多一次渲染 pass（1280×720 + Lumen ≈ 10~60s/pass）。
        # 如需 down_camera 数据，在 save_frame 里补充保存逻辑后再加回来。
        # 返回顺序与请求顺序严格对应：[0]=front RGB, [1]=front Depth, [2]=front Seg
        all_responses = client.simGetImages([
            airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Scene,
                                False, False),         # [0] front RGB
            airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.DepthPlanar,
                                True,  False),         # [1] front Depth float32
            airsim.ImageRequest(FRONT_CAM_IDX, airsim.ImageType.Segmentation,
                                False, False),         # [2] front Seg
        ])

        # ── 4. 船只状态（位姿）────────────────────────────────
        # getVesselState() 不传参数（与 simGetImages 一样，传 vessel_name 可能卡）
        # 实际测试中 getVesselState(VESSEL_NAME) 是安全的，保留 vessel_name 调用
        state = client.getVesselState(VESSEL_NAME)

        # ── 5. LiDAR（需要传感器名 + vessel_name，与相机规则不同）──
        lidar_data = client.getLidarData(LIDAR_NAME, VESSEL_NAME)

    finally:
        # 无论前面是否异常，都要恢复仿真（与上方 simPause 注释保持一致）
        # client.simPause(False)
        pass

    # ── 6. 解码 front_camera RGB ─────────────────────────────
    # CosysAirSim 3.0.1 实测：原始图像已经是正向的，不需要 flipud。
    # （标准 AirSim 文档说需要 flipud，但本版本已修正，加了反而倒置）
    r_rgb = all_responses[0]
    img_rgb = np.frombuffer(r_rgb.image_data_uint8, dtype=np.uint8)
    img_rgb = img_rgb.reshape(r_rgb.height, r_rgb.width, 3)
    img_rgb_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # ── 7. 解码 Depth（float32，单位米）────────────────────────
    r_depth = all_responses[1]
    depth = np.array(r_depth.image_data_float, dtype=np.float32)
    depth = depth.reshape(r_depth.height, r_depth.width)
    # 无效点（天空/无返回）的值很大（如 65504），替换为 inf 方便后续过滤
    depth[depth > 1e4] = np.inf

    # ── 8. 解码 Segmentation ─────────────────────────────────
    r_seg = all_responses[2]
    img_seg = np.frombuffer(r_seg.image_data_uint8, dtype=np.uint8)
    img_seg = img_seg.reshape(r_seg.height, r_seg.width, 3)
    img_seg_bgr = cv2.cvtColor(img_seg, cv2.COLOR_RGB2BGR)

    # ── 9. 解码 LiDAR（点云坐标，SensorLocalFrame）──────────
    pts = np.array(lidar_data.point_cloud, dtype=np.float32)
    if len(pts) >= 3:
        pts = pts.reshape(-1, 3)     # (N, 3)，每行是一个点 [x, y, z]
    else:
        pts = np.zeros((0, 3), dtype=np.float32)

    # ── 10. 提取位姿 ─────────────────────────────────────────
    # position 单位：米（UE5 世界坐标，X=前, Y=右, Z=下）
    # orientation：四元数 (w, x, y, z)
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


# ============================================================
#  ④ 保存单帧数据
# ============================================================

def save_frame(dirs: dict[str, Path], idx: int, frame: dict) -> None:
    """
    将一帧数据写入磁盘。
    文件名：四位零填充整数（0000, 0001, ...）

    格式选择理由：
      - RGB/Seg → PNG（无损，支持 uint8）
      - Depth   → NPY（保留 float32 精度，PNG 会丢失小数）
      - LiDAR   → JSON（可读，便于调试；大数据集可改 NPY）
    """
    name = f"{idx:04d}"

    # RGB：直接 imwrite，已经是 BGR
    cv2.imwrite(str(dirs["rgb"] / f"{name}.png"), frame["rgb"])

    # Depth：用 numpy 保存 float32 数组
    np.save(str(dirs["depth"] / f"{name}.npy"), frame["depth"])

    # Segmentation
    cv2.imwrite(str(dirs["seg"] / f"{name}.png"), frame["seg"])

    # LiDAR：转为列表再 JSON 序列化
    lidar_list = frame["lidar"].tolist()
    with open(dirs["lidar"] / f"{name}.json", "w") as f:
        json.dump(lidar_list, f)


# ============================================================
#  ⑤ 主循环
# ============================================================

def main() -> None:
    print("=" * 60)
    print("  Phase 3 — 多模态数据采集")
    print(f"  目标帧数：{NUM_FRAMES}，运动间隔：{MOVE_SECONDS}s/帧")
    print("=" * 60)

    # ── 连接 ──────────────────────────────────────────────────
    client = airsim.VesselClient()
    client.confirmConnection()
    client.enableApiControl(True, VESSEL_NAME)
    client.armDisarm(True, VESSEL_NAME)        # hello_ship.py 验证必须有这一行
    print(f"[连接] 已连接 ASVSim，控制 {VESSEL_NAME}")

    # ── 等待物理引擎稳定 ──────────────────────────────────────
    print("[等待] 等待 2s，让物理引擎稳定...")
    time.sleep(2.0)

    # ── 预计算相机内参（整个采集过程不变）─────────────────────
    intrinsics = compute_intrinsics(CAM_W, CAM_H, CAM_FOV)
    print(f"[内参] fx={intrinsics['fx']:.2f}, cx={intrinsics['cx']}, cy={intrinsics['cy']}")

    # ── 创建输出目录 ──────────────────────────────────────────
    dirs = create_output_dirs(DATASET_ROOT)

    # ── 设置轨迹（给船一个持续的控制指令）────────────────────
    # 船会持续以 THRUST 推力、ANGLE 偏转角运动，直到我们改变控制或停止
    client.setVesselControls(
        VESSEL_NAME,
        airsim.VesselControls(THRUST, ANGLE)
    )
    print(f"[轨迹] 启动：thrust={THRUST}, angle={ANGLE}（0.5=直行, >0.5=右转, <0.5=左转）")
    print(f"[提示] 按 Ctrl+C 可提前停止，已采集的帧不会丢失")

    # ── 采集循环 ──────────────────────────────────────────────
    all_poses: list[dict] = []
    collected = 0

    try:
        for i in range(NUM_FRAMES):
            # 1. 让船运动一段时间，再暂停采集
            #    第 0 帧也先等一下，让船有初始速度
            time.sleep(MOVE_SECONDS)

            # 2. 采集当前帧
            try:
                frame = collect_one_frame(client, intrinsics)
            except Exception as e:
                print(f"[警告] 第 {i} 帧采集失败，跳过: {e}")
                continue

            # 3. 保存到磁盘
            save_frame(dirs, i, frame)

            # 4. 收集位姿（最后统一写 poses.json）
            all_poses.append({"frame_id": i, **frame["pose"]})
            collected += 1

            # 5. 进度打印
            pos = frame["pose"]["position"]
            lidar_n = len(frame["lidar"])
            depth_valid = np.sum(np.isfinite(frame["depth"]))
            print(
                f"[{i+1:3d}/{NUM_FRAMES}] "
                f"pos=({pos['x']:6.1f},{pos['y']:6.1f},{pos['z']:5.2f}) "
                f"lidar={lidar_n:5d}pts "
                f"depth_valid={depth_valid:7d}px"
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
        poses_path = dirs["base"] / "poses.json"
        with open(poses_path, "w") as f:
            json.dump(all_poses, f, indent=2)
        print(f"[保存] poses.json 已写入（{len(all_poses)} 帧）")

    # ── 完成报告 ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  采集完成：{collected} 帧")
    print(f"  输出目录：{dirs['base']}")
    print(f"  验证命令：python 3-verify_dataset.py {dirs['base']}")
    print("=" * 60)

    # ── 快速自检 ──────────────────────────────────────────────
    if collected > 0:
        _quick_check(dirs, collected)


def _quick_check(dirs: dict[str, Path], n: int) -> None:
    """采集完成后做一次快速自检，打印数据统计。"""
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
    first_rgb = list(dirs["rgb"].glob("*.png"))
    if first_rgb:
        img = cv2.imread(str(sorted(first_rgb)[0]))
        print(f"  首帧 RGB 形状: {img.shape}  ← 期望 (720, 1280, 3)")

    first_dep = list(dirs["depth"].glob("*.npy"))
    if first_dep:
        d = np.load(str(sorted(first_dep)[0]))
        valid = d[np.isfinite(d)]
        if len(valid) > 0:
            print(f"  首帧 Depth: shape={d.shape}, "
                  f"min={valid.min():.2f}m max={valid.max():.2f}m "
                  f"有效像素={len(valid)}/{d.size}")
        else:
            print("  [警告] 首帧 Depth 全部无效（场景可能没有可见物体）")

    print("[自检] 完成。如有异常请检查 [警告] 信息。")


# ============================================================
if __name__ == "__main__":
    main()
