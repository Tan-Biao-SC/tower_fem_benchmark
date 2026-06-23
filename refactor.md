# 项目重构方案

## 1. 重构目标

本项目后续同时服务两个层级的分析任务：

1. 周期桁架单元建模，并提取等效刚度参数和质量/惯性参数。
2. 由周期桁架单元组成有限长桁架结构，开展模态、静力和参数分析。

重构的核心目标是把这两类任务在代码、模板、结果和 ANSYS 过程文件上清晰分离，同时保留统一入口 `run.py`，避免后续批量分析时文件互相覆盖或职责混乱。

## 2. 推荐目录结构

```text
tower_fem_benchmark/
├── run.py
├── templates/
│   ├── periodic/
│   └── truss/
├── periodic/
│   ├── __init__.py
│   ├── case.py
│   ├── engine.py
│   ├── runner.py
│   ├── parser.py
│   └── defaults.py
├── truss/
│   ├── __init__.py
│   ├── case.py
│   ├── engine.py
│   ├── runner.py
│   ├── parser.py
│   └── defaults.py
├── common/
│   ├── __init__.py
│   ├── ansys.py
│   └── paths.py
├── cases/
│   ├── periodic/
│   └── truss/
├── results/
│   ├── periodic/
│   └── truss/
├── figures/
│   ├── periodic/
│   └── truss/
├── tmp/
│   ├── periodic/
│   └── truss/
├── references/
├── deprecated/
├── test/
├── theories.md
├── USAGE.md
└── AGENTS.md
```

目录职责：

- `templates/`：只存放可参数化的 ANSYS APDL 模板，不存放运行产物。
- `periodic/`：周期桁架单元参数提取的 Python 程序。
- `truss/`：有限长桁架模型分析的 Python 程序。
- `common/`：跨模块共享能力，例如 ANSYS 调用、路径管理、文件收集。
- `cases/`：Python 生成的完整 ANSYS 输入脚本，作为可复现分析记录。
- `tmp/`：ANSYS 实际工作目录，存放 `.DB`、`.rst`、`.full`、`.emat`、`.err` 等过程文件。
- `results/`：最终数值结果、日志和汇总文件。
- `figures/`：最终图片输出。
- `test/`：保留当前已验证的探索性命令流，作为迁移来源和人工对照，不作为正式批处理入口。
- `deprecated/`：历史模型和旧验证数据，暂不参与新流程。

## 3. 模块边界

### 3.1 `periodic/`

负责周期桁架单元的 FEM 建模和等效参数提取。

输入参数应覆盖：

- 单元内部子节数量 `n`。
- 单元长度、截面宽度等几何参数。
- 主材、横隔、斜材的截面参数。
- 材料弹性模量、泊松比、密度。
- 刚度提取方式：周期边界 PBC、刚性端平面 RP。

主要输出：

- `*_pbc_Dmatrix.csv`
- `*_rp_Dmatrix.csv`
- `*_inertia.txt`
- 后续需要增加惯性参数汇总表，从`*_inertia.txt`中提取出完整的惯性参数表，例如 `*_mass.csv`
- 后续可增加统一汇总表，例如 `periodic_summary.csv`。

初始实现应同时保留两种刚度计算：

- PBC：来自 `test/pbcstiff.mac`，代表松弛周期边界下的等效刚度。
- RP：来自 `test/rpstiff.mac`，代表刚性端平面约束下的等效刚度。

惯性参数使用当前已验证的 `IRLF,-1` 和 `IRLIST` 流程。

### 3.2 `truss/`

负责有限长桁架结构分析。

输入参数应覆盖：

- 周期单元数量。
- 每个周期单元的几何和构件参数。
- 边界条件：自由、悬臂、简支，后续可扩展弹性支承。
- 分析类型：模态、静力、振型后处理。

主要输出：

- 模态频率。
- 静力位移/转角响应。
- 模态振型数据。
- 振型图或结构响应图。

当前 `benchmark/` 中与有限长塔架相关的逻辑可逐步迁移到 `truss/`，迁移完成后再删除或废弃 `benchmark/`。

### 3.3 `common/`

共享逻辑应少而稳定，避免把业务分支塞入 common。

建议初始只放：

- `AnsysCommand` 或 `run_ansys()`：统一封装 ANSYS 调用。
- `ProjectPaths`：统一管理 `templates/cases/results/figures/tmp` 的模块子目录。
- 文件收集工具：从 `tmp/<module>/<case>/` 收集结果到 `results/<module>/`。

ANSYS 调用必须使用参数列表，不使用字符串拼接和 `shell=True`：

```python
subprocess.run(
    [ansys_exe, "-b", "-i", str(input_path), "-o", str(log_path)],
    cwd=str(work_dir),
)
```

Windows PowerShell 下默认可执行文件使用 `ansys190.exe`，同时保留 `--ansys-exe` 传入完整路径的能力。

## 4. 运行方式

统一入口 `run.py` 只负责命令行调度，不承载具体建模逻辑。

建议命令形式：

```bash
python run.py periodic --dry-run
python run.py periodic --cases 0 1 2
python run.py periodic --ansys-exe ansys190.exe

python run.py truss --dry-run
python run.py truss --cases 0 1 2
python run.py truss --plot-shapes 7
python run.py truss --validate
```

