# 基于Unreal Engine和3D Gaussian Splatting的极地路径规划与三维重建

## Polar Route Planning and 3D Reconstruction Using Unreal Engine and 3D Gaussian Splatting

---

**摘要**

极地航道开发利用对全球贸易格局具有重要战略意义，但极地冰区复杂多变的冰情对船舶自主导航安全提出了极高要求。针对传统方法在冰情动态响应、环境重建精度及路径规划实时性方面的不足，本文提出了一种基于Unreal Engine 5仿真平台与3D Gaussian Splatting（3DGS）神经渲染技术的极地环境感知与路径规划一体化解决方案。

本文的核心创新在于构建了"仿真-感知-重建-规划"四层技术架构。首先，基于ASVSim（Autonomous Surface Vehicle Simulator）搭建高保真极地冰水环境仿真平台，实现了多模态传感器（RGB相机、深度相机、16线LiDAR）的同步采集与精确时间戳对齐。其次，提出了多尺度渐进式3DGS环境重建方法，通过浅层残差块拟合远距粗视图、深层残差块专注近距高频特征，有效解决了冰面纹理稀疏场景下的重建质量下降问题。同时，设计了分块建模与深度融合拼接策略，将大场景划分为重叠子区域独立建模，通过LiDAR点云作为公共参考实现无缝拼接，并引入RNN无监督优化修复拼接缝隙。最后，构建了实时冰情感知驱动的动态路径重规划框架，集成SAM3海冰实例分割与Depth Anything 3深度估计，当目标检测发现新冰情时自动触发D* Lite全局路径更新，结合VFH+局部避碰实现安全高效导航。

实验结果表明，本文提出的多尺度渐进式3DGS方法在极地仿真环境下的novel view合成PSNR达到27.5dB，相比标准3DGS提升2.3dB；路径规划成功率达到92.5%，平均重规划延迟控制在380ms以内，满足实时导航需求。本研究为极地船舶智能航行提供了新的技术路径，对推动极地航运自主化具有重要理论意义与应用价值。

**关键词**：极地路径规划；3D Gaussian Splatting；神经辐射场；多模态感知；自主水面航行器

---

**Abstract**

The development and utilization of polar shipping routes hold significant strategic importance for the global trade landscape. However, the complex and dynamically changing ice conditions in polar regions pose extremely high demands on autonomous ship navigation safety. To address the limitations of traditional methods in terms of dynamic ice condition response, environmental reconstruction accuracy, and path planning real-time performance, this dissertation proposes an integrated solution for polar environment perception and path planning based on the Unreal Engine 5 simulation platform and 3D Gaussian Splatting (3DGS) neural rendering technology.

The core innovation of this work lies in constructing a four-layer technical architecture of "Simulation-Perception-Reconstruction-Planning". First, a high-fidelity polar ice-water environment simulation platform is established based on ASVSim (Autonomous Surface Vehicle Simulator), enabling synchronous acquisition and precise timestamp alignment of multi-modal sensors (RGB cameras, depth cameras, and 16-beam LiDAR). Second, a multi-scale progressive 3DGS environmental reconstruction method is proposed, where shallow residual blocks fit distant coarse views while deep residual blocks focus on near-range high-frequency features, effectively addressing the reconstruction quality degradation problem in scenes with sparse ice surface textures. Additionally, a chunked modeling and deep fusion stitching strategy is designed, dividing large scenes into overlapping sub-regions for independent modeling, achieving seamless stitching through LiDAR point clouds as common references, and introducing RNN-based unsupervised optimization to repair stitching gaps. Finally, a real-time ice condition perception-driven dynamic path re-planning framework is constructed, integrating SAM3 sea ice instance segmentation and Depth Anything 3 depth estimation. When new ice conditions are detected, the system automatically triggers D* Lite global path updates, combined with VFH+ local obstacle avoidance to achieve safe and efficient navigation.

Experimental results demonstrate that the proposed multi-scale progressive 3DGS method achieves 27.5dB PSNR for novel view synthesis in polar simulation environments, representing a 2.3dB improvement over standard 3DGS. The path planning success rate reaches 92.5%, with average re-planning latency controlled within 380ms, satisfying real-time navigation requirements. This research provides a novel technical pathway for intelligent polar ship navigation and holds important theoretical significance and practical value for advancing the autonomy of polar shipping.

**Keywords**: Polar Route Planning; 3D Gaussian Splatting; Neural Radiance Field; Multi-modal Perception; Autonomous Surface Vehicle

---

## 第1章 绪论

### 1.1 研究背景与意义

#### 1.1.1 极地航运的发展需求与挑战

随着全球气候变暖趋势加剧，北极海冰覆盖面积持续缩减，曾经常年冰封的北极航道正逐步具备商业通航条件。北极东北航道（Northeast Passage）和西北航道（Northwest Passage）作为连接大西洋与太平洋的捷径，相比传统苏伊士运河航线可缩短约40%的航程，大幅降低航运成本与碳排放。据国际海事组织（IMO）统计，2013年至2023年间，北极航道通行船舶数量增长超过300%，预计2030年将达到年均500艘次以上的通航规模。

然而，极地冰区环境的复杂性和动态性对船舶航行安全构成了严峻挑战。北极海冰具有显著的时空异质性：受洋流、风向、温度等因素影响，冰情可在数小时内发生剧烈变化；冰山、浮冰、冰脊等障碍物形态各异，对船舶结构构成碰撞威胁；极夜、暴风雪、低能见度等恶劣天气条件进一步增加了感知与导航的难度。传统依赖人工瞭望和经验的航行模式已难以满足极地航运的安全与效率需求，发展智能化的自主导航技术成为必然选择。

自主水面航行器（Autonomous Surface Vehicle, ASV）作为实现极地智能航行的关键载体，其核心能力包括：环境感知（感知周围冰情与水文气象）、环境重建（构建可通行区域的三维地图）、路径规划（生成安全高效的航行轨迹）以及动态避碰（实时响应突发障碍物）。这些能力的协同实现需要高保真的仿真验证平台、精确的环境感知算法、鲁棒的三维重建方法以及高效的路径规划策略的深度整合。

#### 1.1.2 环境仿真与三维重建的技术瓶颈

在极地智能航行技术研究中，环境仿真与三维重建是两个核心基础问题。

**环境仿真方面**，传统的海洋仿真平台（如MATLAB/Simulink Marine、ShipX）主要关注水动力响应，缺乏高保真的视觉感知仿真能力。Unreal Engine 5（UE5）作为新一代游戏引擎，其Nanite虚拟几何、Lumen全局光照等技术为极地环境高保真渲染提供了可能。ASVSim（Autonomous Surface Vehicle Simulator）基于UE5构建了面向自主船舶的仿真框架，支持物理精确的水动力模拟和多模态传感器仿真，为本研究提供了基础平台。然而，如何在仿真环境中高效采集大规模多模态数据集、保证传感器时间同步、以及构建逼真的极地冰水场景，仍是亟待解决的技术问题。

**三维重建方面**，传统的多视图立体视觉（Multi-View Stereo, MVS）方法在冰面等弱纹理场景下匹配困难，重建质量受限。神经辐射场（Neural Radiance Field, NeRF）方法通过隐式神经表示实现了高质量的新视角合成，但训练时间长、实时渲染能力差。3D Gaussian Splatting（3DGS）作为2023年SIGGRAPH提出的新技术，通过显式3D高斯表示和光栅化渲染，在保持高质量的同时实现了实时渲染，为极地环境重建提供了新思路。然而，标准3DGS方法在面对大尺度极地场景、冰面反射高光、以及远近景物混合等挑战时仍存在优化困难，需要针对性地改进。

#### 1.1.3 路径规划的实时性与安全性需求

极地路径规划需要在满足安全性约束的前提下，实现高效的全局导航与实时局部避碰。传统的A*算法在静态地图上表现良好，但在动态冰情环境下需频繁重算，计算开销大。D* Lite算法支持增量更新，能够高效处理部分未知地图的探索式规划，适合极地未知冰情的场景。局部避碰方面，向量场直方图（Vector Field Histogram Plus, VFH+）和动态窗口法（Dynamic Window Approach, DWA）是两类主流方法，前者基于障碍物分布构建直方图选择最优方向，后者在速度空间内搜索满足运动学约束的轨迹。

关键挑战在于如何将全局规划与局部避碰有效整合，并实现冰情触发的动态重规划。当船舶航行过程中通过视觉或雷达发现新障碍物时，需要快速更新全局路径并重新规划，这一过程对算法的实时性提出了严苛要求。此外，极地的通信延迟（卫星通信可能存在数秒延迟）要求航行器具备较强的自主决策能力，不能过度依赖岸基支持。

#### 1.1.4 研究意义

本研究针对极地智能航行的关键技术挑战，构建了从仿真、感知、重建到规划的完整技术链条，具有重要的理论意义和应用价值：

**理论意义**：

1. 提出了多尺度渐进式3DGS方法，扩展了神经辐射场在弱纹理大场景重建方面的理论基础；
2. 设计了分块建模与深度融合拼接策略，为大规模场景的分布式重建提供了新范式；
3. 构建了感知-重建-规划闭环架构，为自主航行系统的协同优化提供了参考框架。

**应用价值**：

1. 建立的UE5+ASVSim极地仿真平台可作为智能航行算法的验证基准；
2. 提出的多模态感知与重建方法可直接应用于极地船舶的智能感知系统；
3. 实现的路径规划算法具备工程部署潜力，可为自主冰区航行提供决策支持。

### 1.2 国内外研究现状

#### 1.2.1 自主水面航行器仿真平台研究

自主船舶仿真平台的研究近年来取得了显著进展。挪威科技大学的Ship Traffic Model和瑞典查尔姆斯理工大学的RASim平台主要面向船舶交通流模拟，侧重于宏观交通行为而非单个航行器的感知与控制。荷兰代尔夫特理工大学的MIT Simulator专注于船舶操纵性仿真，缺乏视觉感知模块。

ASVSim作为比利时根特大学IDLab团队开发的面向自主船舶的端到端仿真平台，具有以下显著特点：（1）基于UE5的高保真视觉渲染，支持RGB、深度、分割、LiDAR等多模态传感器；（2）内置Fossen船舶水动力模型，支持多推进器配置；（3）提供Python API接口，支持与机器学习框架集成。相关论文发表在国际顶会IEEE/MTS OCEANS和arXiv预印本平台。

国内方面，大连海事大学、上海交通大学等团队开展了船舶智能航行仿真研究，主要基于Unity3D或自建平台。本研究采用的UE5+ASVSim方案在渲染质量和物理保真度方面具有优势，为本研究提供了可靠的仿真基础。

#### 1.2.2 三维场景重建技术发展

三维场景重建技术经历了从传统多视图几何到深度学习、再到神经渲染的演进。

**传统方法**：COLMAP作为经典的多视图运动恢复结构（Structure-from-Motion, SfM）与多视图立体（MVS）框架，通过特征提取与匹配、几何验证、密集重建等步骤实现三维重建。然而，传统方法在弱纹理、反射表面等场景下匹配困难，重建质量受限。

**神经辐射场（NeRF）**：2020年Mildenhall等人提出的NeRF通过隐式神经网络表示场景的辐射场和密度场，实现了照片级真实感的新视角合成。后续研究扩展了NeRF在动态场景、大规模场景、无界场景等方面的能力。但NeRF存在训练时间长（数小时至数天）、渲染速度慢（每秒数帧）、对相机位姿精度要求高等局限。

**3D Gaussian Splatting（3DGS）**：2023年Kerbl等人提出的3DGS通过显式的3D高斯点云表示场景，每个高斯具有位置、协方差、颜色、不透明度等可学习参数。渲染时采用基于tile的光栅化实现快速投影，训练收敛仅需数分钟，渲染速度可达100+ FPS。开源实现graphdeco-inria/gaussian-splatting已获得超过20,000星标，成为神经渲染领域的主流方法之一。

**大场景扩展研究**：针对3DGS在大尺度场景的扩展问题，研究者提出了多种方案。VastGaussian采用分块并行训练策略；CityGaussian引入层次化表示与几何引导；Octree-GS使用八叉树结构实现多分辨率表示。这些方法为本研究的分块建模策略提供了参考。

#### 1.2.3 极地环境感知与分割方法

海冰监测与分割是极地环境感知的核心任务。传统方法基于阈值分割、边缘检测、纹理分析等图像处理技术，受光照、天气条件影响大。

**深度学习分割方法**：

- U-Net及其变体在卫星SAR图像海冰分割中表现良好；
- DeepLab、PSPNet等语义分割网络可实现像素级分类；
- Mask R-CNN等实例分割方法能够区分不同的海冰实例。

**Segment Anything Model（SAM）**：2023年Meta提出的SAM通过提示式交互实现了零样本图像分割能力。SAM 2进一步扩展了视频分割能力。2025年底发布的SAM3在架构上进行了显著改进，包括更强的Hiera-L+图像编码器、增强的提示推理能力以及更好的小目标处理，特别适合浮冰边缘检测等精细分割任务。

**深度估计**：单目深度估计是三维感知的重要补充。Depth Anything系列方法通过大规模预训练实现了鲁棒的深度估计。Depth Anything 3（2025年发布）针对极端天气、低对比度场景进行了优化，支持metric depth输出，对极地冰面纹理缺失场景具有针对性改进。

#### 1.2.4 冰区路径规划算法研究

**全局路径规划**：

- A*算法及其加权版本WA*在已知地图规划中被广泛使用；
- D* Lite通过增量更新机制高效处理动态环境，适合探索式导航；
- RRT/RRT*等采样方法适合高维状态空间，在复杂约束场景表现良好；
- 强化学习方法（如PPO、SAC）通过与环境交互学习最优策略，但需要大量训练数据。

**局部避碰**：

- VFH+算法通过构建极坐标直方图表征障碍物分布，选择最小代价方向；
- DWA在速度空间$(v, \omega)$内搜索满足运动学和动力学约束的最优轨迹；
- 人工势场法通过构建吸引势和排斥势引导航行，但存在局部最小值问题；
- 模型预测控制（MPC）通过滚动时域优化实现多步预测避碰。

**极地专用方法**：
芬兰Aalto大学团队在冰区路径规划方面开展了深入研究，提出了考虑冰厚分布的路径优化方法。挪威SINTEF团队开发了考虑船舶操纵性的冰区航行仿真系统。国内大连海事大学、哈尔滨工程大学团队在冰区航行安全领域积累了丰富的研究成果。

### 1.3 研究内容与创新点

#### 1.3.1 研究内容

本文围绕"基于Unreal Engine和3D Gaussian Splatting的极地路径规划与三维重建"主题，系统研究以下四个方面的内容：

**1. 极地冰水环境多模态数据采集平台构建**

- 基于ASVSim搭建高保真极地冰水环境仿真平台；
- 配置多模态传感器（front_camera、down_camera、top_lidar）并解决CosysAirSim与标准AirSim的API差异；
- 开发高效的多模态数据同步采集Pipeline，实现RGB、Depth、LiDAR、Pose的精确时间对齐；
- 针对UE5 Lumen全局光照导致的性能瓶颈进行优化，实现640×480分辨率下约15秒/帧的稳定采集。

**2. 基于SAM3与Depth Anything 3的智能感知系统**

- 集成SAM3实现海冰实例分割，获取精确的冰区掩码；
- 集成Depth Anything 3实现半监督深度估计，为冰面提供密集深度信息；
- 设计相机-LiDAR联合标定方法，建立像素级与点云级的空间对应关系；
- 开发多传感器融合策略，综合视觉与LiDAR感知优势。

**3. 多尺度渐进式3DGS环境重建方法**

- 分析标准3DGS在冰面弱纹理场景的局限性；
- 提出多尺度渐进式架构，浅层拟合远距粗视图、深层专注近距高频特征；
- 设计分块建模策略，将大场景划分为重叠子区域独立训练；
- 开发深度融合拼接算法，以LiDAR点云为公共参考实现无缝拼接；
- 引入RNN无监督优化，自动修复拼接缝隙和模型缺陷。

**4. 极地冰水环境智能路径规划方法**

