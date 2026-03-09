"""
Phase 1 传感器验证脚本
验证 settings.json 中所有传感器是否正确加载并能产生数据

使用前提：UE5 + ASVSim 已运行，settings.json 已加载（重启仿真后生效）

运行方式：
    python 2-verify_sensors.py

预期输出（全绿）：
    [OK] 已连接 ASVSim
    [OK] Vessel1 存在
    [OK] 物理引擎已激活，当前速度: 0.012 m/s
    [OK] front_camera RGB: 1280x720, 2764800 bytes
    [OK] front_camera Depth: 1280x720, min=0.41m max=98.3m
    [OK] front_camera Seg: 1280x720
    [OK] down_camera RGB: 1280x720
    [OK] LiDAR top_lidar: 4096 点, 距离范围 0.5~99.8m
    [OK] 相机内参计算: fx=711.11 fy=711.11 cx=640.0 cy=360.0
"""

import cosysairsim as airsim
import numpy as np
import math
import time
import sys


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def get_intrinsics(width: int, height: int, fov_deg: float = 90.0) -> dict:
    """根据分辨率和视场角计算相机内参矩阵 K。"""
    fov_rad = math.radians(fov_deg)
    fx = width / (2 * math.tan(fov_rad / 2))
    fy = fx
    cx = width / 2.0
    cy = height / 2.0
    return {"fx": fx, "fy": fy, "cx": cx, "cy": cy,
            "K": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]}


# ─────────────────────────────────────────────
# 验证步骤
# ─────────────────────────────────────────────

def check_connection(client: airsim.VesselClient) -> bool:
    """Step 1: 验证连接。"""
    try:
        client.confirmConnection()
        ok("已连接 ASVSim")
        return True
    except Exception as e:
        fail(f"连接失败: {e}")
        return False


def check_vessel(client: airsim.VesselClient, vessel_name: str = "Vessel1") -> bool:
    """Step 2: 验证船只是否生成。"""
    vehicles = client.listVehicles()
    if vessel_name not in vehicles:
        fail(f"{vessel_name} 未找到，当前场景: {vehicles}")
        fail("请检查 settings.json 中 'AutoCreate': true 及 PawnPath 是否正确")
        return False
    ok(f"{vessel_name} 存在，场景载具列表: {vehicles}")
    return True


def check_physics(client: airsim.VesselClient, vessel_name: str = "Vessel1") -> bool:
    """Step 3: 验证物理引擎状态（读取船只运动学数据）。"""
    state = client.getVesselState(vessel_name)
    vel = state.kinematics_estimated.linear_velocity
    speed = math.sqrt(vel.x_val ** 2 + vel.y_val ** 2 + vel.z_val ** 2)
    pos = state.kinematics_estimated.position

    ok(f"船只状态正常：速度={speed:.4f} m/s, Z={pos.z_val:.3f}m")
    if speed < 1e-6:
        print("      (速度=0 是正常初始状态：Z=0 无外力时船只静止，物理引擎仍在运行)")
    return True


def check_camera(
    client: airsim.VesselClient,
    camera_name: str,
    camera_index: int,
    vessel_name: str = "Vessel1",
) -> bool:
    """Step 4: 验证相机能产生 RGB / Depth / Seg 三类图像。

    注意：simGetImages 使用整型 index（0, 1, 2…），不是 Sensors 块里的字符串名字。
    字符串名字仅供 LiDAR 等传感器使用；相机名在服务端注册为 "0"、"1"、"2" 等。
    SensorType:1 的顺序决定 index，排除 LiDAR 等非相机传感器。
    """
    all_ok = True
    try:
        responses = client.simGetImages([
            airsim.ImageRequest(camera_index, airsim.ImageType.Scene, False, False),
            airsim.ImageRequest(camera_index, airsim.ImageType.DepthPlanar, True, False),
            airsim.ImageRequest(camera_index, airsim.ImageType.Segmentation, False, False),
        ])

        # RGB
        r = responses[0]
        if r.width > 0 and r.height > 0 and len(r.image_data_uint8) > 0:
            ok(f"{camera_name} RGB: {r.width}x{r.height}, {len(r.image_data_uint8)} bytes")
        else:
            fail(f"{camera_name} RGB 数据为空（width={r.width} height={r.height}）")
            all_ok = False

        # Depth
        rd = responses[1]
        if rd.width > 0 and len(rd.image_data_float) > 0:
            depth_arr = np.array(rd.image_data_float, dtype=np.float32)
            valid = depth_arr[depth_arr < 1e5]  # 过滤无穷远
            if len(valid) > 0:
                ok(f"{camera_name} Depth: {rd.width}x{rd.height}, "
                   f"min={valid.min():.2f}m max={valid.max():.2f}m")
            else:
                warn(f"{camera_name} Depth 数据全为无穷远 — 场景可能没有障碍物")
        else:
            fail(f"{camera_name} Depth 数据为空")
            all_ok = False

        # Segmentation
        rs = responses[2]
        if rs.width > 0 and len(rs.image_data_uint8) > 0:
            seg_arr = np.frombuffer(rs.image_data_uint8, dtype=np.uint8)
            unique_colors = len(np.unique(seg_arr))
            ok(f"{camera_name} Seg: {rs.width}x{rs.height}, "
               f"独立像素值={unique_colors} (>1 说明有对象被分割)")
        else:
            fail(f"{camera_name} Seg 数据为空，检查 'InitialInstanceSegmentation': true")
            all_ok = False

    except Exception as e:
        fail(f"{camera_name} 图像请求异常: {e}")
        return False

    return all_ok


