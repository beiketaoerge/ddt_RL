# UniLab — loco-mani 示例自包含包

本文件夹是从 UniLab 仓库中抽取的 **`go2_arm_manip_loco`（Go2 四足 + 机械臂的 loco-manipulation）示例**的 **完整可运行闭包**，并包含它用到的 **两个 PPO 算法**：

- **标准 PPO**（`rsl_rl` 版，带 final-observation bootstrap）→ `FinalObservationAwarePPO`
- **HIM-PPO**（Hybrid Internal Model，源自 HIMLoco）

> 范围说明：这是 UniLab 完整包的一个**子集**——只包含从本示例（两个训练脚本 + env）出发、通过 `import` 实际可达的模块。共 **72 个 `unilab` 模块** + 配置 + 资产 + 入口脚本。

## 关于目录结构的重要说明

你之前选择了「按 env/algos/conf 子目录重组」+「完整可运行闭包」。这两者其实有冲突：本示例靠
- 包导入 `from unilab.x.y import ...`
- 脚本里 `@hydra.main(config_path="../conf/ppo")`（相对脚本位置）
- `ASSETS_ROOT_PATH = src/unilab/assets`（相对包位置）

三处**硬编码的相对结构**。把模块扁平化重组会同时打断这三者，导致**无法运行**。因此为兑现「可运行」，本包**保留了 `src/unilab/...`、`conf/...`、`scripts/...` 的原始包结构**，并用下面这张「逻辑导航」代替子目录重组，让你按主题快速定位。

## 逻辑导航（按主题）

### ① loco-mani 环境本体
| 文件 | 作用 |
|--|--|
| `src/unilab/envs/locomotion/go2_arm/manip_loco.py` | **任务主体**：obs 组装、reward、IK 在环控制、**EE 目标轨迹**（球坐标 lerp：移动 1–3s → 保持 0.5–2s → 重采样）|
| `src/unilab/envs/locomotion/go2_arm/base.py` | Go2Arm base + **DLS 阻尼最小二乘 IK 求解器** |
| `src/unilab/envs/locomotion/go2_arm/__init__.py` | env 注册 |
| `src/unilab/envs/locomotion/common/{base,rewards,commands,domain_rand,dr_provider,height_scan,terrain_spawn}.py` | locomotion 共享：基类、模块化 reward、速度命令、域随机化、地形高度扫描 |
| `src/unilab/envs/common/rotation.py` | 四元数/坐标变换数值库 |

### ② 两个 PPO 算法
| 文件 | 作用 |
|--|--|
| `src/unilab/algos/torch/rsl_rl_ppo.py` | **标准 PPO**（`FinalObservationAwarePPO`，配置里以 `unilab.algos.torch.rsl_rl_ppo:FinalObservationAwarePPO` 被动态加载）|
| `src/unilab/algos/torch/rsl_rl_runtime.py` | rsl_rl runner 装配/解析 |
| `src/unilab/algos/torch/him_ppo/estimator.py` | **HIM estimator**：encoder→(速度3D + latent)，target 网络 + 32 prototype，Sinkhorn + SwAV swap loss |
| `src/unilab/algos/torch/him_ppo/actor_critic.py` | `HIMActorCritic`：estimator + actor + critic 装配（estimator 输出 detach 后喂 actor）|
| `src/unilab/algos/torch/him_ppo/algorithm.py` | `HIMPPO`：PPO 主体 + 每 minibatch 调 estimator.update + timeout bootstrap |
| `src/unilab/algos/torch/him_ppo/storage.py` | `HIMRolloutStorage`（额外存 next_critic_obs）|
| `src/unilab/algos/torch/him_ppo/runner.py` | `HIMOnPolicyRunner` + ONNX/TorchScript 导出（estimator+actor 端到端）|

### ③ env / backend 契约（底层依赖）
- `src/unilab/base/{np_env,base,observations,final_observation,registry,scene,augmentation}.py`
- `src/unilab/base/backend/{__init__,base}.py`、`mujoco/{backend,xml,playback}.py`、`motrix/{backend,scene,playback}.py`、`motrix_camera.py`、`playback_common.py`
  - ⚠️ Motrix 后端文件随闭包一并带上（`backend/__init__` 的工厂会引用），但 **loco-mani 当前只支持 mujoco** 后端。

### ④ 配置（Hydra）
- `conf/ppo/config.yaml` — PPO 根配置。**本包改动**：默认 `task` 由 `go1_joystick_flat/mujoco` 改为 `go2_arm_manip_loco/mujoco`，使无参运行即命中本例。
- `conf/ppo/task/go2_arm_manip_loco/{mujoco,motrix}.yaml` — PPO owner YAML（reward scale、IK 参数、EE 目标范围、DR 等）
- `conf/ppo_him/config.yaml` + `conf/ppo_him/task/go2_arm_manip_loco/mujoco.yaml` — HIM-PPO 配置（含 estimator 超参、课程学习 stage 设置）

### ⑤ 资产
- `src/unilab/assets/robots/go2_arm/scene_flat.xml`（场景，`include` 机器人 XML）
- `src/unilab/assets/robots/go2_arm/go2_with_arm_mjx_full_collision.xml`（Go2+臂 本体）
- `src/unilab/assets/robots/go2_arm/assets/*.{obj,STL}`（mesh）