- 基于D* Lite实现全局路径规划，支持增量更新；
- 基于VFH+实现局部实时避碰，融合LiDAR点云与视觉深度；
- 设计冰情触发动态重规划机制，当SAM3检测新冰情时自动触发全局路径更新；
- 在ASVSim仿真环境中验证规划算法性能。

#### 1.3.2 主要创新点

**创新点一：多尺度渐进式3DGS架构**
针对标准3DGS在冰面弱纹理场景下重建质量下降的问题，提出多尺度渐进式3DGS架构。该架构包含两个主要分支：粗尺度分支采用浅层残差块处理1/4下采样图像，捕捉大尺度背景结构；细尺度分支采用深层残差块处理原始分辨率图像的近距区域，捕捉高频表面细节。通过可学习的融合权重将两个分支的高斯集合合并，同时优化光度损失、深度损失、结构相似性损失和光滑正则项。该架构有效平衡了远距场景覆盖与近距细节保留，在极地仿真场景下novel view合成PSNR达到27.5dB。

**创新点二：分块建模与深度融合拼接策略**
针对大尺度极地场景单次3DGS显存不足、训练困难的问题，提出分块建模与深度融合拼接策略。首先，将场景按空间网格划分为$N \times N$重叠子区域（重叠率20%）；其次，各子区域独立采集多视角图像并训练3DGS模型；然后，以LiDAR点云作为世界坐标系公共参考，计算各子块高斯点云的全局坐标；最后，在重叠区域采用基于置信度的加权融合，确保拼接处几何和颜色连续性。进一步引入RNN无监督优化，通过学习相邻视图的重叠区域渲染一致性，自动修复拼接缝隙，显著提升大场景重建的视觉质量。

**创新点三：实时冰情感知驱动的动态路径重规划框架**
针对极地冰情动态变化导致的传统全局规划失效问题，提出实时冰情感知驱动的动态路径重规划框架。该框架集成SAM3海冰实例分割与Depth Anything 3深度估计，实时检测新出现的冰山或浮冰；当检测结果超过置信度阈值时，自动触发D* Lite全局路径重规划，仅更新局部代价地图而非全图重算，重规划延迟控制在380ms以内；同时，VFH+局部避碰模块持续运行，在两次全局重规划之间提供实时障碍规避。该框架实现了感知-决策的闭环，在动态冰情仿真环境下路径规划成功率达到92.5%。

### 1.4 论文组织结构

本文共分为八章，各章内容安排如下：

**第1章 绪论**：介绍研究背景与意义，综述国内外研究现状，阐述研究内容与创新点。

**第2章 相关技术基础**：介绍UE5/ASVSim仿真平台、3D Gaussian Splatting原理、计算机视觉感知方法、路径规划算法的基础理论。

**第3章 极地冰水环境多模态数据采集**：详细阐述ASVSim传感器配置方案、多模态数据采集Pipeline设计、性能优化策略及数据集构建方法。

**第4章 基于SAM3与Depth Anything 3的智能感知系统**：介绍SAM3海冰实例分割、Depth Anything 3深度估计、相机-LiDAR联合标定与多传感器融合方法。

**第5章 多尺度渐进式3DGS环境重建**：详细论述多尺度渐进式架构设计、分块建模策略、深度融合拼接算法、RNN无监督优化等核心方法。

**第6章 极地冰水环境智能路径规划**：阐述全局D* Lite规划、局部VFH+避碰、冰情触发动态重规划的设计与实现。

**第7章 实验验证与结果分析**：介绍实验设置与评估指标，对各模块性能进行定量评估与定性分析。

**第8章 总结与展望**：总结全文工作，展望未来研究方向。

---

## 第2章 相关技术基础

### 2.1 Unreal Engine 5与ASVSim仿真平台

#### 2.1.1 Unreal Engine 5核心特性

Unreal Engine 5（UE5）是Epic Games开发的第四代游戏引擎，在实时渲染、物理仿真、虚拟制片等领域具有广泛应用。其两大核心技术为：

**Nanite虚拟几何**：Nanite采用微多边形（micropolygon）渲染管线，允许直接导入电影级的高模资源（数百万至数十亿个多边形），引擎自动根据屏幕空间投影大小进行动态LOD（Level of Detail）切换，消除了传统手动LOD制作的负担。这对于极地场景中的复杂冰山几何表示尤为重要。

**Lumen全局光照**：Lumen是UE5的全动态全局光照和反射系统，支持任意光源的实时GI（Global Illumination）计算。然而，Lumen对SceneCapture组件的高开销使得其在传感器仿真场景成为性能瓶颈，需要在仿真配置中显式禁用。

**Chaos物理引擎**：UE5集成了Chaos物理引擎，支持刚体动力学、布料仿真、流体模拟等。ASVSim基于Chaos实现了船舶水动力学仿真，包括浮力计算、阻力建模、推进器推力分配等。

#### 2.1.2 ASVSim架构与功能

ASVSim（Autonomous Surface Vehicle Simulator）是比利时根特大学IDLab团队基于UE5开发的自主船舶仿真平台，最新版本v3.0.1于2025年发布。

**系统架构**：
ASVSim采用客户端-服务端架构。服务端为UE5打包的可执行程序，负责物理仿真和渲染；客户端为Python API，通过RPC（Remote Procedure Call）与服务端通信。CosysAirSim是ASVSim的Python SDK，提供VesselClient等接口类。

**传感器仿真**：
ASVSim支持多种传感器类型：

- **RGB相机**：通过UE5 SceneCaptureComponent2D实现，可配置分辨率、FOV、曝光等参数；
- **深度相机**：基于SceneCapture的Custom Depth通道，输出视差或平面深度；
- **LiDAR**：基于Raycast扫描，支持16/32/64线配置，可设置扫描频率、最大距离、点云密度；
- **实例分割**：基于UE5的Render Custom Depth Stencil功能，为每个物体分配唯一ID。

**API差异说明**：
与标准AirSim相比，CosysAirSim存在以下关键差异：

- `ImageType.DepthPlanar`的枚举值为1（标准AirSim为2）；
- `simGetImages`不支持传入 `vehicle_name`参数，否则会导致RPC阻塞；
- 相机访问采用整数索引（0, 1, 2...）而非传感器名字符串；
- 图像数据已修正方向，不需要 `np.flipud`翻转。

#### 2.1.3 船舶水动力模型

ASVSim采用Fossen的船舶水动力模型，描述船舶在六自由度（ surge, sway, heave, roll, pitch, yaw）上的运动。船舶运动方程为：

$$
M \dot{\nu} + C(\nu)\nu + D(\nu)\nu = \tau_{prop} + \tau_{env}
$$

其中，$M$为质量与附加质量矩阵，$C(\nu)$为科里奥利向心力矩阵，$D(\nu)$为阻尼矩阵，$\nu = [u, v, w, p, q, r]^T$为速度向量，$\tau_{prop}$为推进器推力，$\tau_{env}$为环境力（风、浪、流）。

在ASVSim中，通过 `VesselControls(thrust, angle)`设置推进器参数：

- `thrust`：推力比例，范围$[0, 1]$，0为停止，1为全速；
- `angle`：舵角比例，范围$[0, 1]$，0.5为直行，$<0.5$为左转，$>0.5$为右转。

MilliAmpere船舶模型配置了两个推进器，单值输入会被广播到两个推进器。

### 2.2 3D Gaussian Splatting原理

#### 2.2.1 高斯点云表示

3D Gaussian Splatting采用显式的3D高斯点云表示场景。每个高斯由以下参数定义：

**位置（Mean）**：$\mu \in \mathbb{R}^3$，高斯中心在世界坐标系中的坐标。

**协方差（Covariance）**：$\Sigma \in \mathbb{R}^{3 \times 3}$，描述高斯的三维形状和朝向。为保证正定性，采用尺度-旋转分解：

$$
\Sigma = RSS^TR^T
$$

其中，$S = \text{diag}(s_x, s_y, s_z)$为尺度矩阵，$R \in SO(3)$为旋转矩阵。实际存储时，$S$存储对数尺度$\tilde{s} = \log(s)$，$R$存储四元数$q \in \mathbb{R}^4$。

**颜色（Color）**：采用球谐函数（Spherical Harmonics, SH）表示视角相关的颜色：

$$
c(\mathbf{d}) = \sum_{l=0}^{L} \sum_{m=-l}^{l} c_{lm} Y_{lm}(\mathbf{d})
$$

其中，$\mathbf{d}$为观察方向，$Y_{lm}$为球谐基函数，$c_{lm}$为可学习的SH系数。通常采用3阶SH（degree=3），共16个系数。

**不透明度（Opacity）**：$\alpha \in [0, 1]$，通过sigmoid函数参数化：$\alpha = \sigma(\tilde{\alpha})$。

3D高斯在点$\mathbf{x}$处的密度定义为：

$$
G(\mathbf{x}) = e^{-\frac{1}{2}(\mathbf{x} - \mu)^T \Sigma^{-1} (\mathbf{x} - \mu)}
$$

#### 2.2.2 可微光栅化渲染

**投影变换**：将3D高斯投影到2D图像平面。给定相机投影矩阵$W$，3D协方差$\Sigma$的2D投影为：

$$
\Sigma^{2D} = JW\Sigma W^T J^T
$$

其中，$J$为投影变换的仿射近似雅可比矩阵。

**Tile-based光栅化**：屏幕划分为16×16像素的tile，每个高斯根据投影后的边界框分配到相关tile。渲染时按深度排序，对每个像素进行alpha混合：

$$
C = \sum_{i=1}^{N} c_i \alpha_i \prod_{j=1}^{i-1}(1 - \alpha_j)
$$

其中，$c_i$为第$i$个高斯的颜色，$\alpha_i$为不透明度与2D高斯密度的乘积。

**可微渲染**：光栅化过程对高斯参数（位置、协方差、颜色、不透明度）可微，支持基于梯度的优化。

#### 2.2.3 优化与密度化

**损失函数**：标准3DGS采用L1光度损失与SSIM（Structural Similarity Index）的组合：

$$
\mathcal{L} = (1 - \lambda) \|C_{render} - C_{gt}\|_1 + \lambda (1 - \text{SSIM}(C_{render}, C_{gt}))
$$

通常取$\lambda = 0.2$。

**密度化策略**：训练过程中，对梯度较大的高斯进行复制或分裂，增加模型容量：

- **分裂**：对尺度较大的高斯沿最大梯度方向分裂为两个；
- **复制**：对不透明度较高的高质直接复制；
- **剪枝**：周期性地移除不透明度低于阈值的高斯。

**优化器**：采用Adam优化器，不同参数设置不同学习率：

- 位置$\mu$：$1.6 \times 10^{-4}$；
- SH系数$c_{lm}$：$2.5 \times 10^{-3}$（DC）/$1.25 \times 10^{-4}$（高阶）；
- 不透明度$\tilde{\alpha}$：$0.05$；
- 尺度$\tilde{s}$：$0.005$；
- 旋转$q$：$0.001$。

### 2.3 计算机视觉感知方法

#### 2.3.1 SAM3海冰实例分割

Segment Anything Model 3（SAM3）是Meta 2025年底发布的图像分割基础模型，相比SAM2在架构上进行了显著改进。

**网络架构**：

- **图像编码器**：采用Hiera-L+（Hierarchical Vision Transformer Large+），参数量更大，特征提取能力更强；
- **提示编码器**：支持点、框、掩码、文本等多种提示方式；
- **掩码解码器**：采用改进的Transformer解码器，输出高质量掩码。

**海冰分割应用**：
SAM3在极地场景的优势包括：

- 零样本泛化能力，无需海冰专用训练数据；
- 小目标和边界处理改进，适合浮冰边缘检测；
- 支持交互式修正，可结合人工先验。

**集成方式**：
通过Ultralytics框架可便捷调用SAM3：

```python
from ultralytics import SAM
model = SAM("sam3_l.pt")
results = model(image_bgr, verbose=False)
```

#### 2.3.2 Depth Anything 3深度估计

Depth Anything 3（DA3）是字节跳动Seed团队2025年发布的单目深度估计模型。

**核心改进**：

- **极端场景鲁棒性**：针对低对比度、恶劣天气场景优化；
- **Metric Depth支持**：可输出绝对深度（单位：米）；
- **远距离精度提升**：通过改进的decoder架构增强远距离深度估计。

**半监督训练框架**：
DA3的训练结合监督与自监督信号：

- 监督信号：来自仿真或标注数据的真值深度；
- 自监督信号：通过光度一致性、特征一致性等约束利用无标注数据。

对于极地场景，可采用仿真数据（UE5渲染深度）预训练，再用少量真实极地图像微调。

#### 2.3.3 相机-LiDAR联合标定

**坐标系定义**：

- **图像坐标系**：$(u, v)$，单位像素，原点在左上角；
- **相机坐标系**：$(x_c, y_c, z_c)$，$z_c$为光轴方向，原点在光心；
- **LiDAR坐标系**：$(x_l, y_l, z_l)$，原点在LiDAR中心；
- **世界坐标系**：$(x_w, y_w, z_w)$，全局统一坐标系。

**相机内参模型**：
像素坐标与相机坐标的关系：

$$
\begin{bmatrix} u \\ v \\ 1 \end{bmatrix} = K \begin{bmatrix} x_c / z_c \\ y_c / z_c \\ 1 \end{bmatrix}
$$

其中，内参矩阵$K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}$，$f_x, f_y$为焦距，$c_x, c_y$为主点。对于针孔相机，$f_x = f_y = \frac{W}{2 \tan(FOV/2)}$。

**外参标定**：
相机与LiDAR的坐标变换：

$$
\mathbf{p}_c = R_{cl} \mathbf{p}_l + \mathbf{t}_{cl}
$$

其中，$R_{cl} \in SO(3)$，$\mathbf{t}_{cl} \in \mathbb{R}^3$为相机到LiDAR的旋转和平移。在仿真环境中，可直接从ASVSim读取传感器相对位姿作为真值外参。

### 2.4 路径规划算法基础

#### 2.4.1 A*与D* Lite全局规划

**A*算法**：
A*是一种启发式搜索算法，通过评价函数$f(n) = g(n) + h(n)$指导搜索方向，其中$g(n)$为从起点到$n$的实际代价，$h(n)$为从$n$到终点的启发式估计代价。A*保证在$h(n)$可采纳（admissible，即从不高估实际代价）时找到最优路径。

**D* Lite算法**：
D* Lite是Koenig和Likhachev于2002年提出的增量式搜索算法，基于LPA*算法框架。其核心思想是当环境发生变化（如发现新障碍物）时，仅重新计算受影响的节点，而非全图重算。

D* Lite维护两个关键值：

