# Tower FEM Benchmark — 使用指南

## 目录结构

```
tower_fem_benchmark/
├── run.py                  # 主入口脚本
├── extract_shape.py        # 模态振型提取脚本
├── benchmark/              # Python 包
│   ├── case.py             # 工况定义（数据类 + 枚举）
│   ├── engine.py            # 模板引擎（拼接 + 替换）
│   ├── runner.py            # ANSYS 运行器
│   ├── parser.py            # 结果解析器
│   └── validator.py         # 结果验证器
├── templates/               # APDL 模板文件
│   ├── 01_model_basic.inp
│   ├── 02_a_model_diaph_x.inp
│   ├── ...
│   ├── 05_modal_analysis.inp
│   ├── 05_static_cantilever.inp
│   ├── 05_static_simple.inp
│   ├── 06_modal_post_shape.inp
│   └── 06_modal_plot_shape.inp
├── cases/                   # ANSYS 工作目录（.inp, .db, .rst）
├── results/                 # 最终结果（.txt, .log）
└── validations/             # 参考数据
```

## 前提条件

- Python 3.10+（需要 `numpy`）
- ANSYS v221（`ansys221` 在 PATH 中，或通过 `--ansys-exe` 指定路径）

---

## 1. `run.py` — 主运行脚本

### 基本用法

```bash
# 运行所有工况
python run.py

# 仅生成 .inp 文件（不运行 ANSYS）
python run.py --dry-run

# 运行 + 验证
python run.py --validate

# 只运行指定工况（0-based 索引）
python run.py --cases 0 1 2

# 指定 ANSYS 路径
python run.py --ansys-exe /usr/ansys_inc/v221/ansys/bin/ansys221

# 运行模态分析后，绘制前 7 阶振型
python run.py --plot-shapes 7 --cases 0
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 仅生成 `.inp` 文件，不运行 ANSYS |
| `--validate` | 运行后与参考数据对比验证 |
| `--plot-shapes N` | 模态分析后绘制前 N 阶振型（需要先运行模态分析） |
| `--cases i j k` | 只运行指定索引的工况 |
| `--ansys-exe PATH` | 指定 ANSYS 可执行文件路径 |

### 工况定义

在 `run.py` 中通过 `CaseDefinition` 数据类定义工况：

```python
from benchmark.case import CaseDefinition, DiaphType, BraceType, BCType, AnalysisType

case = CaseDefinition(
    name="my_case",              # 工况名称（唯一标识）
    num_sections=10,             # 周期段数 (NP)
    num_subsections=2,           # 每段子节数 (NC)
    ls=3.0,                      # 子节长度 (m)
    ws=2.0,                      # 截面宽度 (m)
    diaph=DiaphType.X,           # 横隔类型: X 或 SLASH
    brace=BraceType.X,           # 斜撑类型: X, W, N
    bc=BCType.FIX_FREE,          # 边界条件: NONE, FIX_FREE, SIMPLE, ELASTIC
    analysis=AnalysisType.MODAL, # 分析类型: MODAL, STATIC_CANTILEVER, STATIC_SIMPLE
    num_modes=30,                # 模态提取阶数
)
```

### 模板拼接规则

根据工况参数自动选择模板并按顺序拼接：

| 分析场景 | 模板序列 |
|----------|----------|
| 自由模态 | 01 → 02 → 03 → 05_modal_analysis |
| 悬臂模态 | 01 → 02 → 03 → 04_a → 05_modal_analysis |
| 简支模态 | 01 → 02 → 03 → 04_b → 05_modal_analysis |
| 悬臂静力 | 01 → 02 → 03 → 04_a → 05_static_cantilever |
| 简支静力 | 01 → 02 → 03 → 04_b → 05_static_simple |

### 占位符替换

模板中的 `__XXX_VAL__`（数值）和 `__XXX_STR__`（字符串）会被自动替换：

| 占位符 | 替换为 |
|--------|--------|
| `__CASE_NAME_VAL__` / `__CASE_NAME_STR__` | 工况名称 |
| `__JobName_STR__` | 工况名称（ANSYS jobname） |
| `__NumSections_VAL__` | 周期段数 |
| `__NumSubsections_VAL__` | 每段子节数 |
| `__Ls_VAL__` | 子节长度 |
| `__Ws_VAL__` | 截面宽度 |
| `__NUM_MODES_VAL__` | 模态提取阶数 |
| `__TARGET_MODE_VAL__` | 目标模态阶数（post_shape 用） |
| `__NUM_PLOT_MODES_VAL__` | 绘制模态阶数（plot_shape 用） |

### 文件流转

```
run.py
  │
  ├─ TemplateEngine.build(case)
  │    └─ 拼接模板 + 替换占位符 → cases/<name>.inp
  │
  ├─ AnsysRunner.run_case(case)
  │    └─ ansys221 -b -i cases/<name>.inp -o results/<name>.log
  │       ├─ cases/<name>.db      ← 数据库文件
  │       ├─ cases/<name>.rst      ← 结果文件
  │       └─ cases/<name>_freq.txt ← 输出结果
  │
  └─ _collect_results()
       └─ cases/<name>_freq.txt → results/<name>_freq.txt
