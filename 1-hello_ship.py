# 引入必要的库，假设你已经把 ASVSim 的 airsim 库放在了旁边
import cosysairsim as airsim 
import time
import math

# 1. 连接到仿真器
client = airsim.VesselClient()
client.confirmConnection()

print("已连接到 ASVSim！")

# 2. 获取场景中可用的船只列表
vehicles = client.listVehicles()
print(f"场景中可用的船只: {vehicles}")

if not vehicles:
    print("错误：场景中没有可用的船只！请在 UE4 场景中添加船只。")
    exit(1)

# 尝试使用 "MilliAmpere"，如果没有就用第一个可用的船只
vessel_name = "MilliAmpere" if "MilliAmpere" in vehicles else vehicles[0]
print(f"使用船只: {vessel_name}")

# 开启 API 控制权限
client.enableApiControl(True, vessel_name)
client.armDisarm(True, vessel_name)

print(f"已获取 {vessel_name} 的控制权，准备启航...")

# 3. 控制船只运动
# 论文 [cite: 147, 446] 提到：
# thrust (推力): 0 到 1
# angle (角度): 0 到 1 (0.5 是中间/直行，0 是最左，1 是最右)

try:
    # 让船向前直行
    print("引擎全开！(Thrust=1.0, Angle=0.0)")
    # VesselControls(thrust, angle): thrust 推力, angle 舵角 (弧度)
    client.setVesselControls(vessel_name, airsim.VesselControls(1.0, 0.0))
    
    # 持续运行 5 秒
    time.sleep(5)
    
    # 尝试左转
    print("左转！(Thrust=0.8, Angle=-0.5)")
    client.setVesselControls(vessel_name, airsim.VesselControls(0.8, -0.5))
    time.sleep(5)

    # 尝试右转
    print("右转！(Thrust=0.8, Angle=0.5)")
    client.setVesselControls(vessel_name, airsim.VesselControls(0.8, 0.5))
    time.sleep(5)

except KeyboardInterrupt:
    print("手动停止")

finally:
    # 4. 停船并释放控制
    client.setVesselControls(vessel_name, airsim.VesselControls(0.0, 0.0))
    client.armDisarm(False, vessel_name)
    client.enableApiControl(False, vessel_name)
    print("测试结束，船只已停止。")