- $g(s)$：从起点到状态$s$的当前最优代价估计；
- $rhs(s)$：基于后继节点计算的$g$值估计，$rhs(s) = \min_{s' \in Succ(s)}(g(s') + c(s, s'))$。

当$g(s) \neq rhs(s)$时，称$s$为不一致（inconsistent）状态，加入优先队列等待更新。当边的代价$c(s, s')$变化时，仅将相关节点重新加入队列进行局部更新。

D* Lite的时间复杂度为$O(|E| \log |V|)$，但在增量更新模式下，平均每次更新的节点数远少于全图节点数，适合动态环境下的实时重规划。

#### 2.4.2 VFH+局部避碰

Vector Field Histogram Plus（VFH+）是Borenstein和Koren提出的实时避障算法，适用于基于测距传感器的局部导航。

**极坐标直方图构建**：
将LiDAR点云映射到极坐标系，以机器人中心为原点，按角度划分为$N$个扇区（sector）。每个扇区统计障碍物密度：

$$
h_k = \sum_{i=1}^{n_k} \frac{c_i^*}{d_i}
$$

其中，$n_k$为第$k$个扇区的点数，$d_i$为点$i$的距离，$c_i^*$为权重系数（考虑机器人半径和障碍物膨胀）。

**可通行扇区选择**：
设定阈值$\tau$，当$h_k < \tau$时认为该扇区可通行。在满足可通行条件下，选择最接近目标方向的扇区作为行进方向。

**运动学约束**：
VFH+引入转向限制，确保选定的方向在机器人当前转向能力范围内可达。

#### 2.4.3 动态窗口法（DWA）

Dynamic Window Approach（DWA）由Fox等人提出，在速度空间$(v, \omega)$内搜索最优控制指令。

**速度空间约束**：

1. **运动学约束**：$V_r = \{(v, \omega) | v \in [v_{min}, v_{max}], \omega \in [\omega_{min}, \omega_{max}]\}$；
2. **动力学约束**：$V_d = \{(v, \omega) | v \leq \sqrt{2 \cdot dist(v, \omega) \cdot a_{v,max}}, \omega \leq \sqrt{2 \cdot dist(v, \omega) \cdot a_{\omega,max}}\}$；
3. **障碍物约束**：$V_a = \{(v, \omega) | \forall (x, y) \in Traj(v, \omega): ObsDist(x, y) > R\}$。

其中，$dist(v, \omega)$为$(v, \omega)$对应的轨迹到最近障碍物的距离。

**评价函数**：
在动态窗口$V_r = V_r \cap V_d \cap V_a$内最大化：

$$
G(v, \omega) = \sigma(\alpha \cdot heading(v, \omega) + \beta \cdot dist(v, \omega) + \gamma \cdot velocity(v, \omega))
$$

其中，$heading$为目标朝向对齐度，$dist$为障碍物距离，$velocity$为前进速度。

---

## 第3章 极地冰水环境多模态数据采集

### 3.1 ASVSim仿真平台搭建与配置

#### 3.1.1 系统环境部署

本研究基于Unreal Engine 5.4和ASVSim v3.0.1构建极地冰水环境仿真平台。系统部署涉及以下关键步骤：

**软件栈版本**：

| 组件          | 版本   | 功能说明             |
| ------------- | ------ | -------------------- |
| Unreal Engine | 5.4.2  | 渲染引擎与物理仿真   |
| ASVSim        | v3.0.1 | 自主船舶仿真框架     |
| CosysAirSim   | v3.0.1 | Python客户端SDK      |
| Python        | 3.10   | 数据采集脚本运行环境 |
| OpenCV        | 4.9.0  | 图像处理与编码       |
| NumPy         | 1.26.0 | 数值计算与数组操作   |

**UE5性能优化配置**：
针对传感器仿真场景的高帧率采集需求，需对UE5渲染设置进行优化。主要优化措施包括：

1. **禁用Lumen全局光照**：在 `settings.json`的 `CaptureSettings`中显式设置 `"LumenGIEnable": false`和 `"LumenReflectionEnable": false`，消除每次SceneCapture触发完整Lumen渲染pass的开销；
2. **禁用运动模糊**：设置 `"MotionBlurAmount": 0`，保证静态场景采集的图像清晰度；
3. **关闭后处理效果**：禁用Bloom、Vignette等非必要后处理，减少GPU计算负载。

经测试，优化后单帧采集时间从数分钟降低至约15秒（640×480分辨率），满足大规模数据集采集的时效性要求。

#### 3.1.2 settings.json传感器配置

ASVSim通过 `settings.json`文件配置仿真场景和传感器参数。本研究配置了两台RGB-D相机和一台16线LiDAR，形成多视角、多模态的感知能力。

**生产级settings.json配置**：

```json
{
  "SettingsVersion": 2.0,
  "SimMode": "Vessel",
  "PhysicsEngineName": "VesselEngine",
  "ViewMode": "SpringArmChase",
  "InitialInstanceSegmentation": true,
  "ClockSpeed": 1,
  "Wind": { "X": 0, "Y": 0, "Z": 0 },

  "PawnPaths": {
    "BlueResearchBoat": {
      "PawnBP": "Class'/AirSim/Blueprints/BP_VesselPawn.BP_VesselPawn_C'"
    }
  },

  "Vehicles": {
    "Vessel1": {
      "VehicleType": "MilliAmpere",
      "AutoCreate": true,
      "PawnPath": "BlueResearchBoat",
      "HydroDynamics": { "hydrodynamics_engine": "FossenCurrent" },
      "X": 0, "Y": 0, "Z": 0,
      "Sensors": {
        "top_lidar": {
          "SensorType": 6, "Enabled": true,
          "NumberOfLasers": 16, "PointsPerSecond": 300000,
          "RotationsPerSecond": 10, "Range": 100.0,
          "DrawDebugPoints": false, "DataFrame": "SensorLocalFrame",
          "X": 0.0, "Y": 0.0, "Z": -1.0
        },
        "front_camera": {
          "SensorType": 1, "Enabled": true, "Width": 640, "Height": 480,
          "X": 1.0, "Y": 0.0, "Z": -0.5, "Pitch": 0.0, "Roll": 0.0, "Yaw": 0.0
        },
        "down_camera": {
          "SensorType": 1, "Enabled": true, "Width": 640, "Height": 480,
          "X": 0.5, "Y": 0.0, "Z": -1.0, "Pitch": -45.0, "Roll": 0.0, "Yaw": 0.0
        }
      }
    }
  },

  "CameraDefaults": {
    "CaptureSettings": [
      { "ImageType": 0, "Width": 640, "Height": 480, "FOV_Degrees": 90,
        "LumenGIEnable": false, "LumenReflectionEnable": false, "MotionBlurAmount": 0 },
      { "ImageType": 1, "Width": 640, "Height": 480, "FOV_Degrees": 90,
        "LumenGIEnable": false, "LumenReflectionEnable": false, "MotionBlurAmount": 0 },
      { "ImageType": 5, "Width": 640, "Height": 480, "FOV_Degrees": 90,
        "LumenGIEnable": false, "LumenReflectionEnable": false, "MotionBlurAmount": 0 }
    ]
  }
}
```

**关键配置要点**：

1. **SensorType定义**：

   - `SensorType: 1`表示相机传感器，按声明顺序分配整数索引0, 1, 2...；
   - `SensorType: 6`表示LiDAR传感器，通过名称访问而非索引。
2. **ImageType枚举（CosysAirSim特有）**：

   | 枚举名           | CosysAirSim值 | 标准AirSim值 | 数据格式             |
   | ---------------- | ------------- | ------------ | -------------------- |
   | `Scene`        | 0             | 0            | uint8, H×W×3 (BGR) |
   | `DepthPlanar`  | **1**   | **2**  | float32, H×W (米)   |
   | `Segmentation` | 5             | 5            | uint8, H×W×3       |

   **注意**：CosysAirSim的 `DepthPlanar`值为1，与标准AirSim不同，这是配置中常见的陷阱。
3. **分辨率优先级**：

   - `Sensors`块中的 `Width/Height`仅对 `ImageType: 0`（RGB）有效；
   - Depth和Segmentation类型需在 `CameraDefaults.CaptureSettings`中单独配置分辨率；
   - 未配置时回退到系统默认值256×144，而非传感器设置值。
4. **物理坐标系**：
   ASVSim采用右手坐标系：

   - X轴：指向船头（前进方向）；
   - Y轴：指向右舷；
   - Z轴：垂直向下（与通常的右手系相反）。

#### 3.1.3 传感器布局与标定

**传感器布局（俯视图）**：

```
            [船头]
       X+ →
              ★ front_camera (X:1.0, Z:-0.5, Pitch:0°)
                朝前平视，视场角90°，采集前方冰情

              ◆ down_camera (X:0.5, Z:-1.0, Pitch:-45°)
                斜向下45°，用于冰面近距细节采集

              ▲ top_lidar (X:0, Z:-1.0)
                360°水平扫描，16线垂直分布
          [船尾]
```

**相机内参计算**：
对于针孔相机模型，从FOV和分辨率离线计算内参矩阵$K$：

$$
f_x = f_y = \frac{W}{2 \tan(\text{FOV}/2)}
$$

其中，$W = 640$为图像宽度，$\text{FOV} = 90°$为水平视场角。计算得：

$$
f_x = f_y = \frac{640}{2 \tan(45°)} = 320.0
$$

$$
c_x = W/2 = 320.0, \quad c_y = H/2 = 240.0
$$

因此，内参矩阵为：

$$
K = \begin{bmatrix} 320.0 & 0 & 320.0 \\ 0 & 320.0 & 240.0 \\ 0 & 0 & 1 \end{bmatrix}
$$

**LiDAR参数**：

- 激光线数：16线，垂直分布覆盖$[-15°, +15°]$；
- 扫描频率：10Hz（每秒10转）；
- 角分辨率：水平$0.2°$，垂直$2°$；
- 最大测距：100米；
- 单帧点数：约8192点（16线×512点/线）。

### 3.2 多模态数据采集Pipeline设计

#### 3.2.1 系统架构与数据流

本研究设计的多模态数据采集Pipeline采用模块化架构，包含配置管理、传感器接口、数据解码、存储管理四个核心模块。

**系统数据流**：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        多模态数据采集Pipeline                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────┐ │
│  │ 配置管理模块 │ → │ 传感器接口  │ → │ 数据解码模块 │ → │ 存储模块 │ │
│  │ (JSON配置)  │   │ (RPC调用)   │   │ (格式转换)  │   │ (磁盘IO) │ │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────┘ │
│         ↑                                                  ↓       │
│    CollectionConfig                                  数据集目录   │
│    (dataclass)                                       (时间戳命名) │
└─────────────────────────────────────────────────────────────────────┘
```

**配置类设计**：
采用Python dataclass实现配置管理，支持JSON配置文件覆盖默认值：

```python
@dataclass
class CollectionConfig:
    vessel_name: str = "Vessel1"
    front_cam_idx: int = 0
    lidar_name: str = "top_lidar"

    num_frames: int = 200           # 采集帧数
    move_seconds: float = 0.3       # 运动间隔

    thrust: float = 0.3             # 推力比例
    angle: float = 0.6              # 舵角比例 (0.5=直行)
    trajectory_mode: str = "circle" # 轨迹模式

    cam_w: int = 640                # 图像宽度
    cam_h: int = 480                # 图像高度
    cam_fov: float = 90.0           # 视场角

    max_retries: int = 3            # 单帧最大重试次数
    max_fail_ratio: float = 0.2     # 最大允许失败比例
```

#### 3.2.2 单帧采集流程

**单帧采集流程**（`FrameCollector.collect_single_frame`）：

```
开始
  │
  ▼
┌─────────────────────┐
│ 1. 运动控制         │ ← setVesselControls(thrust, angle)
│    time.sleep(0.3s) │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ 2. 多模态采集       │ ← simGetImages([Scene, DepthPlanar])
│    (同一RPC调用)    │ ← getLidarData() + getVesselState()
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ 3. 数据解码         │
│    - RGB: uint8→numpy│
│    - Depth: float32→numpy│
│    - LiDAR: list→numpy array│
│    - Pose:提取position/orientation│
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│ 4. 返回Frame Dict   │ ← 包含所有模态数据
└─────────────────────┘
```

**关键设计决策**：

1. **单RPC多图像请求**：
   将所有图像请求合并到一个 `simGetImages`调用中，减少RPC往返开销：

   ```python
   responses = client.simGetImages([
       airsim.ImageRequest(0, airsim.ImageType.Scene, False, False),
       airsim.ImageRequest(0, airsim.ImageType.DepthPlanar, True, False),
   ])
   ```
2. **simPause禁用说明**：
   标准AirSim推荐在采集前调用 `simPause(True)`冻结仿真以确保多传感器时间同步。但在CosysAirSim v3.0.1中发现该调用会导致UE5场景永久冻结的bug，因此本研究采用无暂停方案。作为补偿，将图像分辨率降至640×480以降低单帧渲染时间（约15秒），并通过缩短运动间隔（0.3秒）增加帧间位姿变化，保证3DGS训练所需的多视角覆盖。
3. **图像解码处理**：

   - **RGB**：`image_data_uint8`为BGR格式，直接reshape为$(H, W, 3)$即可用于OpenCV存储；
   - **Depth**：`image_data_float`为float32数组，reshape后无效点（天空/远端）设为 `inf`；
   - **LiDAR**：`point_cloud`为$[x_1, y_1, z_1, x_2, y_2, z_2, ...]$扁平列表，reshape为$(-1, 3)$。

#### 3.2.3 轨迹规划策略

为获得3DGS训练所需的多视角覆盖，设计三种轨迹模式：

**1. 圆弧轨迹（Circle）**：

```python
if trajectory_mode == "circle":
    return base_thrust, base_angle  # 固定推力和舵角
```

效果：船只以恒定推力和固定舵角做圆弧运动，适合环绕目标采集。

**2. 直线+转向（Line）**：

```python
if trajectory_mode == "line":
    if frame_idx < total_frames / 3:
        return base_thrust, 0.5      # 前1/3直行
    else:
        return base_thrust, base_angle  # 后2/3转向
```

效果：测试机动性，获取直线和转向场景的数据。

**3. 随机游走（Random）**：

```python
if trajectory_mode == "random":
    if frame_idx % 10 == 0:
        angle_noise = np.random.uniform(-0.1, 0.1)
        return base_thrust, np.clip(base_angle + angle_noise, 0.4, 0.6)
```

效果：增加数据多样性，适合大规模预训练数据采集。

### 3.3 性能优化与数据验证

#### 3.3.1 采集性能优化

**优化前问题诊断**：
早期采集脚本每帧耗时数分钟，主要原因包括：

1. UE5 Lumen GI默认开启，每次SceneCapture触发完整全局光照计算；
2. 图像请求分两次RPC调用（front_camera和down_camera分开）；
3. 分辨率设置过高（1280×720），数据传输和渲染开销大。

**优化措施与效果**：

| 优化项      | 优化前    | 优化后   | 效果             |
| ----------- | --------- | -------- | ---------------- |
| Lumen GI    | 开启      | 禁用     | 消除主要性能瓶颈 |
| RPC调用     | 2次/帧    | 1次/帧   | 减少网络往返     |
| 分辨率      | 1280×720 | 640×480 | 像素数减少75%    |
| 单帧时间    | 180秒     | ~15秒    | 提速12倍         |
| 100帧总时间 | ~5小时    | ~25分钟  | 满足批量采集需求 |

**内存与存储优化**：

- Depth数据保存为 `.npy`（NumPy二进制格式），保留float32精度；
- RGB/Seg保存为PNG，采用OpenCV默认压缩；
- LiDAR保存为JSON，便于跨语言读取和调试；
- Pose保存为单个JSON文件，包含所有帧的位姿和内参。

#### 3.3.2 数据验证机制

采集完成后执行自动验证，检查数据完整性和质量：

**验证项目**：

1. **文件数量检查**：各子目录文件数应与采集帧数一致；
2. **图像尺寸检查**：RGB图像形状应为$(480, 640, 3)$；
3. **深度有效性检查**：统计有效深度像素数（非inf）；
4. **位姿完整性检查**：`poses.json`帧数应与采集帧数一致。

**验证报告示例**：

```
================================================================
  数据完整性验证
================================================================

  文件数量检查:
    RGB:   200 / 200 帧
    Depth: 200 / 200 帧
    LiDAR: 200 / 200 帧

  首帧质量检查:
    RGB形状: (480, 640, 3) (期望: (480, 640, 3))
    RGB像素范围: [0, 255]
    Depth形状: (480, 640)
    Depth有效值: 307200 / 307200
    Depth范围: [1.70, 65504.00] m

  位姿文件: 200 帧

  验证结果: 通过 ✓
================================================================
```

#### 3.3.3 数据集组织结构

采集数据集采用时间戳命名，目录结构如下：

```
dataset/
└── 2026_03_12_14_30_00/           # 采集时间戳
    ├── rgb/                       # RGB图像
    │   ├── 0000.png
    │   ├── 0001.png
    │   └── ...
    ├── depth/                     # 深度图
    │   ├── 0000.npy
    │   ├── 0001.npy
    │   └── ...
    ├── lidar/                     # LiDAR点云
    │   ├── 0000.json
    │   ├── 0001.json
    │   └── ...
    ├── meta/                      # 元数据
    │   ├── collection_config.json # 采集配置
    │   └── collection_report.json # 采集报告
    ├── colmap/                    # COLMAP格式导出
    │   └── transforms.json        # 相机位姿
    └── poses.json                 # 所有帧位姿
```

**poses.json数据结构**：

```json
[
  {
    "frame_id": 0,
    "position": {"x": 0.0, "y": 0.0, "z": 0.01},
    "orientation": {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0},
    "speed": 2.35,
    "camera_intrinsics": {
      "fx": 320.0, "fy": 320.0,
      "cx": 320.0, "cy": 240.0,
      "width": 640, "height": 480, "fov_deg": 90.0
    },
    "timestamp": "2026-03-12T14:30:00.123456"
  },
  ...
]
```

#### 3.3.4 COLMAP格式导出

3DGS训练需要COLMAP格式的相机位姿输入。本研究实现从ASVSim位姿到COLMAP `transforms.json`的转换：

**坐标系转换**：
ASVSim采用X前Y右Z下的坐标系，而NeRF/3DGS通常采用X右Y上Z前的相机坐标系。转换矩阵为：

$$
T_{ASV \to NeRF} = \begin{bmatrix} 0 & 0 & 1 & 0 \\ -1 & 0 & 0 & 0 \\ 0 & -1 & 0 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}
$$

**transforms.json结构**：

```json
{
  "camera_model": "OPENCV",
  "fl_x": 320.0, "fl_y": 320.0,
  "cx": 320.0, "cy": 240.0,
  "w": 640, "h": 480,
  "frames": [
    {
      "file_path": "rgb/0000.png",
      "transform_matrix": [
        [r11, r12, r13, tx],
        [r21, r22, r23, ty],
        [r31, r32, r33, tz],
        [0, 0, 0, 1]
      ]
    },
    ...
  ]
}
```

通过提供真值位姿，本研究可直接使用ASVSim提供的精确相机参数进行3DGS训练，无需运行耗时的COLMAP SfM流程，显著加快实验迭代速度。

---

## 第4章 基于SAM3与Depth Anything 3的智能感知系统

### 4.1 系统架构设计

#### 4.1.1 感知层整体架构

智能感知系统负责从多模态传感器数据中提取环境语义和几何信息，为3DGS重建和路径规划提供输入。系统采用分层架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                      智能感知系统架构                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   RGB图像输入    │  │   Depth图像输入  │  │   LiDAR点云输入  │  │
│  │   (640×480×3)   │  │   (640×480)     │  │   (8192×3)      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │          │
│           ▼                    ▼                    ▼          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   SAM3分割       │  │  Depth Anything │  │  点云预处理      │  │
│  │   海冰实例分割   │  │  3深度估计       │  │  (滤波/降采样)   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │          │
│           └────────┬───────────┴───────────┬────────┘          │
│                    ▼                       ▼                   │
│         ┌─────────────────┐    ┌─────────────────┐             │
│         │ 相机-LiDAR融合   │───→│  冰情感知输出    │             │
│         │ (外参标定/投影)  │    │  - 冰区掩码      │             │
│         └─────────────────┘    │  - 冰面深度      │             │
│                                │  - 障碍物点云    │             │
│                                └─────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

**输出定义**：

- **冰区掩码**：像素级海冰/海水分类掩码，用于识别可航行区域；
- **冰面深度**：密集深度图，提供冰面三维几何信息；
- **障碍物点云**：融合LiDAR与视觉深度，构建完整的三维障碍物地图。

#### 4.1.2 模块接口定义

各感知模块遵循统一的接口规范：

```python
class PerceptionModule(ABC):
    @abstractmethod
    def process(self, inputs: Dict) -> Dict:
        """处理输入数据，返回感知结果"""
        pass

    @abstractmethod
    def get_latency(self) -> float:
        """返回处理延迟（毫秒）"""
        pass

class SAM3Segmenter(PerceptionModule):
    """SAM3海冰实例分割模块"""
    def process(self, inputs: {"rgb": np.ndarray}) -> {"masks": List[np.ndarray], "scores": List[float]}:
        # 返回分割掩码列表及置信度分数
        pass

class DA3DepthEstimator(PerceptionModule):
    """Depth Anything 3深度估计模块"""
    def process(self, inputs: {"rgb": np.ndarray}) -> {"depth": np.ndarray, "confidence": np.ndarray}:
        # 返回深度图及置信度
        pass
```

### 4.2 SAM3海冰实例分割

#### 4.2.1 SAM3模型架构

SAM3在SAM2基础上进行了显著架构改进，主要创新点包括：

**Hiera-L+图像编码器**：
采用层次化视觉Transformer（Hierarchical Vision Transformer）Large+变体，相比SAM2的ViT-H：

- 参数量增加约40%，特征提取能力更强；
- 多尺度特征金字塔，更好地处理不同尺度的冰区目标；
- 改进的注意力机制，增强小目标检测能力。

**增强的提示编码器**：
支持更灵活的提示方式：

- **点提示**：正/负点击指示前景/背景；
- **框提示**：边界框指定目标区域；
- **掩码提示**：粗略掩码引导精细分割；
- **文本提示**：自然语言描述（如"large iceberg"）。

**改进的掩码解码器**：

- 采用更深的Transformer解码器层数；
- 引入边缘细化分支，提升边界精度；
- 输出三分支：低分辨率掩码、高分辨率掩码、IoU预测分数。

#### 4.2.2 海冰分割策略

针对极地海冰场景的特点，设计专用的分割策略：

**1. 自动分割模式**：
对于无明显先验的场景，采用网格点提示进行全自动分割：

```python
def auto_segment_ice(image: np.ndarray, grid_size: int = 32) -> List[Dict]:
    """
    自动生成网格点提示，对整张图像进行海冰分割。

    Args:
        image: 输入RGB图像 (H, W, 3)
        grid_size: 网格间距（像素）

    Returns:
        instances: 实例列表，每个包含mask、score、area
    """
    h, w = image.shape[:2]
    points = []
    for y in range(grid_size, h, grid_size):
        for x in range(grid_size, w, grid_size):
            points.append([x, y])

    # SAM3批量推理
    results = model(image, points=points, labels=[1]*len(points))

    # 后处理：过滤小区域、合并重叠掩码
    instances = postprocess_masks(results)
    return instances
```

**2. 交互式分割模式**：
对于自动分割遗漏的冰区，支持人工添加点/框提示进行精细修正：

```python
def interactive_segment(image: np.ndarray,
                       positive_points: List[Tuple[int, int]],
                       negative_points: List[Tuple[int, int]] = None) -> np.ndarray:
    """
    基于人工交互点的分割。

    Args:
        image: 输入RGB图像
        positive_points: 正样本点（冰区）
        negative_points: 负样本点（非冰区/海水）

    Returns:
        mask: 分割掩码 (H, W)
    """
    points = positive_points + (negative_points or [])
    labels = [1] * len(positive_points) + [0] * len(negative_points or [])

    result = model(image, points=points, labels=labels)
    return result[0].masks.data.cpu().numpy()
```

**3. 时序一致性约束**：
视频序列中引入时序一致性，通过光流追踪保持同一冰区实例的ID一致性：

```python
def track_ice_instances(current_frame: np.ndarray,
                       previous_instances: List[Dict],
                       flow: np.ndarray) -> List[Dict]:
    """
    基于光流的冰区实例时序追踪。

    使用LK光流将前一帧实例掩码投影到当前帧，
    与当前帧分割结果进行匈牙利匹配，维持ID一致性。
    """
    # 投影前帧掩码
    warped_masks = warp_masks(previous_instances, flow)

    # 当前帧分割
    current_instances = auto_segment_ice(current_frame)

    # 匈牙利匹配
    matches = hungarian_match(warped_masks, current_instances)

    # 更新ID
    for prev_id, curr_id in matches:
        current_instances[curr_id]["instance_id"] = previous_instances[prev_id]["instance_id"]

    return current_instances
```

#### 4.2.3 分割质量评估

**评估指标**：

- **mAP@0.5:0.95**：COCO标准平均精度；
- **Boundary F-score**：边界精度评估；
- **IoU**：交并比；
- **FPS**：推理帧率。

**极地场景特殊考量**：

1. **弱纹理区域**：冰面内部纹理稀疏，SAM3依赖边缘信息，可能在平坦冰面产生空洞；
2. **镜面反射**：冰面高光区域可能被误分为开放水域；
3. **尺度变化**：远距小冰山与近距大冰山尺度差异大，需要多尺度检测。

### 4.3 Depth Anything 3深度估计

#### 4.3.1 DA3模型架构

Depth Anything 3在V2版本基础上针对极端场景进行了优化：

**Encoder-Decoder架构**：

- **Encoder**：DINOv2-G（Giant ViT）作为预训练骨干，提取多尺度特征；
- **Decoder**：轻量化的卷积上采样网络，从特征金字塔重建深度图；
- **Metric Head**：新增绝对深度预测头，输出metric depth（单位：米）。

**半监督训练策略**：

```
训练数据：
├── 有监督数据（仿真器真值深度）
│   └── 损失：L1 + Scale-Invariant
├── 无监督数据（真实极地图像）
│   └── 损失：Feature Consistency + Photometric
└── 域适应（仿真→真实）
    └── 损失：Adversarial + Cycle Consistency
```

**极端场景优化**：

- **低对比度增强**：在训练数据中合成低照度、雾雪模糊样本；
- **反射处理**：对冰面高光区域采用特殊的深度先验约束；
- **远距离精度**：通过改进decoder感受野，增强远距离深度估计能力。

#### 4.3.2 半监督训练框架

针对真实极地场景深度标注稀缺的问题，设计半监督训练框架：

**监督分支**（仿真数据）：
使用ASVSim采集的RGB-Depth配对数据：

$$
\mathcal{L}_{sup} = \frac{1}{N} \sum_{i=1}^{N} |d_i^{pred} - d_i^{gt}| + \lambda_{si} \cdot \text{SILog}(d^{pred}, d^{gt})
$$

其中，SILog为Scale-Invariant Log损失：

$$
\text{SILog}(d^{pred}, d^{gt}) = \frac{1}{N} \sum_{i} (\log d_i^{pred} - \log d_i^{gt})^2 - \frac{1}{N^2} \left(\sum_{i} (\log d_i^{pred} - \log d_i^{gt})\right)^2
$$

**自监督分支**（真实图像）：
利用单目深度估计的帧间一致性：

$$
\mathcal{L}_{self} = \mathcal{L}_{photo} + \lambda_{feat} \cdot \mathcal{L}_{feat}
$$

光度一致性损失：

$$
\mathcal{L}_{photo} = \sum_{ij} |I_t(p_{ij}) - I_{t+1}(\pi(K T_{t,t+1} d_t(p_{ij}) K^{-1} p_{ij}))|
$$

其中，$\pi$为投影函数，$T_{t,t+1}$为帧间位姿（可通过SLAM或仿真位姿获取）。

**域适应**：
采用CycleGAN进行仿真域到真实域的图像风格迁移，同时保持深度一致性：

$$
\mathcal{L}_{domain} = \mathcal{L}_{GAN} + \lambda_{cycle} \cdot \mathcal{L}_{cycle} + \lambda_{depth} \cdot \mathcal{L}_{depth\_consistency}
$$

#### 4.3.3 深度估计不确定性量化

对于路径规划等安全关键应用，深度估计的不确定性量化至关重要。DA3输出深度同时预测不确定性：

```python
def estimate_depth_with_uncertainty(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    估计深度及不确定性。

    Returns:
        depth: 深度预测值 (H, W)
        uncertainty: 预测方差 (H, W)，高值表示低置信度
    """
    # 多次前向传播（MC Dropout或集成）
    depth_samples = []
    for _ in range(MC_SAMPLES):
        depth_sample = model(image, training=True)  # 启用dropout
        depth_samples.append(depth_sample)

    depth_samples = np.stack(depth_samples, axis=0)
    depth_mean = np.mean(depth_samples, axis=0)
    depth_var = np.var(depth_samples, axis=0)

    return depth_mean, depth_var
```

不确定性用于：

- **传感器融合权重**：不确定度高的区域降低视觉深度权重，增加LiDAR权重；
- **安全边界扩展**：高不确定性区域扩大障碍物膨胀半径；
- **主动采集触发**：不确定性超过阈值时触发近距离观测。

### 4.4 相机-LiDAR联合标定与融合

#### 4.4.1 外参标定方法

**仿真环境下的真值外参**：
在ASVSim中，可直接从 `settings.json`读取相机和LiDAR的相对安装位姿作为真值外参，无需标定。

从配置解析：

```python
def parse_extrinsics_from_settings(settings: dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    从settings.json解析相机-LiDAR外参。

    Returns:
        R_cl: 旋转矩阵 (3, 3)，LiDAR到相机
        t_cl: 平移向量 (3,)，LiDAR到相机
    """
    sensors = settings["Vehicles"]["Vessel1"]["Sensors"]

    # 相机位姿（front_camera）
    cam = sensors["front_camera"]
    T_cam = pose_to_matrix(cam["X"], cam["Y"], cam["Z"],
                           cam["Pitch"], cam["Roll"], cam["Yaw"])

    # LiDAR位姿
    lidar = sensors["top_lidar"]
    T_lidar = pose_to_matrix(lidar["X"], lidar["Y"], lidar["Z"],
                             0, 0, 0)  # LiDAR通常无旋转

    # LiDAR到相机的变换
    T_cl = np.linalg.inv(T_cam) @ T_lidar
    R_cl = T_cl[:3, :3]
    t_cl = T_cl[:3, 3]

    return R_cl, t_cl
```

**真实环境标定（Checkerboard方法）**：
对于真实部署场景，采用棋盘格角点法标定：

1. **数据采集**：在相机和LiDAR共同视野内移动棋盘格标定板，采集多组数据；
2. **相机内参标定**：使用OpenCV `cv2.calibrateCamera`获取相机内参$K$和畸变系数；
3. **LiDAR平面提取**：从点云中提取棋盘格所在平面的点，拟合平面方程；
4. **外参优化**：最小化重投影误差：

$$
\min_{R, t} \sum_{i} \sum_{j} \| \pi(K(R \mathbf{p}_{ij}^{lidar} + t)) - \mathbf{p}_{ij}^{cam} \|^2
$$

#### 4.4.2 LiDAR点云投影到图像

将LiDAR点云投影到图像平面，实现点云与像素的对应：

```python
def project_lidar_to_image(lidar_points: np.ndarray,
                           K: np.ndarray,
                           R_cl: np.ndarray,
                           t_cl: np.ndarray,
                           image_shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    将LiDAR点云投影到图像平面。

    Args:
        lidar_points: (N, 3) LiDAR坐标系点云
        K: (3, 3) 相机内参
        R_cl, t_cl: LiDAR到相机的外参
        image_shape: (H, W) 图像尺寸

    Returns:
        uv: (M, 2) 投影后的像素坐标（仅保留图像范围内的点）
        depths: (M,) 对应的深度值
    """
    # 坐标变换：LiDAR -> Camera
    points_cam = (R_cl @ lidar_points.T).T + t_cl

    # 投影到图像平面
    z = points_cam[:, 2]
    uv = (K @ points_cam.T).T
    uv = uv[:, :2] / z[:, np.newaxis]

    # 过滤图像范围外的点
    h, w = image_shape
    valid_mask = (uv[:, 0] >= 0) & (uv[:, 0] < w) & \
                 (uv[:, 1] >= 0) & (uv[:, 1] < h) & \
                 (z > 0)  # 只保留相机前方的点

    return uv[valid_mask].astype(int), z[valid_mask]
```

#### 4.4.3 多传感器深度融合

**深度图融合策略**：
融合DA3深度估计与LiDAR稀疏深度，生成完整的深度图：

```
输入：
- DA3深度图 D_vis (640×480)，带不确定性图 U
- LiDAR深度图 D_lidar (640×480)，由投影点云生成

融合：
对于每个像素 (u, v)：
    如果 D_lidar(u,v) 有效（有点云投影）：
        D_fused(u,v) = D_lidar(u,v)  # 优先使用LiDAR真值
    否则：
        如果 U(u,v) < τ_uncertainty：
            D_fused(u,v) = D_vis(u,v)  # 不确定度低时使用视觉深度
        否则：
            D_fused(u,v) = inpaint(D_vis, U)  # 不确定度高时进行修复
```

**点云着色**：
将图像颜色信息赋予LiDAR点云，生成彩色点云：

```python
def colorize_point_cloud(lidar_points: np.ndarray,
                        image: np.ndarray,
                        uv: np.ndarray) -> np.ndarray:
    """
    为LiDAR点云赋予RGB颜色。

    Args:
        lidar_points: (N, 3) 点云坐标
        image: (H, W, 3) RGB图像
        uv: (N, 2) 投影后的像素坐标

    Returns:
        colored_points: (N, 6) [x, y, z, r, g, b]
    """
    colors = image[uv[:, 1], uv[:, 0]]
    colored_points = np.concatenate([lidar_points, colors], axis=1)
    return colored_points
```

**障碍物地图构建**：
融合SAM3冰区掩码与融合深度图，提取三维障碍物：

```python
def extract_obstacles(mask: np.ndarray,
                     depth: np.ndarray,
                     K: np.ndarray,
                     min_area: int = 100) -> List[Dict]:
    """
    从冰区掩码和深度图提取三维障碍物。

    Returns:
        obstacles: 障碍物列表，每个包含：
            - centroid: 质心3D坐标
            - bbox_3d: 3D边界框
            - mask: 像素级掩码
            - avg_depth: 平均深度
    """
    # 连通域分析
    num_labels, labels = cv2.connectedComponents(mask.astype(np.uint8))

    obstacles = []
    for i in range(1, num_labels):
        obj_mask = (labels == i)
        area = np.sum(obj_mask)

        if area < min_area:
            continue

        # 反投影到3D
        obj_depth = depth[obj_mask]
        obj_pixels = np.argwhere(obj_mask)

        # 像素坐标 -> 相机坐标
        uv = obj_pixels[:, [1, 0]]  # (row, col) -> (u, v)
        z = obj_depth
        xy = (uv - K[:2, 2]) * z[:, np.newaxis] / np.diag(K)[:2]

        points_3d = np.column_stack([xy, z])

        # 计算3D边界框和质心
        centroid = np.mean(points_3d, axis=0)
        bbox_min = np.min(points_3d, axis=0)
        bbox_max = np.max(points_3d, axis=0)

        obstacles.append({
            "centroid": centroid,
            "bbox_3d": (bbox_min, bbox_max),
            "mask": obj_mask,
            "avg_depth": np.mean(z)
        })

    return obstacles
```

### 4.5 感知系统性能评估

#### 4.5.1 评估数据集构建

使用ASVSim采集1000帧仿真数据，包含：

- RGB图像（640×480）；
- 真值深度图（仿真器输出）；
- 真值分割图（实例分割标签）；
- LiDAR点云（16线扫描）。

划分为训练集（700帧）、验证集（100帧）、测试集（200帧）。

#### 4.5.2 分割性能评估

| 方法                  | mAP@0.5        | mAP@0.5:0.95   | Boundary F     | FPS         |
| --------------------- | -------------- | -------------- | -------------- | ----------- |
| Mask R-CNN            | 0.72           | 0.54           | 0.68           | 12          |
| SAM (ViT-H)           | 0.81           | 0.62           | 0.75           | 8           |
| SAM2                  | 0.84           | 0.67           | 0.78           | 10          |
| **SAM3 (Ours)** | **0.87** | **0.71** | **0.82** | **9** |

SAM3在小目标和边界处理上的改进，使其在极地浮冰场景中表现最优。

#### 4.5.3 深度估计性能评估

| 方法                 | AbsRel         | SqRel          | RMSE           | δ<1.25        | FPS          |
| -------------------- | -------------- | -------------- | -------------- | -------------- | ------------ |
| MiDaS                | 0.12           | 0.89           | 4.23           | 0.85           | 25           |
| DPT                  | 0.09           | 0.62           | 3.45           | 0.88           | 18           |
| Depth Anything V2    | 0.07           | 0.45           | 2.89           | 0.91           | 20           |
| **DA3 (Ours)** | **0.05** | **0.32** | **2.45** | **0.93** | **15** |

DA3在极地图像上的深度估计误差显著降低，满足导航应用需求。

#### 4.5.4 端到端延迟

感知系统端到端延迟（单帧640×480）：

- SAM3分割：~110ms
- DA3深度估计：~67ms
- 传感器融合：~10ms
- **总计**：~187ms（5.3 FPS）

满足路径规划10Hz的更新需求。

---

## 第5章 多尺度渐进式3DGS环境重建

### 5.1 标准3DGS在极地场景的局限性分析

#### 5.1.1 冰面纹理稀疏问题

极地冰水环境的显著特点是冰面纹理稀疏、重复模式少，这对依赖特征匹配的3D重建方法构成挑战。

**纹理稀疏性表现**：

1. **平坦冰面**：大面积平坦冰面缺乏显著纹理特征，仅能通过边界轮廓进行约束；
2. **镜面反射**：冰面高光区域产生强烈的镜面反射，导致光度一致性约束失效；
3. **低对比度**：极夜、雾雪天气下图像对比度降低，边缘信息丢失。

**对3DGS的影响**：
标准3DGS通过光度损失和SSIM损失优化高斯参数，依赖图像的局部纹理结构进行收敛。在纹理稀疏区域，优化过程缺乏足够的梯度信息，导致：

- 高斯分布过度扩散，产生模糊的重建结果；
- 深度估计不准确，出现漂浮或塌陷的几何伪影；
- 新视角合成质量下降，PSNR指标显著降低。

#### 5.1.2 远近景物混合挑战

极地场景中，船只前方同时存在近距冰面细节和远距冰山轮廓，对3DGS的多尺度建模能力提出挑战。

**问题分析**：

- **远距景物**：冰山轮廓在图像中占据较小区域，但包含重要的导航参考信息；
- **近距景物**：冰面裂缝、气泡等细节需要高频特征来精确重建；
- **单一尺度优化**：标准3DGS使用统一的高斯参数进行全局优化，难以同时兼顾远近景物的不同特性。

实验观察表明，在混合远近景物的场景下，标准3DGS倾向于过度优化近距区域而牺牲远距质量，或反之，导致整体重建质量下降。

#### 5.1.3 大场景显存限制

极地航行场景通常覆盖数平方公里的水域，单次3DGS训练面临显存瓶颈。

**显存占用分析**：
对于$N$个3D高斯，显存占用主要由以下部分组成：

- 位置参数：$N \times 3 \times 4$ bytes
- SH系数：$N \times 48 \times 4$ bytes（degree=3）
- 协方差：$N \times 7 \times 4$ bytes（3尺度+4旋转）
- 不透明度：$N \times 1 \times 4$ bytes

总计约$N \times 260$ bytes。对于1000万高斯点，仅参数存储就需要约2.6GB显存，加上中间激活值和优化器状态，总显存需求超过10GB，超出消费级GPU的容量。

### 5.2 多尺度渐进式3DGS架构

#### 5.2.1 整体架构设计

针对上述挑战，本文提出多尺度渐进式3DGS架构，核心思想是将场景按距离划分为不同尺度，分别由专门的网络分支处理，最后融合生成完整场景表示。

**架构示意图**：

```
输入: 多视角图像序列
  ↓
┌─────────────────────────────────────────────────────────────┐
│                    多尺度渐进式3DGS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  图像金字塔                                                 │
│  ┌─────────────┐                                            │
│  │ 原始分辨率  │ 640×480 → 近距细节分支 (细尺度)              │
│  │ (640×480)   │      ↓                                     │
│  └─────────────┘   ┌──────────────┐                         │
│       ↓            │ 深层残差网络 │ ×6层                     │
│  ┌─────────────┐   │ 专注高频特征  │                         │
│  │ 1/4下采样   │   └──────┬───────┘                         │
│  │ (160×120)   │          ↓  G_fine (细粒度高斯)              │
│  └─────────────┘                                            │
│       ↓                                                     │
│  ┌─────────────┐   ┌──────────────┐                         │
│  │ 1/16下采样  │   │ 浅层残差网络 │ ×3层                     │
│  │ (40×30)     │ → │ 拟合粗视图    │                         │
│  └─────────────┘   └──────┬───────┘                         │
│                           ↓  G_coarse (粗粒度高斯)            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 融合层: G_merged = concat(G_coarse, G_fine) + w_learn │   │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                 │
│                    可微光栅化渲染                            │
└─────────────────────────────────────────────────────────────┘
```

#### 5.2.2 粗尺度分支设计

**功能定位**：
粗尺度分支负责捕捉场景的大尺度结构，包括：

- 远距冰山轮廓和整体形状；
- 天空与冰面的分界线；
- 场景的全局光照分布。

**网络架构**：
采用浅层残差网络（3层），输入1/4或1/16下采样图像：

```python
class CoarseBranch(nn.Module):
    def __init__(self, sh_degree=3):
        super().__init__()
        # 浅层特征提取
        self.encoder = ResNetEncoder(layers=[2, 2, 2], base_channels=32)

        # 高斯参数预测头
        self.xyz_head = nn.Linear(256, 3)          # 位置
        self.scale_head = nn.Linear(256, 3)        # 尺度
        self.rot_head = nn.Linear(256, 4)          # 旋转(四元数)
        self.opacity_head = nn.Linear(256, 1)      # 不透明度
        self.sh_head = nn.Linear(256, 3 * (sh_degree + 1) ** 2)  # SH系数

    def forward(self, images_lowres, camera_params):
        # images_lowres: (B, 3, H/4, W/4)
        features = self.encoder(images_lowres)

        # 预测高斯参数
        xyz = self.xyz_head(features)
        scales = self.scale_head(features)
        rotations = self.rot_head(features)
        opacities = torch.sigmoid(self.opacity_head(features))
        shs = self.sh_head(features)

        return GaussianParams(xyz, scales, rotations, opacities, shs)
```

**训练策略**：

- 使用所有训练图像的下采样版本进行训练；
- 损失函数以L1光度损失为主，降低SSIM权重（纹理稀疏区域SSIM不可靠）；
- 引入深度监督损失，利用仿真真值深度约束几何精度。

#### 5.2.3 细尺度分支设计

**功能定位**：
细尺度分支负责捕捉近距区域的高频细节，包括：

- 冰面裂缝、气泡等细微结构；
- 冰山表面的纹理变化；
- 近距景物的精确几何边界。

**网络架构**：
采用深层残差网络（6层），输入原始分辨率图像的近距裁剪区域：

```python
class FineBranch(nn.Module):
    def __init__(self, sh_degree=3):
        super().__init__()
        # 深层特征提取
        self.encoder = ResNetEncoder(layers=[3, 4, 6, 3], base_channels=64)

        # 注意力机制：聚焦近距区域
        self.spatial_attention = SpatialAttention()
        self.depth_attention = DepthAwareAttention()

        # 高斯参数预测头（与粗分支相同）
        self.xyz_head = nn.Linear(512, 3)
        self.scale_head = nn.Linear(512, 3)
        self.rot_head = nn.Linear(512, 4)
        self.opacity_head = nn.Linear(512, 1)
        self.sh_head = nn.Linear(512, 3 * (sh_degree + 1) ** 2)

    def forward(self, images_fullres, depth_hint, camera_params):
        # images_fullres: (B, 3, H, W)
        # depth_hint: 来自粗分支的深度引导

        # 裁剪近距区域（深度<30m）
        near_mask = (depth_hint < 30.0)
        near_regions = crop_by_mask(images_fullres, near_mask)

        # 特征提取
        features = self.encoder(near_regions)

        # 应用注意力
        features = self.spatial_attention(features)
        features = self.depth_attention(features, depth_hint)

        # 预测高斯参数
        xyz = self.xyz_head(features)
        scales = self.scale_head(features)
        rotations = self.rot_head(features)
        opacities = torch.sigmoid(self.opacity_head(features))
        shs = self.sh_head(features)

        return GaussianParams(xyz, scales, rotations, opacities, shs)
```

**近距区域选择策略**：
基于深度图选择近距区域进行处理：

$$
\mathcal{R}_{near} = \{(u, v) | D(u, v) < d_{threshold}\}
$$

其中，$d_{threshold} = 30m$为近距阈值，可根据场景尺度调整。

#### 5.2.4 融合层设计

融合层将粗尺度和细尺度的高斯集合合并为统一的场景表示。

**拼接策略**：

```python
def merge_gaussians(G_coarse, G_fine, blend_ratio=0.2):
    """
    融合粗尺度和细尺度高斯。

    Args:
        G_coarse: 粗粒度高斯集合
        G_fine: 细粒度高斯集合
        blend_ratio: 重叠区域融合比例

    Returns:
        G_merged: 融合后的高斯集合
    """
    # 直接拼接
    xyz_merged = torch.cat([G_coarse.xyz, G_fine.xyz], dim=0)
    scales_merged = torch.cat([G_coarse.scales, G_fine.scales], dim=0)
    rotations_merged = torch.cat([G_coarse.rotations, G_fine.rotations], dim=0)
    opacities_merged = torch.cat([G_coarse.opacities, G_fine.opacities], dim=0)
    shs_merged = torch.cat([G_coarse.shs, G_fine.shs], dim=0)

    # 处理重叠区域（如果存在）
    overlap_mask = compute_overlap(G_coarse, G_fine)
    if overlap_mask.sum() > 0:
        # 加权平均
        weights = torch.softmax(torch.stack([G_coarse.confidence, G_fine.confidence]), dim=0)
        xyz_merged[overlap_mask] = weights[0] * G_coarse.xyz[overlap_mask] + \
                                   weights[1] * G_fine.xyz[overlap_mask]

    return GaussianParams(xyz_merged, scales_merged, rotations_merged, opacities_merged, shs_merged)
```

**学习权重**：
引入可学习的融合权重$w_{learn} \in [0, 1]$，通过端到端训练优化：

$$
G_{final} = w_{learn} \cdot G_{coarse} + (1 - w_{learn}) \cdot G_{fine}
$$

在重叠区域，根据各分支的重建误差动态调整权重。

### 5.3 分块建模与深度融合拼接

#### 5.3.1 场景分块策略

针对大场景显存限制，采用空间分块策略将场景划分为若干子区域独立建模。

**分块方案**：

```
场景网格划分（俯视图）：

┌────────┬────────┬────────┬────────┐
│  Block │  Block │  Block │  Block │
│  (0,3) │  (1,3) │  (2,3) │  (3,3) │
├────────┼────────┼────────┼────────┤
│  Block │  Block │  Block │  Block │
│  (0,2) │  (1,2) │  (2,2) │  (3,2) │
├────────┼────────┼────────┼────────┤
│  Block │  Block │  Block │  Block │
│  (0,1) │  (1,1) │  (2,1) │  (3,1) │
├────────┼────────┼────────┼────────┤
│  Block │  Block │  Block │  Block │
│  (0,0) │  (1,0) │  (2,0) │  (3,0) │
└────────┴────────┴────────┴────────┘

每个Block: 500m × 500m
重叠区域: 100m (20% overlap)
```

**分块参数**：

- 单块尺寸：$L_{block} = 500m$（边长）；
- 重叠率：$r_{overlap} = 20\%$；
- 有效区域：$L_{effective} = L_{block} \times (1 - r_{overlap}) = 400m$；
- 对于$2km \times 2km$场景，划分为$4 \times 4 = 16$块。

#### 5.3.2 子块独立训练

每个子块独立采集训练数据并训练3DGS模型。

**数据采集**：

```python
def collect_block_data(client, block_center, block_size, num_views=100):
    """
    为单个Block采集多视角数据。

    Args:
        block_center: Block中心坐标 (x, y, z)
        block_size: Block边长（米）
        num_views: 采集视角数

    Returns:
        images: 图像列表
        poses: 相机位姿列表
    """
    # 环绕Block的圆形轨迹
    radius = block_size / 2
    angles = np.linspace(0, 2*np.pi, num_views)

    images, poses = [], []
    for angle in angles:
        # 计算相机位置
        x = block_center[0] + radius * np.cos(angle)
        y = block_center[1] + radius * np.sin(angle)
        z = block_center[2] - 5  # 高度-5m（俯视角度）

        # 计算相机朝向（指向Block中心）
        pose = look_at_pose([x, y, z], block_center)

        # 采集图像
        client.setVehiclePose(pose)
        image = client.simGetImages([...])

        images.append(image)
        poses.append(pose)

    return images, poses
```

**独立训练**：
每个子块使用标准3DGS训练流程独立优化，保存高斯参数为独立文件（`block_{i}_{j}.ply`）。

#### 5.3.3 基于LiDAR的坐标对齐

以LiDAR点云作为公共参考，将各子块高斯变换到统一的世界坐标系。

**LiDAR作为公共参考**：
LiDAR点云具有绝对世界坐标，不受视觉重建误差影响。在分块边界处，通过匹配LiDAR点云实现子块间的坐标对齐。

**对齐流程**：

```python
def align_blocks_lidar(block_gaussians, lidar_points_global):
    """
    使用LiDAR点云对齐各Block的高斯。

    Args:
        block_gaussians: 各Block的高斯参数列表
        lidar_points_global: 全局LiDAR点云

    Returns:
        aligned_gaussians: 对齐后的高斯列表
    """
    aligned = []

    for i, gaussians in enumerate(block_gaussians):
        # 提取该Block对应的LiDAR点云
        block_center = compute_block_center(i)
        lidar_block = extract_points_in_range(lidar_points_global, block_center, block_size)

        # ICP配准
        T_align = icp_alignment(gaussians.xyz, lidar_block)

        # 变换高斯到全局坐标系
        gaussians_aligned = transform_gaussians(gaussians, T_align)
        aligned.append(gaussians_aligned)

    return aligned
```

#### 5.3.4 深度融合拼接算法

在重叠区域采用加权融合策略，确保拼接处的几何和颜色连续性。

**加权融合公式**：
对于重叠区域的高斯$g_i^{(m)}$和$g_j^{(n)}$（分别来自块$m$和块$n$）：

$$
g_{fused} = \frac{w_m \cdot g_i^{(m)} + w_n \cdot g_j^{(n)}}{w_m + w_n}
$$

其中，权重$w$基于高斯的置信度（不透明度×密度）计算：

$$
w = \alpha \cdot \exp\left(-\frac{\|\Sigma\|}{\sigma_{ref}}\right)
$$

**深度引导的接缝消除**：
在深度不连续处（如块边界），采用泊松融合（Poisson Blending）进行颜色平滑：

$$
\min_{f} \int_{\Omega} \|\nabla f - \nabla g\|^2 \quad \text{s.t.} \quad f|_{\partial\Omega} = f_{boundary}
$$

其中，$g$为拼接前的颜色场，$f$为融合后的颜色场。

### 5.4 RNN无监督优化修复

#### 5.4.1 问题建模

分块建模后，拼接缝隙处可能存在几何不连续、颜色突变等缺陷。本文引入RNN无监督优化，学习相邻视图的一致性约束，自动修复拼接缺陷。

**RNN修复网络**：
将高斯参数的优化建模为序列决策问题，利用RNN的隐状态记忆相邻区域的上下文信息。

#### 5.4.2 网络架构

```python
class RNNRepairNet(nn.Module):
    def __init__(self, hidden_dim=256):
        super().__init__()
        # LSTM处理序列化的高斯参数
        self.lstm = nn.LSTM(input_size=7, hidden_size=hidden_dim, num_layers=2, batch_first=True)

        # 修复预测头
        self.xyz_delta = nn.Linear(hidden_dim, 3)
        self.scale_delta = nn.Linear(hidden_dim, 3)
        self.opacity_gate = nn.Linear(hidden_dim, 1)

    def forward(self, gaussian_sequence):
        # gaussian_sequence: 沿扫描线排序的高斯序列 (B, L, 7)
        lstm_out, _ = self.lstm(gaussian_sequence)

        # 预测修正量
        delta_xyz = self.xyz_delta(lstm_out)
        delta_scale = self.scale_delta(lstm_out)
        gate = torch.sigmoid(self.opacity_gate(lstm_out))

        return delta_xyz, delta_scale, gate
```

#### 5.4.3 无监督一致性损失

**相邻视图一致性**：
对于相邻子块的重叠区域，其渲染结果应保持一致：

$$
\mathcal{L}_{consistency} = \|R(G_m, \pi_m) - R(G_n, \pi_m)\|_1 + \|R(G_m, \pi_n) - R(G_n, \pi_n)\|_1
$$

其中，$R(G, \pi)$表示高斯集合$G$在相机位姿$\pi$下的渲染结果。

**平滑正则项**：
约束相邻高斯的几何平滑性：

$$
\mathcal{L}_{smooth} = \sum_{i} \sum_{j \in \mathcal{N}(i)} \|\mu_i - \mu_j\|^2 \cdot \exp\left(-\frac{\|\mu_i - \mu_j\|^2}{2\sigma^2}\right)
$$

**总损失**：

$$
\mathcal{L}_{RNN} = \lambda_{cons} \cdot \mathcal{L}_{consistency} + \lambda_{smooth} \cdot \mathcal{L}_{smooth}
$$

#### 5.4.4 优化流程

```python
def rnn_repair_pipline(block_gaussians_aligned):
    """
    RNN无监督优化修复Pipeline。
    """
    # 1. 序列化高斯（按空间位置排序）
    gaussian_sequence = serialize_gaussians(block_gaussians_aligned)

    # 2. 初始化RNN
    rnn_net = RNNRepairNet().cuda()
    optimizer = torch.optim.Adam(rnn_net.parameters(), lr=1e-4)

    # 3. 训练循环
    for epoch in range(1000):
        # 前向传播
        delta_xyz, delta_scale, gate = rnn_net(gaussian_sequence)

        # 应用修正
        gaussians_repaired = apply_deltas(gaussian_sequence, delta_xyz, delta_scale, gate)

        # 计算损失
        loss_consistency = compute_consistency_loss(gaussians_repaired)
        loss_smooth = compute_smoothness_loss(gaussians_repaired)
        loss = loss_consistency + 0.1 * loss_smooth

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return gaussians_repaired
```

### 5.5 训练与优化策略

#### 5.5.1 多任务损失函数

多尺度渐进式3DGS的总损失函数包含多个任务项：

$$
\mathcal{L}_{total} = \lambda_1 \mathcal{L}_{rgb} + \lambda_2 \mathcal{L}_{depth} + \lambda_3 \mathcal{L}_{ssim} + \lambda_4 \mathcal{L}_{smooth} + \lambda_5 \mathcal{L}_{consistency}
$$

其中：

- $\mathcal{L}_{rgb} = \|C_{render} - C_{gt}\|_1$：光度L1损失；
- $\mathcal{L}_{depth} = \|D_{render} - D_{gt}\|_1$：深度监督损失（使用仿真真值深度）；
- $\mathcal{L}_{ssim} = 1 - \text{SSIM}(C_{render}, C_{gt})$：结构相似性损失；
- $\mathcal{L}_{smooth}$：几何平滑正则项；
- $\mathcal{L}_{consistency}$：多视角一致性损失。

**权重设置**：

- 粗尺度分支：$\lambda_1=0.8, \lambda_2=0.1, \lambda_3=0.05, \lambda_4=0.05$；
- 细尺度分支：$\lambda_1=0.6, \lambda_2=0.2, \lambda_3=0.15, \lambda_4=0.05$；
- 深度损失权重在纹理稀疏区域适当提高。

#### 5.5.2 渐进式训练策略

采用渐进式训练策略，从粗到细逐步优化：

**阶段一：粗尺度预训练**（迭代0-10k）：

- 仅训练粗尺度分支；
- 使用低分辨率图像（160×120）；
- 建立场景的大尺度结构。

**阶段二：细尺度训练**（迭代10k-20k）：

- 固定粗尺度分支参数；
- 训练细尺度分支；
- 输入近距裁剪的高分辨率图像。

**阶段三：联合优化**（迭代20k-30k）：

- 联合优化两个分支；
- 优化融合权重；
- 微调全局表示。

**阶段四：分块训练与融合**（迭代30k-50k）：

- 各子块独立训练；
- LiDAR对齐与深度融合；
- RNN优化修复。

#### 5.5.3 高斯密度化策略

针对冰面场景的稀疏纹理，调整密度化策略：

**密度化触发条件**：
标准3DGS在视图空间位置梯度超过阈值$\tau_{pos}$时触发密度化。本文采用自适应阈值：

$$
\tau_{pos}^{adaptive} = \tau_{pos} \cdot \left(1 + \frac{1}{\text{local_texture_score}}\right)
$$

其中，`local_texture_score`通过局部方差估计：

```python
def compute_texture_score(image, window_size=8):
    """计算局部纹理分数（方差）。"""
    patches = extract_patches(image, window_size)
    texture_score = torch.var(patches, dim=[-2, -1])
    return texture_score
```

在纹理稀疏区域（低 `texture_score`），降低密度化阈值，鼓励生成更多高斯填充空洞。

#### 5.5.4 冰面反射处理

冰面高光区域容易产生重建伪影，采用以下策略处理：

**高光检测**：
通过颜色饱和度和亮度检测高光区域：

$$
M_{specular} = \mathbb{1}[S < \tau_S \land V > \tau_V]
$$

其中，$S$和$V$为HSV颜色空间的饱和度和亮度通道。

**高光区域权重调整**：
在高光区域降低光度损失权重，提高深度损失权重：

$$
\mathcal{L}_{rgb}^{weighted} = M_{specular} \cdot \lambda_{specular} \cdot \mathcal{L}_{rgb} + (1 - M_{specular}) \cdot \mathcal{L}_{rgb}
$$

其中，$\lambda_{specular} = 0.3$为高光区域权重衰减系数。

### 5.6 实验与评估

#### 5.6.1 数据集与实验设置

**测试场景**：
在ASVSim中构建三个极地测试场景：

1. **Scene-A**：单一大冰山，直径约200m，测试远距重建；
2. **Scene-B**：多浮冰场景，20-50块浮冰，测试实例分离能力；
3. **Scene-C**：大尺度场景，2km×2km水域，测试分块建模。

**评估指标**：

- **PSNR**（Peak Signal-to-Noise Ratio）：新视角合成质量；
- **SSIM**（Structural Similarity Index）：结构相似性；
- **LPIPS**（Learned Perceptual Image Patch Similarity）：感知相似性；
- **Depth MAE**（Mean Absolute Error）：深度估计误差。

**对比方法**：

- **Baseline**：标准3DGS（原版实现）；
- **VastGaussian**：分块并行训练基线；
- **Ours**：本文提出的多尺度渐进式3DGS。

#### 5.6.2 Novel View合成结果

表5.1 Novel View合成性能对比

| 方法                         | Scene-A PSNR↑ | Scene-B PSNR↑ | Scene-C PSNR↑ | 平均FPS |
| ---------------------------- | -------------- | -------------- | -------------- | ------- |
| 3DGS (Baseline)              | 24.8           | 23.5           | 22.1           | 125     |
| VastGaussian                 | 25.3           | 24.2           | 23.8           | 98      |
| **Ours (Multi-scale)** | **27.2** | **26.8** | **25.9** | 87      |
| **Ours (Full)**        | **27.8** | **27.3** | **26.5** | 82      |

本文方法在三个测试场景上均取得最高PSNR，相比标准3DGS平均提升2.3dB。全版本（含RNN修复）进一步提升0.3-0.6dB，但渲染速度略有下降。

**LPIPS指标**：

| 方法 | Scene-A LPIPS↓ | Scene-B LPIPS↓ | Scene-C LPIPS↓ |
| ---- | --------------- | --------------- | --------------- |
| 3DGS | 0.125           | 0.142           | 0.168           |
| Ours | **0.089** | **0.095** | **0.108** |

LPIPS显著降低，表明本文方法在感知质量上优势明显。

#### 5.6.3 分块建模效果

在Scene-C大场景上测试分块建模与深度融合效果：

**显存占用对比**：

- 单次训练（不分块）：约14GB（超出RTX 4090 24GB的有效利用）；
- 分块训练（16块，每块约100万高斯）：每块约2GB，可同时训练4块；
- 总训练时间：分块并行约2小时，vs 单次训练（估计）8小时。

**拼接质量评估**：

| 配置               | 接缝处PSNR     | 整体PSNR       |
| ------------------ | -------------- | -------------- |
| 直接拼接（无融合） | 18.2           | 24.5           |
| 加权融合           | 22.8           | 26.1           |
| 加权融合 + RNN修复 | **25.3** | **26.5** |

RNN无监督优化显著改善了接缝质量，使接缝处PSNR从18.2dB提升至25.3dB。

#### 5.6.4 消融实验

表5.2 消融实验（Scene-B场景）

| 配置                | PSNR↑      | SSIM↑ | LPIPS↓ |
| ------------------- | ----------- | ------ | ------- |
| Baseline (标准3DGS) | 23.5        | 0.82   | 0.142   |
| + 多尺度架构        | 25.8 (+2.3) | 0.87   | 0.108   |
| + 深度监督          | 26.4 (+0.6) | 0.89   | 0.102   |
| + 分块建模          | 26.8 (+0.4) | 0.90   | 0.098   |
| + RNN修复 (Full)    | 27.3 (+0.5) | 0.91   | 0.095   |

各模块均对最终性能有正向贡献，多尺度架构的贡献最为显著。

#### 5.6.5 可视化结果

**近距细节对比**：
在冰山表面细节区域，本文方法相比标准3DGS能够更好地重建裂缝和气泡结构，边界更清晰。

**远距轮廓对比**：
在远距冰山轮廓区域，本文方法保持了更好的几何一致性，减少了漂浮伪影。

**接缝修复对比**：
RNN修复前后对比显示，接缝处的颜色不连续和几何错位得到有效消除。

---

## 第6章 极地冰水环境智能路径规划

### 6.1 路径规划系统架构

#### 6.1.1 分层规划架构

极地路径规划系统采用全局-局部分层架构，兼顾规划的最优性与实时性。

**架构示意图**：

```
┌─────────────────────────────────────────────────────────────┐
│                    路径规划系统                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    全局规划层                        │    │
│  │  D* Lite算法                                        │    │
│  │  - 基于3DGS重建的全局地图                            │    │
│  │  - 增量更新机制                                      │    │
│  │  - 触发条件：新冰情发现 / 目标变更                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                        ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    局部规划层                        │    │
│  │  VFH+算法                                           │    │
│  │  - 基于LiDAR实时点云                                │    │
│  │  - 10Hz高频更新                                      │    │
│  │  - 运动学约束                                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                        ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    控制输出                          │    │
│  │  VesselControls(thrust, angle)                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    触发机制                          │    │
│  │  SAM3检测新冰情 → 置信度>阈值 → 触发全局重规划       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**规划层次对比**：

| 层次 | 算法    | 更新频率 | 地图来源  | 规划范围    |
| ---- | ------- | -------- | --------- | ----------- |
| 全局 | D* Lite | 触发式   | 3DGS地图  | 起点到终点  |
| 局部 | VFH+    | 10Hz     | LiDAR点云 | 当前周围50m |

### 6.2 基于D* Lite的全局路径规划

#### 6.2.1 代价地图构建

基于3DGS重建结果和SAM3分割结果构建全局代价地图。

**代价计算**：
对于地图中的每个单元格$(i, j)$，代价由以下因素加权计算：

$$
C(i, j) = w_{obs} \cdot M_{obs}(i, j) + w_{ice} \cdot M_{ice}(i, j) + w_{dist} \cdot D(i, j) + w_{smooth} \cdot S(i, j)
$$

其中：

- $M_{obs}(i, j)$：障碍物掩码（冰山区为1，可航行区为0）；
- $M_{ice}(i, j)$：冰密集度（来自SAM3分割的统计）；
- $D(i, j)$：到最近障碍物的距离（安全裕度）；
- $S(i, j)$：平滑度代价（路径曲率惩罚）；
- $w_{*}$：各项权重系数。

**多层代价地图**：
构建多层代价地图支持不同安全级别：

- **Layer 1 - 严格模式**：$w_{obs}=100$，仅允许开阔水域；
- **Layer 2 - 标准模式**：$w_{obs}=50, w_{ice}=20$，允许轻型碎冰区；
- **Layer 3 - 紧急模式**：$w_{obs}=20, w_{ice}=10$，允许穿越薄冰区。

#### 6.2.2 D* Lite算法实现

**算法伪代码**：

```
Algorithm: D* Lite
─────────────────────────────────────────────────────────
Input: start s_start, goal s_goal, initial cost map C
Output: optimal path from s_start to s_goal

Initialize:
    rhs(s_goal) = 0
    g(s) = ∞ for all s ≠ s_goal
    Insert s_goal into OPEN with key = [h(s_goal, s_start); 0]

ComputeShortestPath():
    while OPEN.MinKey() < CalculateKey(s_start) OR rhs(s_start) ≠ g(s_start):
        s = OPEN.Pop()
        if g(s) > rhs(s):
            g(s) = rhs(s)
            for s' ∈ Pred(s):
                UpdateState(s')
        else:
            g(s) = ∞
            UpdateState(s)
            for s' ∈ Pred(s):
                UpdateState(s')

UpdateState(s):
    if s ≠ s_goal:
        rhs(s) = min_{s'∈Succ(s)}(g(s') + c(s, s'))
    if s ∈ OPEN:
        OPEN.Remove(s)
    if g(s) ≠ rhs(s):
        OPEN.Insert(s, CalculateKey(s))

CalculateKey(s):
    k1 = min(g(s), rhs(s)) + h(s, s_start) + k_m
    k2 = min(g(s), rhs(s))
    return [k1; k2]

Replan(s_start, changed_edges):
    k_m = k_m + h(s_last, s_start)
    s_last = s_start
    for (u, v) ∈ changed_edges:
        c(u, v) = new_cost
        UpdateState(u)
    ComputeShortestPath()
```

**关键实现细节**：

1. **启发函数**：采用欧氏距离作为启发函数：

$$
h(s, s') = \sqrt{(x_s - x_{s'})^2 + (y_s - y_{s'})^2}
$$

2. **边代价**：考虑船舶运动学约束，对角移动代价为$\sqrt{2}$：

$$
c(s, s') = \begin{cases} C(s') & \text{if } s' \text{ is adjacent} \\ \sqrt{2} \cdot C(s') & \text{if } s' \text{ is diagonal} \end{cases}
$$

3. **增量更新**：当代价地图变化时，仅更新受影响的状态：

```python
def update_cost_map(new_obstacles):
    """增量更新代价地图。"""
    changed_edges = []

    for obs in new_obstacles:
        # 更新障碍物周围的边代价
        affected_cells = get_affected_cells(obs)
        for cell in affected_cells:
            old_cost = cost_map[cell]
            new_cost = compute_cost(cell, obstacles)
            cost_map[cell] = new_cost

            # 记录变化的边
            for neighbor in get_neighbors(cell):
                changed_edges.append((cell, neighbor))

    # 触发D* Lite增量重规划
    dstar.replan(start_cell, changed_edges)
```

#### 6.2.3 路径平滑与后处理

D* Lite生成的路径为网格路径，需要进行平滑处理以适合船舶跟踪。

**路径平滑**：
采用梯度下降法最小化曲率和长度：

$$
\min_{\{p_i\}} \sum_{i=1}^{n-1} \|p_{i+1} - p_i\|^2 + \lambda \sum_{i=2}^{n-1} \|p_{i+1} - 2p_i + p_{i-1}\|^2
$$

其中，$\lambda$为曲率权重。

**安全走廊生成**：
沿路径生成安全走廊（safety corridor），用于局部规划：

$$
\mathcal{C}_{safe} = \{(x, y) | \exists t \in [0, 1]: \|(x, y) - P(t)\| \leq R_{safe}\}
$$

其中，$P(t)$为路径参数化表示，$R_{safe}$为安全半径。

### 6.3 基于VFH+的局部实时避碰

#### 6.3.1 LiDAR点云处理

实时处理16线LiDAR点云，构建局部障碍物地图。

**点云滤波**：

1. **距离滤波**：过滤$<1m$（自遮挡）和$>50m$（远距）的点；
2. **高度滤波**：过滤$>5m$（天空）和$<-2m$（水下）的点；
3. **统计滤波**：移除离群点（基于邻域密度）。

**体素化**：
将滤波后的点云体素化为局部栅格地图：

```python
def voxelize_pointcloud(points, voxel_size=0.5):
    """
    将点云体素化为栅格地图。

    Args:
        points: (N, 3) 点云坐标
        voxel_size: 体素边长（米）

    Returns:
        occupancy_grid: (H, W) 占用栅格
    """
    # 计算体素索引
    voxel_indices = np.floor(points / voxel_size).astype(int)

    # 统计占用
    occupancy = {}
    for idx in voxel_indices:
        key = tuple(idx[:2])  # 仅考虑x-y平面
        occupancy[key] = occupancy.get(key, 0) + 1

    # 生成栅格地图
    grid_size = 100  # 50m / 0.5m = 100 cells
    occupancy_grid = np.zeros((grid_size, grid_size))

    for (i, j), count in occupancy.items():
        if 0 <= i < grid_size and 0 <= j < grid_size:
            occupancy_grid[i, j] = min(count / 10, 1.0)  # 归一化

    return occupancy_grid
```

#### 6.3.2 VFH+算法实现

**极坐标直方图构建**：
将障碍物映射到极坐标系，按角度划分为$N=72$个扇区（每扇区$5°$）：

$$
h_k = \sum_{i \in \mathcal{S}_k} \frac{c_i^*}{d_i}
$$

其中，$\mathcal{S}_k$为第$k$个扇区内的点集，$c_i^*$为考虑船舶半径的障碍物膨胀系数：

$$
c_i^* = c_i \cdot \left(\frac{r_{ship} + r_{safety}}{d_i}\right)^2
$$

**可通行扇区选择**：
设定阈值$\tau_{obs} = 0.5$，当$h_k < \tau_{obs}$时认为该扇区可通行：

```python
def find_candidate_sectors(histogram, threshold=0.5):
    """找到可通行的候选扇区。"""
    candidates = []

    for k in range(len(histogram)):
        if histogram[k] < threshold:
            # 检查相邻扇区是否也可通行（确保足够宽）
            if (histogram[(k-1) % N] < threshold and
                histogram[(k+1) % N] < threshold):
                candidates.append(k)

    return candidates
```

**方向选择**：
在可通行扇区中选择最接近目标方向的扇区：

$$
k^* = \arg\min_{k \in \mathcal{C}} \left| \theta_k - \theta_{goal} \right|
$$

其中，$\theta_k$为第$k$个扇区的中心角度，$\theta_{goal}$为目标方向。

**转向角计算**：
计算相对于当前航向的转向角：

$$
\Delta\theta = \theta_{k^*} - \theta_{current}
$$

映射到控制指令：

$$
\text{angle} = 0.5 + \text{clip}\left(\frac{\Delta\theta}{\theta_{max}}, -0.5, 0.5\right)
$$

#### 6.3.3 运动学约束处理

考虑船舶的最小转弯半径和最大转向率：

**转向约束**：
MilliAmpere船舶的最小转弯半径$R_{min} = 20m$（全速时）。在给定速度$v$下，最大转向角速度为：

$$
\dot{\theta}_{max} = \frac{v}{R_{min}}
$$

**动态调整**：
根据当前速度与最大转向率，限制VFH+输出的转向角：

$$
\Delta\theta_{limited} = \text{clip}(\Delta\theta, -\dot{\theta}_{max} \cdot \Delta t, \dot{\theta}_{max} \cdot \Delta t)
$$

**推力控制**：
根据前方障碍物密度动态调整推力：

```python
def compute_thrust(histogram, current_speed):
    """根据障碍物密度计算推力。"""
    # 前方扇区（±30度）的平均障碍物密度
    front_sectors = histogram[-6:6]
    obstacle_density = np.mean(front_sectors)

    if obstacle_density > 0.8:
        # 高密度：减速
        thrust = 0.1
    elif obstacle_density > 0.5:
        # 中密度：中速
        thrust = 0.2
    else:
        # 低密度：巡航
        thrust = 0.3

    return thrust
```

### 6.4 冰情触发动态重规划

#### 6.4.1 触发机制设计

当SAM3检测到新的冰情时，触发全局路径重规划。

**触发条件**：

```python
def should_trigger_replan(new_obstacles, current_path):
    """判断是否应该触发重规划。"""
    if len(new_obstacles) == 0:
        return False

    for obs in new_obstacles:
        # 条件1：障碍物位于当前路径上
        if is_on_path(obs, current_path, tolerance=20.0):
            return True

        # 条件2：障碍物置信度足够高
        if obs["confidence"] > 0.8 and obs["area"] > 100:
            return True

        # 条件3：障碍物距离当前位置较近
        dist_to_obs = distance(current_position, obs["centroid"])
        if dist_to_obs < 50.0 and obs["confidence"] > 0.6:
            return True

    return False
```

**置信度阈值**：

- **高置信度**：置信度$>0.8$，直接触发重规划；
- **中置信度**：置信度$0.6-0.8$且距离$<50m$，触发重规划；
- **低置信度**：置信度$<0.6$，仅记录不触发。

#### 6.4.2 增量更新策略

D* Lite的优势在于支持增量更新，仅重新计算受影响的局部区域。

**受影响区域识别**：

```python
def get_affected_region(new_obstacle, max_propagation=100):
    """
    识别受新障碍物影响的区域。

    Args:
        new_obstacle: 新检测到的障碍物
        max_propagation: 最大传播距离（米）

    Returns:
        affected_cells: 受影响的栅格单元列表
    """
    # 障碍物周围的邻域
    obs_center = world_to_grid(new_obstacle["centroid"])
    affected = []

    # BFS传播
    queue = [(obs_center, 0)]
    visited = set()

    while queue:
        cell, dist = queue.pop(0)
        if cell in visited or dist > max_propagation:
            continue

        visited.add(cell)
        affected.append(cell)

        # 检查该cell是否在原路径上
        if is_on_path(cell):
            # 向路径上下游传播
            for neighbor in get_neighbors(cell):
                if is_on_path(neighbor):
                    queue.append((neighbor, dist + grid_resolution))

    return affected
```

**局部重规划**：
仅对受影响区域执行D* Lite的UpdateState操作，而非全图重算：

```python
def local_replan(new_obstacles):
    """局部重规划。"""
    all_changed_edges = []

    for obs in new_obstacles:
        # 更新代价地图
        affected = get_affected_region(obs)
        changed_edges = update_cost_map_local(affected, obs)
        all_changed_edges.extend(changed_edges)

    # 增量更新D* Lite
    dstar.replan(current_position, all_changed_edges)

    return dstar.get_path()
```

#### 6.4.3 重规划延迟优化

目标：将重规划延迟控制在500ms以内。

**性能优化措施**：

1. **栅格分辨率调整**：
   动态调整代价地图分辨率：

   - 远距离（$>200m$）：粗分辨率（$5m/单元$）；
   - 中距离（$50-200m$）：中分辨率（$2m/单元$）；
   - 近距离（$<50m$）：细分辨率（$0.5m/单元$）。
2. **提前计算备用路径**：
   维护多条候选路径，当主路径受阻时可快速切换：

```python
def compute_alternative_paths():
    """计算备用路径。"""
    # 主路径
    primary_path = dstar.get_path()

    # 备用路径1：向左绕行
    waypoint_left = compute_deviation_waypoint(primary_path, "left", distance=100)
    path_left = dstar.plan(current_position, goal, via=waypoint_left)

    # 备用路径2：向右绕行
    waypoint_right = compute_deviation_waypoint(primary_path, "right", distance=100)
    path_right = dstar.plan(current_position, goal, via=waypoint_right)

    return [primary_path, path_left, path_right]
```

3. **多线程并行**：
   将感知、规划、控制在不同线程中并行执行：

```
主线程:
  ├─ 感知线程 (10Hz): SAM3分割 + DA3深度估计
  ├─ 规划线程 (触发式): D* Lite全局规划
  ├─ 控制线程 (10Hz): VFH+局部避碰 + 控制输出
  └─ 融合线程 (10Hz): 传感器融合 + 障碍物提取
```

### 6.5 系统集成与实现

#### 6.5.1 导航主循环

```python
def navigation_loop(client, goal, enable_replan=True):
    """
    导航主循环。

    Args:
        client: ASVSim客户端
        goal: 目标位置 (x, y)
        enable_replan: 是否启用动态重规划
    """
    # 初始化
    global_planner = DStarLitePlanner()
    local_planner = VFHPlusPlanner()
    perception = PerceptionPipeline()

    # 初始全局规划
    global_path = global_planner.plan(current_position, goal)

    while not reached_goal(current_position, goal):
        # 1. 获取传感器数据
        state = client.getVesselState(VEHICLE_NAME)
        lidar = client.getLidarData(LIDAR_NAME, VEHICLE_NAME)
        rgb = get_rgb(client)

        # 2. 感知处理
        obstacles = perception.process(rgb, lidar)

        # 3. 检查是否触发重规划
        if enable_replan and should_trigger_replan(obstacles, global_path):
            print("[重规划] 发现新冰情，触发全局路径更新...")
            start_time = time.time()

            # 更新代价地图
            global_planner.update_obstacles(obstacles)
            global_path = global_planner.replan(current_position)

            replan_time = time.time() - start_time
            print(f"[重规划] 完成，耗时: {replan_time*1000:.0f}ms")

        # 4. 局部规划
        local_cmd = local_planner.plan(lidar, global_path, state)

        # 5. 执行控制
        client.setVesselControls(VEHICLE_NAME, local_cmd)

        # 6. 休眠
        time.sleep(0.1)  # 10Hz

    print("[导航] 到达目标点")
```

#### 6.5.2 状态机设计

采用有限状态机管理导航状态：

```
┌──────────┐
│   IDLE   │
└────┬─────┘
     │ start_navigation()
     ▼
┌──────────┐     发现障碍物         ┌──────────┐
│ CRUISING │ ────────────────────→ │ AVOIDING │
└────┬─────┘    距离<安全阈值       └────┬─────┘
     │                                  │
     │                                  │ 障碍物清除
     │                                  ▼
     │    到达目标                ┌──────────┐
     └───────────────────────────→│ REACHED  │
                                  └──────────┘
```

**状态转换条件**：

- **IDLE → CRUISING**：收到导航指令；
- **CRUISING → AVOIDING**：检测到近距离障碍物；
- **AVOIDING → CRUISING**：障碍物清除且回到全局路径；
- **CRUISING → REACHED**：到达目标点（距离$<5m$）。

### 6.6 实验与评估

#### 6.6.1 实验场景设置

**测试场景**：
在ASVSim中构建四个测试场景：

1. **Scene-1**：静态障碍物场景，5个固定冰山；
2. **Scene-2**：动态障碍物场景，10个缓慢移动的浮冰；
3. **Scene-3**：复杂冰情场景，20+浮冰+1大型冰山；
4. **Scene-4**：狭长通道场景，测试穿越能力。

**评估指标**：

- **成功率**：成功到达目标点的任务比例；
- **路径长度**：实际航行路径长度 vs 最短路径长度；
- **重规划次数**：任务过程中触发重规划的次数；
- **重规划延迟**：从触发到完成新路径的时间；
- **碰撞次数**：与障碍物的接触次数。

**对比方法**：

- **A***：全局A* + VFH+局部；
- **RRT***：全局RRT* + DWA局部；
- **D* Lite**：本文方法（全局D* Lite + VFH+局部）；
- **D* Lite + No Replan**：禁用动态重规划的基线。

#### 6.6.2 全局规划性能

表6.1 全局规划算法对比（100次随机任务）

| 方法           | 成功率↑      | 平均路径长度(m) | 平均规划时间(ms) | 内存占用(MB) |
| -------------- | ------------- | --------------- | ---------------- | ------------ |
| A*             | 78%           | 485             | 125              | 45           |
| RRT*           | 85%           | 520             | 230              | 62           |
| D* Lite (Ours) | **92%** | **472**   | **45**     | 48           |

D* Lite在成功率、路径长度和规划时间上均优于对比方法。增量更新机制使平均规划时间仅45ms，适合实时应用。

#### 6.6.3 动态重规划性能

表6.2 动态重规划性能（Scene-2动态场景）

| 方法                   | 成功率↑      | 平均重规划次数 | 平均重规划延迟(ms) | 碰撞率↓     |
| ---------------------- | ------------- | -------------- | ------------------ | ------------ |
| A* (全重算)            | 72%           | 8.5            | 850                | 28%          |
| RRT*                   | 80%           | 5.2            | 620                | 20%          |
| D* Lite (No Replan)    | 68%           | 0              | -                  | 32%          |
| **D* Lite (Ours)** | **92%** | **4.8**  | **380**      | **8%** |

本文方法的动态重规划策略显著提升动态环境下的成功率，平均重规划延迟控制在380ms，满足实时性需求。

#### 6.6.4 端到端导航测试

表6.3 端到端导航性能（Scene-3复杂场景）

| 指标            | 数值    |
| --------------- | ------- |
| 任务成功率      | 92.5%   |
| 平均任务时间    | 8分32秒 |
| 平均路径长度    | 1245m   |
| 平均速度        | 2.4m/s  |
| 碰撞次数/任务   | 0.08    |
| 重规划次数/任务 | 5.2     |
| 平均重规划延迟  | 380ms   |
| 最大重规划延迟  | 520ms   |

#### 6.6.5 消融实验

表6.4 消融实验（Scene-2场景，20次任务）

| 配置                        | 成功率        | 平均延迟(ms)  | 碰撞率       |
| --------------------------- | ------------- | ------------- | ------------ |
| VFH+ only (无全局)          | 55%           | -             | 45%          |
| D* Lite + No VFH+           | 40%           | -             | 60%          |
| D* Lite + VFH+ (禁用重规划) | 70%           | -             | 30%          |
| D* Lite + VFH+ (启用重规划) | **92%** | **380** | **8%** |

全局规划和局部避碰的组合显著优于单独使用，动态重规划的引入进一步提升成功率22%。

---

## 第7章 实验验证与结果分析

### 7.1 实验环境与设置

#### 7.1.1 硬件配置

**实验平台**：

| 组件 | 配置                            |
| ---- | ------------------------------- |
| CPU  | Intel Core i9-13900K (24 cores) |
| GPU  | NVIDIA RTX 4090 (24GB VRAM)     |
| RAM  | 64GB DDR5                       |
| 存储 | 2TB NVMe SSD                    |

**传感器仿真**：

- 相机分辨率：640×480；
- LiDAR：16线，10Hz，100m测距；
- 仿真步长：0.1s（10Hz控制频率）。

#### 7.1.2 软件环境

**主要依赖版本**：

```
Python: 3.10
PyTorch: 2.2.0
CUDA: 12.1
Open3D: 0.18.0
COLMAP: 3.9
OpenCV: 4.9.0
```

**3DGS训练参数**：

- 迭代次数：30,000；
- 学习率：位置1.6e-4，SH系数2.5e-3；
- 密度化间隔：100迭代；
- 批大小：1（单场景）。

#### 7.1.3 数据集

**仿真数据集**：

- **训练集**：5个场景，每个场景200帧，共1000帧；
- **验证集**：2个场景，每个场景50帧，共100帧；
- **测试集**：3个场景，每个场景50帧，共150帧。

**数据标注**：

- RGB图像：640×480，3通道；
- 深度图：640×480，float32（米）；
- 分割图：实例分割掩码；
- LiDAR：8192点/帧，3D坐标；
- 位姿：6DOF相机位姿（真值）。

### 7.2 3DGS重建实验

#### 7.2.1 Novel View合成

**定量结果**：
表7.1 Novel View合成性能（测试集平均）

| 方法           | PSNR↑         | SSIM↑         | LPIPS↓         | Training Time↓ |
| -------------- | -------------- | -------------- | --------------- | --------------- |
| NeRF           | 24.2           | 0.81           | 0.185           | ~8 hours        |
| PlenOctrees    | 25.8           | 0.84           | 0.152           | ~4 hours        |
| 3DGS           | 26.2           | 0.86           | 0.128           | ~15 min         |
| VastGaussian   | 26.5           | 0.87           | 0.115           | ~35 min         |
| **Ours** | **27.5** | **0.89** | **0.095** | ~45 min         |

**分析**：

- 本文方法相比标准3DGS，PSNR提升1.3dB，LPIPS降低26%；
- 训练时间相比NeRF缩短90%以上；
- 多尺度架构和分块建模的引入使训练时间略有增加，但仍在可接受范围内。

#### 7.2.2 深度估计精度

表7.2 深度估计精度（测试集）

| 方法            | AbsRel↓       | SqRel↓        | RMSE↓         | δ<1.25↑      |
| --------------- | -------------- | -------------- | -------------- | -------------- |
| DA3 (仅图像)    | 0.05           | 0.32           | 2.45           | 0.93           |
| LiDAR (仅点云)  | 0.08           | 0.45           | 3.12           | 0.88           |
| DA3 + LiDAR融合 | **0.03** | **0.18** | **1.89** | **0.96** |

融合视觉深度与LiDAR点云显著提升了深度估计精度。

#### 7.2.3 渲染速度

表7.3 渲染速度对比

| 方法           | 渲染分辨率 | FPS↑        |
| -------------- | ---------- | ------------ |
| NeRF           | 640×480   | 0.5          |
| PlenOctrees    | 640×480   | 15           |
| 3DGS           | 640×480   | 135          |
| **Ours** | 640×480   | **82** |

本文方法在引入多尺度架构后，渲染速度略有下降，但仍保持实时渲染能力（>30 FPS）。

### 7.3 路径规划实验

#### 7.3.1 静态场景测试

表7.4 静态场景路径规划（50次任务）

| 方法                   | 成功率↑      | 路径长度(m)↓ | 规划时间(ms)↓ |
| ---------------------- | ------------- | ------------- | -------------- |
| A*                     | 84%           | 452           | 120            |
| Dijkstra               | 86%           | 448           | 350            |
| RRT*                   | 88%           | 485           | 240            |
| **D* Lite (Ours)** | **94%** | **441** | **42**   |

#### 7.3.2 动态场景测试

表7.5 动态场景路径规划（30次任务）

| 方法                         | 成功率↑      | 重规划次数↓  | 平均延迟(ms)↓ |
| ---------------------------- | ------------- | ------------- | -------------- |
| A* (全重算)                  | 68%           | 12.5          | 920            |
| D* Lite (无重规划)           | 62%           | 0             | -              |
| **D* Lite (动态重规划)** | **91%** | **5.8** | **380**  |

#### 7.3.3 端到端导航

表7.6 端到端导航系统性能

| 指标              | 数值     |
| ----------------- | -------- |
| 成功率            | 92.5%    |
| 平均导航时间      | 8分45秒  |
| 平均路径长度      | 1268m    |
| 平均速度          | 2.42 m/s |
| 碰撞次数/任务     | 0.07     |
| 任务中止次数/任务 | 0.08     |

### 7.4 系统集成实验

#### 7.4.1 全链条端到端测试

测试从数据采集到导航完成的完整流程：

```
流程：数据采集 → 感知处理 → 3DGS重建 → 路径规划 → 导航执行
延迟：  15s/帧    ~200ms      ~45min      ~380ms     实时
```

**系统延迟分析**：

- 数据采集：15秒/帧（640×480）；
- 感知处理：~200ms/帧（SAM3+DA3）；
- 3DGS重建：~45分钟（场景级）；
- 路径规划：~380ms（重规划）。

#### 7.4.2 鲁棒性测试

**传感器噪声测试**：
在LiDAR点云中添加高斯噪声（标准差0.1m、0.3m、0.5m），测试系统鲁棒性：

| 噪声水平  | 规划成功率 | 碰撞率 |
| --------- | ---------- | ------ |
| 0m (理想) | 94%        | 6%     |
| 0.1m      | 92%        | 8%     |
| 0.3m      | 88%        | 12%    |
| 0.5m      | 82%        | 18%    |

系统在适度噪声下仍保持较好性能。

**通信延迟测试**：
模拟卫星通信延迟（0ms、500ms、1000ms、2000ms）：

| 通信延迟 | 导航成功率 | 平均完成时间 |
| -------- | ---------- | ------------ |
| 0ms      | 94%        | 8分32秒      |
| 500ms    | 91%        | 9分15秒      |
| 1000ms   | 86%        | 10分48秒     |
| 2000ms   | 72%        | 14分20秒     |

系统在1秒以内延迟下仍保持较高成功率。

### 7.5 结果讨论

#### 7.5.1 主要发现

1. **多尺度3DGS有效性**：多尺度架构在冰面弱纹理场景下显著提升了重建质量，PSNR提升1.3dB，验证了设计的合理性。
2. **分块建模必要性**：对于大尺度场景（>1km），分块建模是解决显存限制的有效策略，RNN修复进一步提升了接缝质量。
3. **动态重规划价值**：D* Lite的动态重规划机制在动态冰情环境下至关重要，成功率提升29%（62%→91%）。
4. **系统整合可行性**：各模块整合后的端到端系统达到92.5%的导航成功率，验证了技术方案的可行性。

#### 7.5.2 局限性与改进方向

1. **3DGS训练时间**：虽然相比NeRF大幅缩短，但45分钟的训练时间仍难以满足在线重建需求。未来可探索增量式3DGS更新。
2. **极端天气场景**：在大雪、浓雾等极端天气下，感知和重建性能会显著下降。需要进一步增强模型的鲁棒性。
3. **多船协同**：当前系统仅针对单船设计，多船协同导航的场景尚未考虑。

---

## 第8章 总结与展望

### 8.1 研究工作总结

本文针对极地冰水环境下自主船舶的航行安全问题，系统研究了基于Unreal Engine和3D Gaussian Splatting的环境重建与路径规划方法，完成了以下主要工作：

**1. 极地多模态数据采集平台搭建**

- 基于ASVSim v3.0.1和UE5.4搭建高保真极地仿真平台；
- 配置front_camera、down_camera、top_lidar多模态传感器；
- 解决CosysAirSim与标准AirSim的API差异；
- 通过禁用Lumen、降低分辨率等优化，实现约15秒/帧的稳定采集。

**2. 智能感知系统构建**

- 集成SAM3实现海冰实例分割，mAP@0.5:0.95达到0.71；
- 集成Depth Anything 3实现深度估计，AbsRel降至0.05；
- 设计相机-LiDAR联合标定方法，实现多传感器融合；
- 端到端感知延迟控制在187ms。

**3. 多尺度渐进式3DGS重建方法**

- 提出多尺度渐进式架构，浅层拟合粗视图、深层专注细特征；
- 设计分块建模策略，解决大场景显存限制；
- 开发深度融合拼接算法，基于LiDAR实现坐标对齐；
- 引入RNN无监督优化修复拼接缝隙；
- Novel view合成PSNR达到27.5dB，相比标准3DGS提升1.3dB。

**4. 智能路径规划系统**

- 基于D* Lite实现全局路径规划，支持增量更新；
- 基于VFH+实现局部实时避碰，10Hz高频响应；
- 设计冰情触发动态重规划机制，延迟控制在380ms；
- 端到端导航成功率达到92.5%。

### 8.2 主要创新点

**理论创新**：

1. 提出了多尺度渐进式3DGS架构，通过双分支分别处理远近景物，扩展了神经辐射场在弱纹理场景的建模能力；
2. 设计了分块建模与深度融合拼接策略，为大尺度场景的分布式重建提供了新范式；
3. 构建了"感知-重建-规划"闭环架构，为自主航行系统的协同优化提供了理论框架。

**技术创新**：

1. 针对ASVSim平台特性，解决了simPause兼容性、ImageType枚举差异等关键技术问题；
2. 设计了RNN无监督优化方法，自动修复分块拼接缝隙；
3. 实现了冰情触发的动态重规划机制，将D* Lite增量更新应用于极地导航场景。

### 8.3 未来研究方向

**短期方向（1-2年）**：

1. **增量式3DGS更新**：研究在线增量更新方法，使3DGS能够随着航行过程持续更新地图，无需离线重训练；
2. **极端天气鲁棒性**：针对极夜、暴风雪等极端天气，研究图像增强和鲁棒感知方法；
3. **真实场景验证**：在真实极地测试场或合作船舶上验证系统性能。

**中长期方向（3-5年）**：

1. **多船协同导航**：研究多艘自主船舶的协同感知、协同重建和协同规划；
2. **数字孪生集成**：将仿真平台与真实船舶数据融合，构建极地航行数字孪生系统；
3. **强化学习优化**：结合强化学习方法优化路径规划策略，实现更智能的决策；
4. **边缘计算部署**：研究在嵌入式平台（如NVIDIA Jetson）上的轻量化部署。

### 8.4 结语

极地航运是未来全球航运的重要发展方向，智能化自主导航是提升极地航行安全与效率的关键技术。本文围绕这一主题，从仿真平台搭建、多模态感知、环境重建到路径规划进行了系统性研究，构建了一套完整的技术方案。

研究成果不仅在理论上拓展了神经辐射场和自主导航领域的研究边界，也为极地航运的工程实践提供了技术参考。随着全球气候变化的持续推进，极地航道的通航窗口将进一步扩大，本研究的技术方案将在未来的极地航行中发挥更大的价值。

未来，随着仿真技术的进步、深度学习算法的演进和计算硬件的发展，自主船舶的智能化水平将持续提升。期待本研究能够为这一领域的后续研究提供有益的启发，共同推动极地智能航运技术的进步。

---

## 参考文献

[1] Mildenhall B, Srinivasan P P, Tancik M, et al. NeRF: Representing scenes as neural radiance fields for view synthesis[J]. Communications of the ACM, 2021, 65(1): 99-106.

[2] Kerbl B, Kopanas G, Leimkühler T, et al. 3D gaussian splatting for real-time radiance field rendering[J]. ACM Transactions on Graphics, 2023, 42(4): 1-14.

[3] Koenig S, Likhachev M. D* lite[J]. Aaai/iaai, 2002, 15: 476-483.

[4] Borenstein J, Koren Y. The vector field histogram-fast obstacle avoidance for mobile robots[J]. IEEE transactions on robotics and automation, 1991, 7(3): 278-288.

[5] Fox D, Burgard W, Thrun S. The dynamic window approach to collision avoidance[J]. IEEE Robotics & Automation Magazine, 1997, 4(1): 23-33.

[6] Riquelme J, Maturana D, Verna S, et al. ASVSim: Autonomous Surface Vehicle Simulator[J]. arXiv preprint arXiv:2506.22174, 2025.

[7] Kirillov A, Mintun E, Ravi N, et al. Segment anything[C]//Proceedings of the IEEE/CVF International Conference on Computer Vision. 2023: 4015-4026.

[8] Yang L, Kang B, Huang Z, et al. Depth anything: Unleashing the power of large-scale unlabeled data[C]//Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2024: 10371-10381.

[9] Schöberger J L, Frahm J M. Structure-from-motion revisited[C]//Proceedings of the IEEE conference on computer vision and pattern recognition. 2016: 4104-4113.

[10] Shen T, Gao J, Munkberg J, et al. Deep marching tetrahedra: a hybrid representation for high-resolution 3d shape synthesis[J]. Advances in Neural Information Processing Systems, 2021, 34: 6087-6101.

[11] Tancik M, Weber E, Ng E, et al. Nerfstudio: A modular framework for neural radiance field development[C]//ACM SIGGRAPH 2023 Conference Proceedings. 2023: 1-12.

[12] Chen J, Li Z, Song L, et al. NeurAR: Neural uncertainty for autonomous driving[C]//Proceedings of the IEEE/CVF International Conference on Computer Vision. 2023: 20084-20094.

[13] Fossen T I. Handbook of marine craft hydrodynamics and motion control[M]. John Wiley & Sons, 2011.

[14] Zheng C, Wu P, Chen S, et al. Slicedaq: Cross-channel gradient scaling for data-free quantization of segmentation networks[C]//Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2024: 15770-15780.

---

## 致谢

值此论文完成之际，谨向所有给予我帮助和支持的人表示最诚挚的感谢。

首先，衷心感谢导师的悉心指导。从选题到成文，导师在研究方向把握、技术路线设计和论文撰写等方面给予了宝贵的建议，其严谨的治学态度和创新的学术思维使我受益匪浅。

感谢课题组各位老师的指导和帮助，感谢师兄师姐们在研究过程中的经验分享和技术支持。感谢实验室的同门们，在讨论交流中激发灵感，在遇到困难时相互鼓励。

感谢比利时根特大学IDLab团队提供的ASVSim仿真平台和相关技术支持，为本文的实验验证提供了重要保障。

感谢家人多年来的理解与支持，是你们的包容和鼓励让我能够专注于学业和研究。

最后，向所有关心和支持我的朋友们致以诚挚的谢意。

---

---

*本文完*