```

---

## 2. `extract_shape.py` — 模态振型提取

用于在模态分析完成后，提取单阶或多阶模态振型数据。

### 前提

`cases/` 目录下必须存在对应工况的 `.db` 和 `.rst` 文件（即必须先运行过模态分析）。

### 用法

```bash
# 查看可用工况
python extract_shape.py --list

# 提取第 7 阶模态振型数据
python extract_shape.py W2.0_cant_modal 7

# 绘制并提取前 7 阶模态振型（4 视角 PNG + 数据文件）
python extract_shape.py W2.0_cant_modal --plot 7

# 指定 ANSYS 路径
python extract_shape.py W2.0_cant_modal 7 --ansys-exe /path/to/ansys221
```

### 输出

| 命令 | 输出文件 |
|------|----------|
| `extract_shape.py <name> 7` | `results/<name>_shape_7.txt` |
| `extract_shape.py <name> --plot 7` | `results/<name>_shape_1.txt` ~ `results/<name>_shape_7.txt` + PNG 图片 |

振型数据文件格式：
```
Mode frequency =  1.23456E+02 Hz

Station,X(m),UX,UY,UZ,ROTX,ROTY,ROTZ
   1.,  0.0000, 0.00000E+00, 0.12345E-04, ...
   2.,  3.0000, 0.00000E+00, 0.23456E-04, ...
```

---

## 3. `benchmark` 包

### `case.py` — 工况定义

```python
from benchmark.case import *

# 枚举类型
DiaphType.X          # X 型横隔
DiaphType.SLASH       # 单斜杆横隔
BraceType.X           # X 型斜撑
BraceType.W           # W 型斜撑
BraceType.N           # N 型斜撑
BCType.NONE           # 自由-自由
BCType.FIX_FREE       # 固定-自由（悬臂）
BCType.SIMPLE         # 简支
AnalysisType.MODAL             # 模态分析
AnalysisType.STATIC_CANTILEVER # 悬臂静力
AnalysisType.STATIC_SIMPLE     # 简支静力

# 数据类
case = CaseDefinition(name="test", num_sections=10, num_subsections=2,
                      ls=3.0, ws=2.0)
case.tower_height      # → 60.0 (num_sections * num_subsections * ls)
case.num_node_planes   # → 21 (num_sections * num_subsections + 1)
```

### `engine.py` — 模板引擎

```python
from benchmark.engine import TemplateEngine
from pathlib import Path

engine = TemplateEngine(Path("templates"))

# 查看模板拼接顺序
seq = engine.resolve_sequence(case)
# → ['model_basic', DiaphType.X, BraceType.X, BCType.FIX_FREE, AnalysisType.MODAL]

# 生成完整 APDL 输入
content = engine.build(case)

# 生成单阶振型提取脚本
content = engine.build_post_shape(case, target_mode=7)

# 生成多阶振型绘图脚本
content = engine.build_plot_shape(case, num_plot_modes=7)
```

### `runner.py` — ANSYS 运行器

```python
from benchmark.runner import AnsysRunner

runner = AnsysRunner(engine, Path("cases"), Path("results"), ansys_exe="ansys221")

