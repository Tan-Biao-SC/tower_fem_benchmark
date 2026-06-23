# AGENTS.md — tower_fem_benchmark

Parametric FEM benchmark for lattice transmission towers using ANSYS APDL.

## Instruction & Answering Languages
- I will use **English/Chinese** for instructions, and you should always use **Chinese** for answers.

## Running Cases

```bash
python run.py
```

- Reads `master.inp` template, substitutes `__XXX_VAL__` placeholders with case parameters, writes `.inp` files to `cases/`, then runs each through `ansys221 -b -i <case>.inp -o results/<case>.log`.
- ANSYS v221 must be on PATH as `ansys221`. Adjust `ansys_exe` in `run.py` if needed.
- Results are written to `results/<CASE_NAME>.txt` (modal frequencies, CSV: mode number, Hz).

## Two Template Systems

**Root template** (`master.inp`):
- Self-contained, used by `run.py`. Uses BEAM4 + LINK180.
- Placeholders: `__TH_VAL__`, `__SW_VAL__`, `__NP_VAL__`, `__NC_VAL__`, `__CASE_NAME_VAL__`.

**Modular templates** (`templates/`):
- Split into composable parts: model → diaphragm → brace → boundary condition → analysis [+ post-processing].
- Uses BEAM188 + LINK180 + MASS21 (with RBE3 for cross-section coupling).
- Placeholders: `__XXX_VAL__` (numbers), `__XXX_STR__` (strings).
- Files must be concatenated in order. `MAX_ELEM_NUM` variable chains element numbering across files.

### Modular Template Concatenation Order

```
01_model_basic.inp
  → 02_a_model_diaph_x.inp / 02_b_model_diaph_slash.inp
  → 03_a_model_brace_x.inp / 03_b_model_brace_w.inp / 03_c_model_brace_n.inp
  → [04_a_bc_fix_free.inp / 04_b_bc_simple.inp / 04_c_bc_elastic.inp]  (optional for free-free)
  → 05_modal_analysis.inp / 05_static_cantilever.inp / 05_static_simple.inp
  → [06_modal_post_shape.inp]  (optional, append after modal analysis)
```

### Analysis Scenarios

| Scenario | Template Sequence |
|----------|-------------------|
| Free-free modal | 01 → 02 → 03 → 05_modal_analysis [+ 06_modal_post_shape] |
| Cantilever modal | 01 → 02 → 03 → 04_a_bc_fix_free → 05_modal_analysis |
| Simple support modal | 01 → 02 → 03 → 04_b_bc_simple → 05_modal_analysis |
| Cantilever static | 01 → 02 → 03 → 04_a_bc_fix_free → 05_static_cantilever |
| Simple support static | 01 → 02 → 03 → 04_b_bc_simple → 05_static_simple |

### Analysis Template Details

- **`05_modal_analysis.inp`** — Modal solve + frequency extraction. Outputs `results/<CASE_NAME>_freq.txt` (CSV: mode, frequency Hz). Placeholder: `__NUM_MODES_VAL__`.
- **`06_modal_post_shape.inp`** — Optional mode shape extraction. Reads RBE3 master nodes (5000-series). Outputs `results/<CASE_NAME>_shape_<N>.txt`. Placeholder: `__TARGET_MODE_VAL__`.
- **`05_static_cantilever.inp`** — 6 load cases (FX/FY/FZ/MX/MY/MZ = 1e3) at tip RBE3 master node. Outputs `<CASE_NAME>_cantilever.txt` (CSV: load_case, ux–rz).
- **`05_static_simple.inp`** — 6 load cases uniformly distributed across all center nodes. Outputs `<CASE_NAME>_simple.txt` (CSV: load_case, node, ux–rz). No odd `NUM_NODE_PLANES` requirement.
- **`06_modal_post_shape.inp`** — Standalone post-processing. Loads `.db`/`.rst`, extracts single mode shape. Placeholder: `__TARGET_MODE_VAL__`. Outputs `<CASE_NAME>_shape_<N>.txt`.
- **`06_modal_plot_shape.inp`** — Standalone post-processing. Loads `.db`/`.rst`, plots 4-view deformed shapes for first N modes, extracts neutral-axis data for each. Placeholder: `__NUM_PLOT_MODES_VAL__`. Outputs `<CASE_NAME>_shape_<N>.txt` + PNG images.

### Design Principles

- **BC templates only apply constraints** — loads are defined in analysis templates.
- **Analysis templates include post-processing** — solve + result extraction in one file (tightly coupled).
- **Node numbering uses parameters** — tip node = `5000 + NUM_NODE_PLANES`, mid-span = `5000 + (NUM_NODE_PLANES+1)/2`.
- **Free-free modal** = no BC template concatenated.
- **All output filenames use `__CASE_NAME_VAL__`** — no `results/` prefix (ANSYS `*CFOPEN` doesn't support directories). Python runner moves files from `cases/` to `results/`.

## Python Driver

`run.py` uses the `benchmark/` package:
- `benchmark/case.py` — `CaseDefinition` dataclass + enums (DiaphType, BraceType, BCType, AnalysisType)
- `benchmark/engine.py` — `TemplateEngine`: resolve template sequence, concatenate, substitute placeholders
- `benchmark/runner.py` — `AnsysRunner`: generate .inp → run ANSYS → collect results; `run_post_shape()` and `run_plot_shape()` for standalone post-processing
- `benchmark/parser.py` — Parse result CSV files into numpy arrays
- `benchmark/validator.py` — Compare results against reference data

Usage:
```bash
python run.py                          # run all cases
python run.py --dry-run                # generate .inp files only
python run.py --validate               # run + validate
python run.py --plot-shapes 7          # after modal run, plot first 7 mode shapes
python run.py --cases 0 1 2            # run specific cases only
python run.py --ansys-exe /path/to/ansys221
```

## Key Parameters

| Symbol | Meaning | In `master.inp` | In `templates/` |
|--------|---------|-----------------|-----------------|
| Tower height | Total height (m) | `TH` | `NUM_SECTIONS × LS` |
| Section width | Cross-section width (m) | `SW` | `WS` |
| Periodic sections | Number of repeating cells | `NP` | `NUM_SECTIONS` |
| Sub-sections per cell | Subdivisions per cell | `NC` | `NUM_SUB_SECTIONS` |
| Sub-section length | Computed: height/(NP×NC) | `LL` | `LS` |

## Node Numbering Convention

- 1000-series: Bottom-left leg
- 2000-series: Bottom-right leg
- 3000-series: Top-right leg
- 4000-series: Top-left leg
- 5000-series: Cross-section center nodes (RBE3 master, templates only)

## Material

Steel: E = 2.06×10¹¹ Pa, ν = 0.31, ρ = 7850 kg/m³, α = 1.2×10⁻⁵ /°C.

## Validation Reference Data

- `validations/modal/modal_freq.txt` — reference modal frequencies (100 modes, free-free BC)
- `validations/static/tip_disp.txt` — reference tip displacements (6 load cases)

## Notes

- Comments in APDL files and `cases.md` are in Chinese.
- `templates/04_c_bc_elastic.inp` is empty (not yet implemented).
- `model1/` contains a standalone hand-run ANSYS model (`.mac` format) with its own results.
- `01_model_basic.inp` placeholders are now active (hardcoded values removed).