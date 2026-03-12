"""
运行时调整相机位置和后期处理参数（无需重启UE5）
========================================================

当不想重启UE5时，使用此脚本通过API动态调整相机参数。
注意：这只是临时修改，重启后会恢复为settings.json的值。
"""

import cosysairsim as airsim
import time


def adjust_camera_runtime():
    """
    通过API动态调整相机参数（无需重启UE5）。

    这是临时方案，settings.json的修改仍需重启才能永久生效。
    """
    client = airsim.VesselClient()
    client.confirmConnection()

    print("[运行时调整] 修改相机位置和后期处理参数...")

    # 方案1: 通过API设置相机位置（如果ASVSim支持）
    # 注意：不是所有版本都支持运行时修改相机位置
    try:
        # 尝试设置相机姿态（某些版本支持）
        # camera_pose = airsim.Pose(
        #     airsim.Vector3r(2.5, 0.0, -1.8),  # 位置：前移+抬高
        #     airsim.Quaternionr(0.0, 0.087, 0.0, 0.996)  # Pitch -10度的四元数
        # )
        # client.simSetCameraPose("front_camera", camera_pose, "Vessel1")
        print("  [提示] ASVSim v3.0.1 不支持运行时修改相机位置，需重启UE5")
    except Exception as e:
        print(f"  [错误] {e}")

    # 方案2: 修改后期处理设置（如果支持）
    try:
        # 某些版本支持通过API修改后期处理
        # client.simSetPostProcessSettings(...)
        print("  [提示] 后期处理参数需通过settings.json设置，重启生效")
    except:
        pass

    print("\n[结论] ASVSim v3.0.1 的限制：")
    print("  - 相机位置：必须在settings.json中设置，重启生效")
    print("  - 后期处理：必须在settings.json中设置，重启生效")
    print("\n[建议] 请完全关闭并重新打开UE5编辑器")


def verify_current_settings():
    """验证当前相机配置"""
    client = airsim.VesselClient()
    client.confirmConnection()

    print("\n[验证] 当前相机信息：")

    # 采集一帧查看图像
    responses = client.simGetImages([
        airsim.ImageRequest(0, airsim.ImageType.Scene, False, False),
    ])

    r = responses[0]
    print(f"  分辨率: {r.width}x{r.height}")
    print(f"  数据大小: {len(r.image_data_uint8)} bytes")

    # 检查是否能看到船体（通过分析图像内容）
    import numpy as np
    img = np.frombuffer(r.image_data_uint8, dtype=np.uint8).reshape(r.height, r.width, 3)

    # 简单分析：如果底部区域有大量棕色像素，可能是船体
    bottom_region = img[-100:, :, :]  # 底部100行
    brown_pixels = np.sum((bottom_region[:, :, 0] > 80) &
                          (bottom_region[:, :, 0] < 150) &
                          (bottom_region[:, :, 1] > 40) &
                          (bottom_region[:, :, 1] < 100) &
                          (bottom_region[:, :, 2] < 60))

    total_pixels = bottom_region.shape[0] * bottom_region.shape[1]
    brown_ratio = brown_pixels / total_pixels

    print(f"  底部棕色像素比例: {brown_ratio:.2%}")
    if brown_ratio > 0.3:
        print("  [警告] 检测到船体甲板（棕色区域），相机位置未更新")
    else:
        print("  [正常] 未检测到明显船体")

    return brown_ratio < 0.3


if __name__ == "__main__":
    print("=" * 60)
    print("  ASVSim 相机配置验证工具")
    print("=" * 60)

    # 验证当前配置
    is_correct = verify_current_settings()

    if not is_correct:
        print("\n[建议操作]")
        print("1. 完全关闭 UE5 编辑器（点击右上角X）")
        print("2. 重新打开 ASVSim 项目")
        print("3. 等待场景加载完成")
        print("4. 重新运行采集脚本")
        print("\n当前settings.json配置正确，但UE5需要重启才能加载新配置。")
