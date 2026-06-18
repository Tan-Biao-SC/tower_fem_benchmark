# 桁架有限元分析工况

## 1. 有限元分析框架
```
|-- tower_fem_benchmark
    |-- model
    |   |-- basic_model.mac
    |   |-- Xbrace, Wbrace, Nbrace, KBrace
    |   |-- XDiaph, KDiaph, SlashDiaph
    |   |-- boundary
    |-- analysis
    |   |-- static
    |   |-- modal
    |-- postprocess
    |-- results
```

## 1. 影响因素分析

- 桁架类型：
  - 斜撑(X, K, W, N)
  - 横隔类型(X, /, K)
- 几何参数：
  - 周期单元数量($N=L/L_p$), 
  - 周期单元长度/总长度($\varepsilon = L/L_p$), 
  - 子节间数量($n=L_p/L_s$), 
  - 截面尺寸(高跨比$\lambda_H = L/a$)
- 刚度参数：
  - 横隔-塔柱线刚度比 $\beta_B=(EI/L)_\text{横隔} / (EI/L)_\text{塔柱}$， 
  - **斜材-塔柱轴向刚度比** $\beta_D$， 
  - **塔柱长细比** $\lambda_c$ (可能关系不大)
- 约束条件：
  - 悬臂梁，
  - 简支梁，
  - 弹性支撑；
  - 无约束（模态分析）

### 1.1 桁架构造


### 1.2 材料参数


## 2. 分析类型与内容

## 静力分析
- 位移（刚度验证）


## 动力分析（模态）
- 频率
- 模态振型

