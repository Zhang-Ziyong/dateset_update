# 机器人 3D 激光 SLAM 数据集目录

> 自动生成于 2026-09-15。仅收录同时确认包含 3D 激光雷达和轨迹真值的数据集；README 发现项仍需人工复核。

共 **18** 个数据集。字段详情见 [JSON 数据](slam-datasets.json)。

## 筛选规则

- 必须能从官方文档、项目 README 或数据集页面确认 3D LiDAR/3D 激光型号或点云输入。
- 必须提供可用于轨迹评估的 ground truth/reference trajectory（例如 INS/RTK/GNSS、Leica、MoCap）。
- IMU、相机、轮速编码器等为可选传感器，缺失时明确标注。

## 汽车/自动驾驶

| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |
| --- | --- | --- | --- | --- |
| Argoverse 2 Sensor/Lidar Dataset<br>Argo AI 的大规模城市驾驶激光数据集，提供 32 线激光、HD map 和每帧 6-DOF 车辆定位。 | [Argoverse 2 API](https://github.com/argoverse/av2-api) | 3D LiDAR: 两台 Velodyne VLP-32C 32-beam 3D LiDAR<br>视觉: 7 个环视相机和 2 个前向双目相机（Sensor Dataset）<br>GNSS/RTK: GPS-based vehicle localization | 6-DOF ego-vehicle localization per timestamp | [数据集](https://www.argoverse.org/av2.html) / [链接1](https://github.com/argoverse/av2-api) / [链接2](https://www.argoverse.org/av2.html#download) |
| Boreas Dataset<br>覆盖雪、雨、夜间和季节变化的长时间自动驾驶激光数据集。 | [pyboreas](https://github.com/utiasASRL/pyboreas) | 3D LiDAR: Velodyne HDL-64E / 128-beam 3D LiDAR<br>IMU: Applanix POS LV IMU<br>视觉: Ladybug stereo camera<br>GNSS/RTK: Applanix GNSS/INS | Applanix POS LV reference trajectory | [数据集](https://www.boreas.utias.utoronto.ca/) / [链接1](https://github.com/utiasASRL/pyboreas) |
| KAIST Urban Dataset<br>城市场景激光-视觉-惯性数据集，包含多种交通和光照条件。 | [KAIST dataset ROS bag converter](https://github.com/tsyxyz/kaist2bag) | 3D LiDAR: Velodyne HDL-32E 3D LiDAR<br>IMU: Xsens IMU<br>视觉: PointGrey stereo camera<br>GNSS/RTK: RTK-GPS/INS | RTK-GPS/INS reference trajectory | [数据集](https://sites.google.com/view/complex-urban-dataset) / [文档](https://github.com/tsyxyz/kaist2bag#readme) / [链接1](https://github.com/MOLAorg/mola-input-kaist-dataset) |
| KITTI Odometry<br>经典自动驾驶里程计基准，适合评估激光-惯性和多传感器 SLAM。 | [LeGO-LOAM](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM) | 3D LiDAR: Velodyne HDL-64E 3D LiDAR<br>IMU: OXTS IMU/GNSS<br>视觉: 4 cameras (灰度/彩色)<br>编码器: OXTS vehicle odometry<br>GNSS/RTK: GPS/INS | OXTS GPS/INS reference trajectory | [数据集](https://www.cvlibs.net/datasets/kitti/eval_odometry.php) / [文档](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM#readme) / [链接1](https://www.cvlibs.net/datasets/kitti/setup.php) |
| KITTI-360<br>KITTI 系列的全景城市数据集，提供 360 度相机、Velodyne 激光和长距离行驶轨迹。 | [KITTI-360 scripts](https://github.com/autonomousvision/kitti360Scripts) | 3D LiDAR: Velodyne HDL-64E 3D LiDAR<br>IMU: IMU/GPS localization system (OXTS)<br>视觉: 4 个鱼眼相机和前向双目相机 | OXTS IMU/GPS 6-DOF pose trajectory | [数据集](https://www.cvlibs.net/datasets/kitti-360/) / [链接1](https://github.com/autonomousvision/kitti360Scripts) / [链接2](https://www.cvlibs.net/datasets/kitti-360/download.php) |
| MulRan<br>多城市、多天气的激光-惯性-卫星导航数据集，适合回环和长期定位。 | [MOLA MulRan input module](https://github.com/MOLAorg/mola_input_mulran_dataset) | 3D LiDAR: Ouster OS1-64 3D LiDAR<br>IMU: Xsens MTi-300 IMU<br>视觉: ZED stereo camera (部分序列)<br>GNSS/RTK: NovAtel GNSS/INS | NovAtel GNSS/INS reference trajectory | [数据集](https://sites.google.com/view/mulran-pr/dataset) / [文档](https://github.com/MOLAorg/mola_input_mulran_dataset#readme) / [链接1](https://github.com/RPM-Robotics-Lab/file_player_mulran) |
| nuScenes<br>Motional/nuTonomy 发布的大规模自动驾驶多传感器数据集，带时间同步的激光、相机和车辆位姿。 | [nuScenes devkit](https://github.com/nutonomy/nuscenes-devkit) | 3D LiDAR: 32-beam spinning 3D LiDAR<br>视觉: 6 个环视相机<br>GNSS/RTK: CAN bus expansion 中提供 IMU、pose、轮速等车辆状态 | Official ego-pose trajectory per sample | [数据集](https://www.nuscenes.org/nuscenes) / [链接1](https://www.nuscenes.org/download) / [链接2](https://github.com/nutonomy/nuscenes-devkit) |
| Oxford RobotCar<br>覆盖一年天气和昼夜变化的大规模真实道路机器人数据集。 | [RobotCar Dataset SDK](https://github.com/ori-mrg/robotcar-dataset-sdk) | 3D LiDAR: Velodyne HDL-32E 3D LiDAR<br>IMU: Applanix POS LV INS<br>视觉: Bumblebee stereo and PointGrey cameras<br>编码器: CAN bus vehicle odometry<br>GNSS/RTK: GPS/INS | Applanix INS/GPS trajectory | [数据集](https://robotcar-dataset.robots.ox.ac.uk/) / [文档](https://robotcar-dataset.robots.ox.ac.uk/documentation/) / [链接1](https://robotcar-dataset.robots.ox.ac.uk/datasets/) |
| PandaSet<br>Hesai 与 Scale AI 发布的开放自动驾驶数据集，包含高线数激光、相机、GPS 和逐帧传感器位姿。 | [PandaSet devkit](https://github.com/scaleapi/pandaset-devkit) | 3D LiDAR: Hesai Pandar64 和 PandarGT 3D LiDAR<br>视觉: 6 个相机<br>GNSS/RTK: GPS/IMU metadata | Per-frame LiDAR/camera pose in poses.json | [数据集](https://pandaset.org/) / [链接1](https://github.com/scaleapi/pandaset-devkit) / [链接2](https://scaleapi.github.io/pandaset-devkit/) |
| UrbanLoco<br>复杂城市道路的多模态定位数据集，适合 GNSS 退化和激光惯性研究。 | [LIO-SAM](https://github.com/TixiaoShan/LIO-SAM) | 3D LiDAR: Velodyne HDL-32E 3D LiDAR<br>IMU: Xsens IMU<br>视觉: 多目相机<br>编码器: 车辆 CAN/轮速<br>GNSS/RTK: RTK-GPS/INS | RTK-GPS/INS reference trajectory | [数据集](https://urbanloco.com/) / [文档](https://github.com/weisongwen/UrbanLoco) / [链接1](https://github.com/weisongwen/UrbanLoco#readme) |
| Waymo Open Dataset<br>Waymo 发布的高分辨率自动驾驶传感器数据和评测代码，包含多线激光与车辆运动信息。 | [Waymo Open Dataset code](https://github.com/waymo-research/waymo-open-dataset) | 3D LiDAR: 5 个车载 3D LiDAR（多线激光）<br>视觉: 5 个高分辨率相机 | Official vehicle pose in frame metadata | [数据集](https://waymo.com/open/) / [链接1](https://github.com/waymo-research/waymo-open-dataset) / [链接2](https://waymo.com/open/terms/) |

## 室内移动机器人

| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |
| --- | --- | --- | --- | --- |
| Hilti SLAM Challenge 2022<br>面向工程建筑环境的多传感器 SLAM 挑战数据，含高精度轨迹真值。 | [Hilti SLAM Challenge tools](https://github.com/Hilti-Research/hilti-slam-challenge-2022) | 3D LiDAR: Livox Mid-70 3D LiDAR<br>IMU: Xsens IMU<br>视觉: 双目/事件相机（按序列） | Leica BLK ARC/全站仪参考轨迹 | [数据集](https://hilti-challenge.com/dataset-2022.html) / [链接1](https://github.com/Hilti-Research/hilti-slam-challenge-2022) |

## 机器狗/四足机器人

| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |
| --- | --- | --- | --- | --- |
| M3ED (Multi-robot, Multi-sensor, Multi-environment Event Dataset)<br>跨车辆、Spot 机器狗和无人机的平台数据集，覆盖森林、城市、室内外和激烈运动。 | [M3ED processing code](https://github.com/daniilidis-group/m3ed) | 3D LiDAR: 64-channel 3D LiDAR, 10 Hz<br>IMU: 车载/机器狗 IMU（按平台和序列）<br>视觉: 高分辨率事件相机与普通相机 | evo-compatible ground-truth pose files | [数据集](https://m3ed.io/) / [链接1](https://m3ed.io/download/) / [链接2](https://github.com/daniilidis-group/m3ed) |

## 户外/越野机器人

| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |
| --- | --- | --- | --- | --- |
| NCLT (North Campus Long-Term)<br>校园长期运行数据，包含季节和路线变化，适合长期定位与回环检测。 | [hdl_graph_slam](https://github.com/koide3/hdl_graph_slam) | 3D LiDAR: Velodyne HDL-32E 3D LiDAR<br>IMU: Microstrain 3DM-GX3-45 IMU<br>视觉: Ladybug spherical camera<br>编码器: Segway wheel odometry<br>GNSS/RTK: Applanix localization/GPS | Applanix INS/GPS reference trajectory | [数据集](http://robots.engin.umich.edu/nclt/) |

## 无人机/空中机器人

| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |
| --- | --- | --- | --- | --- |
| NTU VIRAL<br>NTU ARIS 的空中机器人多传感器数据集，覆盖室内外飞行和激光退化场景。 | [NTU VIRAL dataset](https://github.com/ntu-aris/ntu_viral_dataset) | 3D LiDAR: 两台 3D LiDAR（包含 Ouster 点云，型号按序列记录）<br>IMU: 多个同步 IMU<br>视觉: 两台时间同步相机<br>UWB: UWB ranging nodes（室内外定位辅助） | Leica prism pose trajectory / CSV ground truth | [数据集](https://ntu-aris.github.io/ntu_viral_dataset/) / [链接1](https://researchdata.ntu.edu.sg/dataset.xhtml?persistentId=doi:10.21979/N9/X39LEK) / [链接2](https://github.com/ntu-aris/ntuviral_gt) / [链接3](https://ntu-aris.github.io/ntu_viral_dataset/evaluation_tutorial.html) |

## 混合场景

| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |
| --- | --- | --- | --- | --- |
| M2DGR (Multi-modal and Multi-scenario SLAM Dataset for Ground Robots)<br>面向地面机器人的多场景多模态 SLAM 基准，含室内、街道、桥梁和停车场序列。 | [Ground-Fusion](https://github.com/SJTU-ViSYS/Ground-Fusion) | 3D LiDAR: Robosense 16 3D LiDAR<br>IMU: Wheeltec IMU、Xsens MTi-680G GNSS-IMU<br>视觉: 多目鱼眼、RGB-D 和事件相机<br>编码器: 轮速里程计<br>GNSS/RTK: Ublox F9P GNSS-RTK | Vicon motion-capture、GNSS-RTK reference trajectory | [数据集](https://github.com/SJTU-ViSYS/M2DGR) / [文档](https://github.com/SJTU-ViSYS/M2DGR#readme) / [链接1](https://github.com/SJTU-ViSYS/M2DGR-plus) / [链接2](https://github.com/sjtuyinjie/M2DGR-Benchmark) |
| Newer College Dataset<br>牛津 New College 校园高精度多传感器数据，适合室内外过渡和激光惯性评估。 | [hdl_graph_slam](https://github.com/koide3/hdl_graph_slam) | 3D LiDAR: Ouster OS1-64 3D LiDAR<br>IMU: VectorNav VN-100 IMU<br>视觉: RealSense stereo/RGB cameras<br>GNSS/RTK: Leica/全站仪参考系统 | Leica/全站仪高精度参考轨迹 | [数据集](https://ori-drs.github.io/newer-college-dataset/) / [链接1](https://ori-drs.github.io/newer-college-dataset/download/) |
| R3LIVE-Dataset<br>HKU MARS 的 LiDAR-惯性-视觉数据集，覆盖 HKU/HKUST 校园、室内外和专门构造的退化场景。 | [R3LIVE](https://github.com/hku-mars/r3live) | 3D LiDAR: Livox LiDAR（livox_ros_driver，型号按序列/设备记录）<br>IMU: Livox/设备 IMU<br>视觉: 彩色相机 | ArUco marker relative pose (部分序列) | [数据集](https://github.com/ziv-lin/r3live_dataset) / [链接1](https://1drv.ms/f/c/3e715b7aa136191a/EqpK7QnN4OpCqHmL2ykpZ50Bjz3pyJ0kwyvwpBBLtzR4bQ?e=TqPN8E) / [链接2](https://pan.baidu.com/s/1zmVxkcwOSul8oTBwaHfuFg) |

## 维护

由 `slam_dataset_updater.py` 通过 GitHub Actions 定时更新。修改 `config.yaml` 中的搜索词或 workflow 的 cron 即可调整范围和时间。