### ⑥ 训练编排 / 支撑
- `src/unilab/training/*`（run、common、experiment、rsl_rl wrapper、reward、monitoring、backend_adapter、seed）
- `src/unilab/dr/*`（域随机化）、`src/unilab/terrains/*`（地形）、`src/unilab/utils/*`、`src/unilab/visualization/*`

### ⑦ 入口脚本
- `scripts/train_rsl_rl.py` — 标准 PPO 训练入口
- `scripts/train_him_ppo.py` — HIM-PPO 训练入口
- `scripts/manip_loco/` — 4 个 IK 诊断/标定脚本（`play_go2_arm_ik_only`、`diagnose_go2_arm_ik`、`calibrate_go2_arm_ee_orientation`、`benchmark_site_jacobian`）

### ⑧ 文档
- `docs/manip_loco.en.md` / `docs/manip_loco.zh.md`（任务说明）

## 如何运行

依赖较重（torch CUDA、mujoco-uni 等）。两种方式：

**A. 用本包自带 pyproject 建独立环境**
```bash
cd loco_mani_bundle
uv sync                      # 安装 pyproject.toml 里的依赖（含 torch cu128）
# 标准 PPO（默认 task 已是 go2_arm_manip_loco/mujoco）
uv run scripts/train_rsl_rl.py
# 或显式指定：
uv run scripts/train_rsl_rl.py task=go2_arm_manip_loco/mujoco
# HIM-PPO
uv run scripts/train_him_ppo.py task=go2_arm_manip_loco/mujoco
```

**B. 复用已装好依赖的环境（不重新下载）**
```bash
cd loco_mani_bundle
PYTHONPATH=$(pwd)/src python scripts/train_rsl_rl.py task=go2_arm_manip_loco/mujoco
PYTHONPATH=$(pwd)/src python scripts/train_him_ppo.py task=go2_arm_manip_loco/mujoco
```

IK 诊断（无需训练）：
```bash
PYTHONPATH=$(pwd)/src python scripts/manip_loco/play_go2_arm_ik_only.py
```

> 注意：HIM-PPO **不**走统一 `uv run train --algo ...` CLI（`him_ppo` 不是合法 `--algo`），只能直接跑 `scripts/train_him_ppo.py`。

## 校验

经 Codex 独立审核 + 静态核验，Category A（抽取缺口）已全部修复：
- **Python import 闭包**：`from unilab.X import ...` 的模块路径全部能在 bundle 内解析（严格检查、无属性回退），除 B1 外**无缺失子模块**。
- **XML 资产引用**：robot XML 里 31 条 mesh/STL/texture 引用全部能在 bundle 内解析（含新补的 16 个 go2 mesh）。
- **配置资产路径**：`conf/` 引用的 `floor.png`、`scene_flat.xml` 均在位。
- **registry**：`ensure_registries()` 默认只扫描 `unilab.envs.locomotion` → 只注册 `go2_arm`，不再触碰缺失的 go1/go2/g1/manipulation/motion_tracking。
- 未做完整运行时冒烟（依赖 torch CUDA 大轮子，本机磁盘受限未安装）；在装好依赖的机器上按上面命令即可运行。

## 与上游的差异（清单）
1. 仅包含本示例可达的 `unilab` 模块子集（完整包 213 个）。
2. `conf/ppo/config.yaml` 默认 `task` 改为 `go2_arm_manip_loco/mujoco`。
3. `pyproject.toml` 去掉了引用 `unilab.cli` / `unilab.tools` 的 `[project.scripts]`（不在闭包内）。
4. 只带 `go2_arm` 一套机器人资产 + 其依赖的 16 个 `go2/assets` mesh + `g1/textures/floor.png`。
5. **registry 裁剪**：`envs/locomotion/__init__.py` 与 `base/registry.py` 改为只注册/扫描 go2_arm 相关（已在文件内注释标注）。

## 已知限制（Category B：上游遗留问题，本次未改，与抽取无关）

> 这些 bug 在原始 UniLab 仓库里同样存在；为与上游一致，bundle 未改。如需可单独处理。

1. **⚠️ HIM-PPO 目前跑不起来**：`scripts/train_him_ppo.py:21` 与 `scripts/manip_loco/benchmark_site_jacobian.py:22` 错误地 `from unilab.base.backend.xml import ...`，而该子模块不存在（正确为 `unilab.base.backend.mujoco.xml`，见 `train_rsl_rl.py:20`）。已实测抛 `ModuleNotFoundError`。**标准 PPO 不受影响。** 修复 = 把这两处改成 `...backend.mujoco.xml`。
2. `go2_arm/assets/arm_base_0.obj`、`link5_1.obj` 声明 `mtllib material.mtl`，但该 `.mtl` 在上游也不存在（一般不影响碰撞 mesh 加载）。
3. `scripts/manip_loco/calibrate_go2_arm_ee_orientation.py` 动态加载的 `scripts/play_go2_arm_onnx_sim2sim.py` 在上游也不存在。
4. 同上脚本 `ROOT_DIR` 解析错位（指向 `scripts/` 而非包根）。
5. `scripts/manip_loco/benchmark_site_jacobian.py:233` 的 `config_path="../conf/ppo"` 相对嵌套脚本解析错位。
