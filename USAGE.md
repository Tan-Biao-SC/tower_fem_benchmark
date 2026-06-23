# Tower FEM Benchmark 使用指南

本项目提供统一入口 `run.py`，但周期单元和有限长桁架已经拆成独立流程：

- `periodic`：周期桁架单元建模，提取 PBC 刚度、RP 刚度和质量/惯性参数。
- `truss`：有限长桁架结构分析，支持模态、悬臂静力、简支静力和振型后处理。

## 前提条件

- Python 3.10+，需要 `numpy`。
- Windows PowerShell 下推荐 ANSYS v190，可执行文件为 `ansys190.exe`。
- 如果 ANSYS 不在 `PATH` 中，通过 `--ansys-exe` 传入完整路径。

示例：

```powershell
python run.py periodic --cases 0 --ansys-exe ansys190.exe
python run.py truss --cases 0 --ansys-exe ansys190.exe
```

## 目录结构

```text
tower_fem_benchmark/
├── run.py
├── common/                 # 公共 ANSYS 调用、路径管理、结果收集
├── periodic/               # 周期单元 Python 流程
├── truss/                  # 有限长桁架 Python 流程
├── templates/
│   ├── periodic/           # 周期单元 APDL 模板
│   └── truss/              # 有限长桁架 APDL 模板
├── cases/
│   ├── periodic/           # 生成的完整周期单元 .inp
│   └── truss/              # 生成的完整有限长桁架 .inp
├── tmp/
│   ├── periodic/           # ANSYS 周期单元工作目录
│   └── truss/              # ANSYS 有限长桁架工作目录
├── results/
│   ├── periodic/           # 周期单元结果与 periodic_summary.csv
│   └── truss/              # 有限长桁架结果与 truss_summary.csv
├── validations/            # 正式参考数据
└── figures/
    └── truss/              # 振型图等图片输出
```

`cases/` 只保存可复现的完整输入脚本；ANSYS 的 `.db`、`.rst`、`.emat` 等过程文件写入 `tmp/<module>/<case>/`；最终数值结果和日志收集到 `results/<module>/`。

## 周期单元流程

仅生成 APDL：

```powershell
python run.py periodic --dry-run
python run.py periodic --dry-run --cases 0
```

运行默认第 0 个 case：

```powershell
python run.py periodic --cases 0 --ansys-exe ansys190.exe
```

如果 `ansys190.exe` 不在 `PATH`：

```powershell
python run.py periodic --cases 0 --ansys-exe "C:\Program Files\ANSYS Inc\v190\ansys\bin\winx64\ansys190.exe"
```

单个周期 case 会顺序执行：

```text
basic model -> PBC stiffness -> basic model -> RP stiffness -> basic model -> inertia
```

输出文件：

```text
results/periodic/<case>.log
results/periodic/<case>_pbc_Dmatrix.csv
results/periodic/<case>_rp_Dmatrix.csv
results/periodic/<case>_inertia.txt
results/periodic/periodic_summary.csv
```

基于已有结果重新生成汇总表：

```powershell
python run.py periodic --summarize
python run.py periodic --summarize --cases 0
```

基于已有结果和参考数据验证：

```powershell
python run.py periodic --summarize --validate --cases 0
```

`periodic_summary.csv` 包含每个 case 的 `pbc_D11` 到 `pbc_D66`、`rp_D11` 到 `rp_D66`、PBC/RP 比值、总质量、质心和惯性矩阵主要分量。

默认 `periodic` case 定义在 `periodic/defaults.py`；参数结构定义在 `periodic/case.py`。
周期单元参考数据位于 `validations/periodic/<case>/`。

## 有限长桁架流程

仅生成 APDL：

```powershell
python run.py truss --dry-run
python run.py truss --dry-run --cases 0
```

运行指定 case：

```powershell
python run.py truss --cases 0 --ansys-exe ansys190.exe
```

运行后绘制前 7 阶振型：

```powershell
python run.py truss --cases 0 --plot-shapes 7 --ansys-exe ansys190.exe
```

运行后验证：

```powershell
python run.py truss --cases 0 --validate --ansys-exe ansys190.exe
```

基于已有结果重新生成汇总表：

```powershell
python run.py truss --summarize
```

输出文件按分析类型不同：

```text
results/truss/<case>.log
results/truss/<case>_freq.txt
results/truss/<case>_cantilever.txt
results/truss/<case>_simple.txt
results/truss/<case>_shape_<N>.txt
results/truss/truss_summary.csv
figures/truss/<case>_mode_<N>.png
```

`truss_summary.csv` 汇总每个已有结果 case 的几何参数、边界条件、构型信息、模态首频或静力最大绝对响应。

默认有限长桁架 case 定义在 `truss/defaults.py`；模板拼接顺序由 `truss/engine.py` 决定。

## 常用命令

```powershell
# 查看总入口
python run.py --help

# 查看子命令
python run.py periodic --help
python run.py truss --help

# 生成并检查周期单元输入
python run.py periodic --dry-run --cases 0

# 运行周期单元第 0 个 case，并生成汇总表
python run.py periodic --cases 0 --ansys-exe ansys190.exe

# 只重建周期单元汇总表
python run.py periodic --summarize

# 重建周期单元汇总表并验证第 0 个 case
python run.py periodic --summarize --validate --cases 0

# 运行有限长桁架第 0 个 case
python run.py truss --cases 0 --ansys-exe ansys190.exe

# 只重建有限长桁架汇总表
python run.py truss --summarize
```