def check_lidar(
    client: airsim.VesselClient,
    lidar_name: str = "top_lidar",
    vessel_name: str = "Vessel1",
) -> bool:
    """Step 5: 验证 LiDAR 能产生点云数据。"""
    try:
        lidar_data = client.getLidarData(lidar_name, vessel_name)
        pts = lidar_data.point_cloud

        if len(pts) < 3:
            fail(f"LiDAR {lidar_name}: 点云为空（length={len(pts)}）")
            fail("检查 SensorType:6 和 Enabled:true；NumberOfLasers 是否 > 0")
            return False

        pts_arr = np.array(pts, dtype=np.float32).reshape(-1, 3)
        distances = np.linalg.norm(pts_arr, axis=1)
        ok(f"LiDAR {lidar_name}: {len(pts_arr)} 点, "
           f"距离范围 {distances.min():.1f}~{distances.max():.1f}m")
        return True

    except Exception as e:
        fail(f"LiDAR {lidar_name} 请求异常: {e}")
        return False


def check_intrinsics(
    camera_name: str = "front_camera",
    width: int = 1280,
    height: int = 720,
    fov_deg: float = 90.0,
) -> bool:
    """Step 6: 直接从 settings.json 已知参数计算内参矩阵 K。

    注意：simGetCameraInfo() 只适用于传统 AirSim 相机对象，
    不适用于通过 Sensors 块 (SensorType:1) 创建的传感器型相机，
    调用会导致 UE5 内部 nullptr 访问崩溃，故此处直接用已知值计算。
    """
    K = get_intrinsics(width, height, fov_deg)
    ok(f"相机内参（{camera_name}, W={width} H={height} FOV={fov_deg}deg）: "
       f"fx={K['fx']:.2f} fy={K['fy']:.2f} cx={K['cx']} cy={K['cy']}")
    print(f"      K = [[{K['fx']:.2f}, 0, {K['cx']}],")
    print(f"           [0, {K['fy']:.2f}, {K['cy']}],")
    print(f"           [0, 0, 1]]")
    return True


# ─────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────

def main() -> None:
    print("=" * 55)
    print("  Phase 1 — settings.json 传感器验证")
    print("=" * 55)

    client = airsim.VesselClient()

    # 连接
    if not check_connection(client):
        sys.exit(1)

    # 等待物理引擎稳定
    print("\n等待 1.5s 让物理引擎稳定...")
    time.sleep(1.5)

    results: list[bool] = []

    print("\n--- Step 1: 船只生成 ---")
    results.append(check_vessel(client))

    print("\n--- Step 2: 物理引擎 ---")
    results.append(check_physics(client))

    print("\n--- Step 3: front_camera (index=0) ---")
    results.append(check_camera(client, "front_camera", camera_index=0))

    print("\n--- Step 4: down_camera (index=1) ---")
    results.append(check_camera(client, "down_camera", camera_index=1))

    print("\n--- Step 5: LiDAR ---")
    results.append(check_lidar(client, "top_lidar"))

    print("\n--- Step 6: 相机内参（离线计算，无需 UE 响应）---")
    results.append(check_intrinsics("front_camera"))

    # 汇总
    print("\n" + "=" * 55)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"验证通过 {passed}/{total} — Phase 1 配置完成，可进入 Phase 2")
    else:
        print(f"验证结果 {passed}/{total} 通过 — 请根据 [FAIL] 信息排查问题")
    print("=" * 55)


if __name__ == "__main__":
    main()