# 运行单个工况
runner.run_case(case)

# 提取单阶振型
runner.run_post_shape(case, target_mode=7)

# 绘制多阶振型
runner.run_plot_shape(case, num_plot_modes=7)

# 批量运行
results = runner.run_all(cases)  # → {name: bool}
```

### `parser.py` — 结果解析

```python
from benchmark.parser import parse_freq, parse_cantilever, parse_simple, parse_shape

# 模态频率
freq = parse_freq(Path("results/W2.0_cant_modal_freq.txt"))
# → ndarray (n_modes, 2): [[mode_num, freq_hz], ...]

# 悬臂端位移
disp = parse_cantilever(Path("results/brace_x_cant_static_cantilever.txt"))
# → ndarray (6, 6): [load_case, (ux, uy, uz, rx, ry, rz)]

# 简支全节点位移
load_cases, nodes, values = parse_simple(Path("results/..._simple.txt"))
# → load_cases: (N,), nodes: (N,), values: (N, 6)

# 模态振型
freq, data = parse_shape(Path("results/..._shape_7.txt"))
# → freq: float (Hz), data: (n_stations, 8)
```

### `validator.py` — 结果验证

```python
from benchmark.validator import validate_frequencies, validate_tip_disp

# 验证模态频率
ok = validate_frequencies(computed, reference, rtol=1e-4)

# 验证悬臂端位移
ok = validate_tip_disp(computed, reference, rtol=1e-3)
```

---

## 4. 完整工作流示例

### 示例 1：运行悬臂模态分析并提取振型

```bash
# 1. 运行工况 0（悬臂模态）
python run.py --cases 0

# 2. 提取第 1 阶振型数据
python extract_shape.py W1.5_cant_modal 1

# 3. 绘制前 7 阶振型（PNG + 数据）
python extract_shape.py W1.5_cant_modal --plot 7
```

### 示例 2：参数扫描 + 验证

```bash
# 1. 运行所有工况
python run.py

# 2. 验证结果
python run.py --validate
```

### 示例 3：仅生成输入文件（不运行 ANSYS）

```bash
# 生成所有工况的 .inp 文件到 cases/ 目录
python run.py --dry-run

# 查看生成的文件
ls cases/*.inp
```

### 示例 4：自定义工况

在 `run.py` 中添加：

```python
from benchmark.case import *

my_case = CaseDefinition(
    name="my_experiment",
    num_sections=5,
    num_subsections=3,
    ls=2.0,
    ws=1.5,
    diaph=DiaphType.SLASH,
    brace=BraceType.W,
    bc=BCType.SIMPLE,
    analysis=AnalysisType.STATIC_SIMPLE,
)
ALL_CASES.append(my_case)
```

然后运行：

```bash
python run.py --cases -1  # 运行最后一个工况
```

---

## 5. 输出文件说明

### 模态分析输出

| 文件 | 格式 | 说明 |
|------|------|------|
| `<name>_freq.txt` | CSV: `mode,freq_hz` | 模态频率 |
| `<name>_shape_<N>.txt` | 见下方 | 第 N 阶振型中性轴位移 |

振型文件格式：
```
Mode frequency =  1.23456E+02 Hz

Station,X(m),UX,UY,UZ,ROTX,ROTY,ROTZ
   1.,  0.0000, 0.00000E+00, 0.12345E-04, ...
```

### 静力分析输出

| 文件 | 格式 | 说明 |
|------|------|------|
| `<name>_cantilever.txt` | CSV: `load_case,ux,uy,uz,rx,ry,rz` | 悬臂端 6 载荷工况位移 |
| `<name>_simple.txt` | CSV: `load_case,node,ux,uy,uz,rx,ry,rz` | 简支全节点位移 |

### ANSYS 中间文件（在 `cases/` 目录）

| 文件 | 说明 |
|------|------|
| `<name>.db` | ANSYS 数据库（几何、网格、参数） |
| `<name>.rst` | ANSYS 结果文件（振型、应力等） |
| `<name>.err` | ANSYS 错误文件 |

> **注意**：`.db` 和 `.rst` 文件保留在 `cases/` 目录中，供 `extract_shape.py` 后续使用。如需清理，请手动删除。