运行流程统一为：

1. 从 `defaults.py` 或配置文件读取 case 列表。
2. 根据 case 和模板生成完整 APDL 输入脚本到 `cases/<module>/`。
3. 为每个 case 创建独立工作目录 `tmp/<module>/<case_name>/`。
4. 在该工作目录中调用 ANSYS。
5. 收集最终输出到 `results/<module>/` 和 `figures/<module>/`。

## 5. 模板迁移方案

### 5.1 周期单元模板

从 `test/` 迁移并参数化以下文件：

- `basicmodel.mac` -> `templates/periodic/01_basic_model.inp`
- `pbcstiff.mac` -> `templates/periodic/02_pbc_stiffness.inp`
- `rpstiff.mac` -> `templates/periodic/03_rp_stiffness.inp`
- `inertia.mac` -> `templates/periodic/04_inertia.inp`

必须参数化：

- `/FILNAME`
- `RESUME`
- `NUM_SUB_SECTIONS`
- `LS`
- `WS`
- 构件截面参数
- 材料参数
- 输出文件名

每个 case 使用独立 job name，避免数据库和结果互相覆盖。

### 5.2 有限长桁架模板

当前 `templates/` 中已有有限长模型模板，迁移到 `templates/truss/`：

- `01_model_basic.inp`
- `02_*_model_diaph_*.inp`
- `03_*_model_brace_*.inp`
- `04_*_bc_*.inp`
- `05_*_analysis.inp`
- `06_*_shape.inp`

迁移后保持原模板拼接顺序不变，先保证 `python run.py truss --dry-run` 输出与当前 `run.py --dry-run` 等价。

## 6. 分阶段实施计划

### 阶段 1：建立新目录和公共运行基础

- 新增 `common/`、`periodic/`、`truss/` 包。
- 新增 `tmp/`，并更新 `.gitignore` 忽略 ANSYS 过程文件。
- 实现跨平台 ANSYS 调用封装，默认支持 Windows `ansys190.exe`。
- 暂不删除旧 `benchmark/` 和旧模板。

验收标准：

- `python run.py --help` 可显示新的子命令结构。
- 不运行 ANSYS 时，所有路径创建和 dry-run 行为正常。

### 阶段 2：迁移有限长桁架现有流程

- 将 `benchmark/` 的 case、engine、runner、parser 逻辑迁移到 `truss/`。
- 将现有 `templates/*.inp` 移动到 `templates/truss/`。
- 修改 `run.py truss` 调用新模块。
- 保留现有模态、静力和振型后处理能力。

验收标准：

- `python run.py truss --dry-run` 可生成完整输入脚本。
- 生成脚本与重构前逻辑保持一致。

### 阶段 3：实现周期单元批处理

- 将 `test/` 中验证过的周期单元命令流迁移为 `templates/periodic/` 模板。
- 实现 `PeriodicCase` 和默认参数扫描。
- 实现 PBC 刚度、RP 刚度、惯性参数的顺序运行。
- 实现结果收集和基础解析。

验收标准：

- `python run.py periodic --dry-run` 可生成完整周期单元 APDL 脚本。
- 单个 case 在 Windows PowerShell + `ansys190.exe` 下可输出 PBC、RP 和惯性结果。
- 默认 case 的输出能与 `test/` 中已有结果对照。

### 阶段 4：结果汇总和验证

- 增加 `periodic_summary.csv`，汇总每个 case 的关键刚度和惯性参数。
- 增加有限长桁架参数分析汇总。
- 将验证数据整理到 `validations/` 或 `references/validation/`。
- 更新 `USAGE.md`。

验收标准：

- 周期单元批量参数分析有统一汇总表。
- 有限长桁架分析仍可独立运行。
- 文档中的命令可直接复现主要流程。

## 7. 重要设计约束

- `cases/` 不作为 ANSYS 工作目录，只保存生成的完整输入脚本。
- `tmp/` 是 ANSYS 工作目录，可安全清理，不作为长期结果保存目录。
- `results/` 只保存最终结果和必要日志。
- `test/` 中现有命令流在迁移完成前不删除，作为验证基准。
- 新增代码优先保持简单，不引入外部依赖；解析 CSV/TXT 可先使用 Python 标准库或现有 numpy。
- 每次重构尽量保持小提交：目录迁移、公共 runner、truss 迁移、periodic 实现分别提交。

## 8. 风险与处理

- Windows 路径中可能包含空格：必须用 `subprocess.run([...])` 参数列表调用 ANSYS。
- ANSYS 输出文件名不宜包含目录：APDL 内部只写当前工作目录文件，Python 负责移动到 `results/`。
- 批量运行会产生大量过程文件：每个 case 使用独立 `tmp/<module>/<case_name>/`。
- 当前仓库可能存在 Windows 权限位变化：后续提交前检查 `git diff --stat`，必要时单独处理文件模式变化。
- 周期单元和有限长桁架参数含义不同：不要强行共用同一个 `CaseDefinition`，只共用底层 ANSYS 调用和路径工具。
