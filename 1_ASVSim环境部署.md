# ASVSim 仿真环境部署记录：从 Blocks 到 LakeEnv (Part 1)

**项目名称**：基于 3DGS 的无人船冰水环境重建与路径规划
**环境**：Windows 10/11, Unreal Engine 5.4, Visual Studio 2022, ASVSim
**显卡**：RTX 5070 Ti（12g显存）

## 1. 简介

本项目基于 ASVSim 框架。默认的编译环境是 `Blocks`，为了进行船舶仿真，需要切换到高保真的水面环境（LakeEnv）。由于 ASVSim 将环境打包为独立工程，本指南记录了从解压环境包到成功编译运行的全过程。

## 2. 准备工作

* **基础环境**：已完成 ASVSim 核心插件的编译，并能成功运行基础 Blocks 环境。

**资源位置**：确认环境压缩包位于 `D:\ASVSim\Unreal\Environments` 。

## 3. 详细部署步骤

### 第一步：解压环境包

1. 进入环境存放目录：`D:\ASVSim\Unreal\Environments`。
2. 找到 `LakeEnv.zip` 。
3. 将其解压到当前文件夹。

**注意**：解压后的目录结构应为 `D:\ASVSim\Unreal\Environments\LakeEnv\LakeEnv`，该目录下应包含 `Blocks.uproject` 文件 。

### 第二步：移植 AirSim 插件 (关键步骤)

解压后的环境包通常不包含核心插件，直接运行会报错 "AirSim plugin could not be found"。必须手动从主工程复制插件。

1. **寻找源插件**：

* 前往 ASVSim 主目录：`D:\ASVSim\Unreal\Plugins` (或原 `Blocks` 工程下的 Plugins)。
* 复制整个 `Plugins` 文件夹。

2. **植入新环境**：

* 进入湖泊环境目录：`D:\ASVSim\Unreal\Environments\LakeEnv\LakeEnv` 。
* 将复制的 `Plugins` 文件夹粘贴于此。

### 第三步：清理旧编译文件

为了防止版本冲突（"Modules are built with a different engine version" 错误），需要清理从其他环境带来的缓存文件。

1. 在 `LakeEnv` 根目录下，**删除**以下文件夹（如果存在）：

* `Binaries`
* `Intermediate`
* `Saved`

2. 进入 `LakeEnv\Plugins\AirSim` 目录，同样**删除**里面的：

* `Binaries`
* `Intermediate`

### 第四步：生成 VS 工程文件

1. 回到 `LakeEnv` 根目录。
2. 右键点击 `Blocks.uproject` 文件。
3. 选择 **Show more options** -> **Generate Visual Studio project files**。
4. 等待运行完成，文件夹中会出现一个新的 `Blocks.sln` (或 `UE5.sln`) 文件。

### 第五步：编译项目 (Rebuild)

1. **关闭** 所有正在运行的 UE5 编辑器或 Visual Studio 窗口。
2. 双击打开新生成的 `Blocks.sln`。
3. 在 Visual Studio 顶部工具栏设置：

* 编译配置：**DebugGame Editor**
* 平台：**Win64**

4. 在右侧“解决方案资源管理器”中：

* 找到 **Games** -> **Blocks** 项目。
* 右键点击 `Blocks`，选择 **Rebuild (重新生成)**。

5. 等待编译完成（Output 窗口显示 `Succeeded`）。

### 第六步：启动仿真

1. 在 Visual Studio 中点击顶部绿色的 **▶ Local Windows Debugger** 按钮。
2. UE5 编辑器将启动。
3. 点击编辑器上方的 **Play** 按钮。

**验证成功**：视口中显示湖面、地形以及一艘红色的 IDLab 仿真船只 。

---

## 4. 常见问题排查 (Troubleshooting)

* **错误：AirSim plugin missing**
* *原因*：忘记执行“第二步”复制 Plugins 文件夹。
* *解决*：手动复制 Plugins 文件夹到项目根目录。
* **错误：Modules are missing or built with a different version**
* *原因*：插件的二进制文件与当前项目不匹配。
* *解决*：**点击 No**，不要让 UE5 自动编译。执行“第三步”清理所有 Binaries/Intermediate 文件夹，然后在 VS 中执行 **Rebuild**。
* **现象：编译着色器 (Compiling Shaders) 很慢**
* *原因*：第一次加载新地图时，UE5 需要为显卡计算光照和材质。
* *解决*：这是正常现象，请耐心等待（3090 显卡通常需 2-5 分钟）。

---

## 5. 下一步计划

完成环境搭建后，接下来将进行：

1. **配置 settings.json**：将仿真模式从 Car 切换为 SurfaceVessel（船只模式）。
2. **Python 控制测试**：编写 Python 脚本控制船只运动。
3. **数据采集**：在湖面环境中测试图像与 LiDAR 数据录制。
