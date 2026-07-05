# Tower FEM Benchmark 使用指南

本项目通过统一入口 `run.py` 运行两类 ANSYS APDL 分析：

- `periodic`：周期桁架单元分析，计算 PBC 刚度、RP 刚度以及质量和惯性参数。
- `truss`：有限长格构塔分析，支持模态、悬臂静力、简支静力及模态振型绘制。

## 环境要求

- Python 3.10 或更高版本
- Python 依赖：`numpy`
- ANSYS Mechanical APDL；代码默认调用 `ansys190.exe`

如果 ANSYS 可执行文件不在 `PATH` 中，请通过 `--ansys-exe` 传入名称或完整路径：

```powershell
python run.py truss --cases 0 --ansys-exe "C:\Program Files\ANSYS Inc\v190\ansys\bin\winx64\ansys190.exe"
```

## 快速开始

查看总帮助及子命令帮助：

```powershell
python run.py --help
python run.py periodic --help
python run.py truss --help
```

仅生成 APDL 输入文件，不启动 ANSYS：

```powershell
python run.py periodic --dry-run
python run.py truss --dry-run
```

运行 Python 默认工况中的第 0 个工况：

```powershell
python run.py periodic --cases 0
python run.py truss --cases 0
```

`--cases` 使用从 0 开始的下标。未指定 `--cases` 时，将运行对应模块的全部 Python 默认工况。

为兼容旧用法，省略子命令时，根级选项会按 `truss` 处理，例如：

```powershell
python run.py --dry-run --cases 0
```

等价于：

```powershell
python run.py truss --dry-run --cases 0
```

## 推荐：使用 CSV 工况表

仓库提供两个示例工况表：

- `cases/periodic_cases.csv`
- `cases/truss_cases.csv`

先查看工况及其下标、ID、名称、启用状态和标签：

```powershell
python run.py periodic --case-table cases/periodic_cases.csv --list-cases
python run.py truss --case-table cases/truss_cases.csv --list-cases
```

按稳定 ID、名称、标签或下标选择工况：

```powershell
python run.py truss --case-table cases/truss_cases.csv --case-ids T001
python run.py truss --case-table cases/truss_cases.csv --case-names base_modal
python run.py truss --case-table cases/truss_cases.csv --tags baseline modal
python run.py truss --case-table cases/truss_cases.csv --cases 0 2
```

选择规则如下：

- 不提供选择器时，只运行 `enabled=true` 的工况。
- 显式使用 `--cases`、`--case-ids`、`--case-names` 或 `--tags` 时，也可选中已禁用工况。
- 多种选择器同时出现时采用“或”关系；`--tags` 后的多个标签要求工况同时包含这些标签。
- `--case-ids`、`--case-names` 和 `--tags` 只能与 `--case-table` 一起使用。
- CSV 中的 `id` 和 `name` 都必须唯一；`tags` 用空格分隔。

### 周期单元 CSV 字段

```text
id,name,tags,enabled,num_sections,num_subsections,ls,ws,density,brace_area,description
```

### 有限长桁架 CSV 字段

```text
id,name,tags,enabled,num_sections,num_subsections,ls,ws,diaph,brace,bc,analysis,num_modes,description
```

枚举字段可用值：

- `diaph`：`x`、`slash`
- `brace`：`x`、`w`、`n`
- `bc`：`none`、`fix_free`、`simple`、`elastic`
- `analysis`：`modal`、`static_cantilever`、`static_simple`

注意：`elastic` 对应的边界条件模板目前尚未实现，不应作为正式计算工况使用。

## 周期单元分析

运行指定 CSV 工况：

```powershell
python run.py periodic `
  --case-table cases/periodic_cases.csv `
  --case-ids P002 `
  --ansys-exe ansys190.exe
```

每个周期工况依次执行以下计算：

```text
基础模型 → PBC 刚度 → 基础模型 → RP 刚度 → 基础模型 → 质量与惯性
```

主要输出：

```text
cases/periodic/<case>.inp
results/periodic/<case>.log
results/periodic/<case>_pbc_Dmatrix.csv
results/periodic/<case>_rp_Dmatrix.csv
results/periodic/<case>_inertia.txt
results/periodic/<case>_mass_matrix.csv
results/periodic/periodic_summary.csv
```

正常运行结束后会自动生成 `periodic_summary.csv`。若已有结果，只重建汇总表：

```powershell
python run.py periodic --summarize
```

未指定工况表或选择器时，汇总命令会读取 `cases/periodic_cases.csv` 中注册的全部工况（包括 `enabled=false` 的工况），并汇总其中已有完整结果的工况。缺少 PBC、RP 或惯性文件的工况会被跳过。

如需只重建部分工况的汇总，可显式传入工况表和选择器：

```powershell
python run.py periodic `
  --case-table cases/periodic_cases.csv `
  --case-ids P001 P002 `
  --summarize
```

根据 `validations/periodic/<case>/` 中已有的参考数据进行验证：

```powershell
python run.py periodic `
  --case-table cases/periodic_cases.csv `
  --case-ids P002 `
  --summarize `
  --validate
```

没有对应参考目录的工况会被跳过。

## 有限长桁架分析

运行模态工况：

```powershell
python run.py truss `
  --case-table cases/truss_cases.csv `
  --case-ids T001 `
  --ansys-exe ansys190.exe
```

运行模态分析后，继续绘制前 7 阶振型：

```powershell
python run.py truss `
  --case-table cases/truss_cases.csv `
  --case-ids T001 `
  --plot-shapes 7
```

`--plot-shapes N` 只作用于所选的模态工况，并依赖该次模态求解生成的数据库和结果文件。

运行并验证结果：

```powershell
python run.py truss --cases 0 --validate
```

验证内容取决于分析类型：模态工况对比 `validations/modal/modal_freq.txt`，悬臂静力工况对比 `validations/static/tip_disp.txt`；其他工况不执行验证。

主要输出：

```text
cases/truss/<case>.inp
results/truss/<case>.log
results/truss/<case>_freq.txt
results/truss/<case>_cantilever.txt
results/truss/<case>_simple.txt
results/truss/<case>_shape_<N>.txt
results/truss/truss_summary.csv
figures/truss/<case>_mode_<N>.png
```

每个工况只产生与其分析类型对应的结果文件。正常运行结束后会自动生成 `truss_summary.csv`。若已有结果，只重建汇总表：

```powershell
python run.py truss --case-table cases/truss_cases.csv --summarize
```

## 目录与文件流转

```text
tower_fem_benchmark/
├── run.py                     # 统一 CLI 入口
├── common/                    # 公共 ANSYS 调用、路径及 CSV 工况工具
├── periodic/                  # 周期单元 Python 流程
├── truss/                     # 有限长桁架 Python 流程
├── templates/
│   ├── periodic/              # 周期单元 APDL 模板
│   └── truss/                 # 有限长桁架 APDL 模板
├── cases/
│   ├── periodic_cases.csv     # 周期单元示例工况表
│   ├── truss_cases.csv        # 有限长桁架示例工况表
│   ├── periodic/              # 生成的周期单元 .inp
│   └── truss/                 # 生成的有限长桁架 .inp
├── tmp/<module>/<case>/       # ANSYS 每个工况的工作目录
├── results/<module>/          # 日志、数值结果和汇总表
├── figures/truss/             # 模态振型图片
└── validations/               # 参考结果
```

生成的完整 `.inp` 保存在 `cases/<module>/`。ANSYS 的 `.db`、`.rst`、`.emat` 等中间文件保存在 `tmp/<module>/<case>/`，最终日志和数值结果会被收集到 `results/<module>/`。

## 工况定义位置

- 周期单元 Python 默认工况：`periodic/defaults.py`
- 周期单元参数结构：`periodic/case.py`
- 有限长桁架 Python 默认工况：`truss/defaults.py`
- 有限长桁架参数结构：`truss/case.py`
- 模板选择与拼接：`periodic/engine.py`、`truss/engine.py`

日常批量计算建议维护 CSV 工况表；Python 默认工况更适合开发、回归和参数扫描。
