# 周期桁架单元刚度和质量参数计算

**核心问题：**
1. 如何通过`FEM`建立周期桁架单元模型，并求解与`EBM`对应的截面刚度矩阵$\mathbf{D}$和截面
   质量矩阵$\mathbf{M}$
2. 如何处理周期桁架单元两端横隔的贡献，`EBM`中其对应变能$U$和动能$T$的贡献只取1/2；
   `FEM`中如何处理？
3. 如何处理周期桁架单元的约束？

---

# 1.截面刚度矩阵$\mathbf{D}$计算
## 1.1 基本原理
### 1.1.1 截面刚度矩阵的本质

对于沿 (x) 轴布置的一维等效梁，可以定义截面广义应变向量$\boldsymbol{\alpha}$:

$$
\boldsymbol{\alpha} = 
    \begin{bmatrix}
    \varepsilon_x&
    \kappa_y&
    \kappa_z&
    \gamma_{xy}&
    \gamma_{xz}&
    \kappa_x
\end{bmatrix}^{\mathrm T}.
$$

其中：
* $\varepsilon_x$：轴向应变；
* $\kappa_y$：绕 $y$ 轴弯曲曲率；
* $\kappa_z$：绕 $z$ 轴弯曲曲率；
* $\gamma_{xy}$：沿 $y$ 方向的广义剪切应变；
* $\gamma_{xz}$：沿 $z$ 方向的广义剪切应变；
* $\kappa_x$：扭转率

与之共轭的截面广义内力$\mathbf{f}$可以写成

$$
\mathbf f =
    \begin{bmatrix}
    N & M_y & M_z & V_y & V_z & T
    \end{bmatrix}^{\mathrm T}.
$$

在线弹性范围内，$\boxed{\mathbf f=\mathbf D\boldsymbol{\alpha}}$, 其中:

$$
\mathbf D=
    \begin{bmatrix}
    D_{11}&D_{12}&\cdots&D_{16}\\
    D_{21}&D_{22}&\cdots&D_{26}\\
    \vdots&\vdots&\ddots&\vdots\\
    D_{61}&D_{62}&\cdots&D_{66}
\end{bmatrix}
$$

就是截面刚度矩阵。

因此，$\mathbf D$ 不是某个有限元节点刚度矩阵，也不是周期单元整体的端部刚度矩阵。它表示：

> 单位长度等效梁中，广义应变与截面广义内力之间的本构关系


---
### 1.1.2 $\mathbf{D}$的基本性质
#### 1.1.2.1 $\mathbf D$ 必须是对称矩阵

对于线弹性保守系统，应变能存在，因此
$$
    D_{ij} = D_{ji}.
$$

这来自 `Maxwell–Betti` 互等定理，也来自二次型 `Hessian` 的对称性：
$$
    \mathbf D = \frac{1}{L} \frac{\partial^2 U}{
        \partial \boldsymbol{\alpha} \partial \boldsymbol{\alpha}^{\mathrm T}}.
$$

所以：
$$
    \boxed{ \mathbf D = \mathbf D^{\mathrm T} }
$$

- 如果通过反力法分别算出 $D_{ij}$ 和 $D_{ji}$，二者差别较大，通常意味着：
    * 广义内力提取有误；
    * 端部力矩合成有误；
    * 边界条件不一致；
    * 刚体约束影响了结果；
    * 数值误差或单位问题。
- 能量法天然只识别对称部分

---

#### 1.1.2.2 截面刚度矩阵还必须半正定或正定

应变能必须满足
$$
    U = \frac12 L \boldsymbol{\alpha}^{\mathrm T} \mathbf D \boldsymbol{\alpha} \ge 0.
$$

因此，$ \mathbf D \succeq 0.$

若六种广义变形均有有限刚度且不存在机构，则应有
$$
    \mathbf D \succ 0.
$$

也就是说，$\mathbf D$ 的全部特征值应为正。这是比逐项检查 $D_{ii}>0$ 更严格的验证。

即使所有对角项都为正，也不能保证整个矩阵正定。例如，过大的耦合项可能导致
$$
    D_{ij}^2 > D_{ii} D_{jj},
$$

从而使某个二阶主子式为负。

对于任意两个分量，至少应满足
$$
    \boxed{ D_{ij}^2 \le D_{ii} D_{jj} }
$$

正定时为严格小于。

---

#### 1.1.2.3 对称结构为什么很多耦合项为零

对于正方形、双向对称 X-X 桁架，如果：
* 几何关于 $y=0$ 对称；
* 几何关于 $z=0$ 对称；
* 材料和截面布置也相应对称；
* 坐标原点位于几何与刚度中心；

那么许多耦合项理论上应为零。例如：
* 轴向—弯曲耦合 $D_{12},D_{13}$ 通常为零；
* 两个方向弯曲耦合 $D_{23}$ 通常为零；
* 轴向—剪切耦合一般为零；
* 对称方形截面下 $D_{22}=D_{33}$；
* $D_{44}=D_{55}$。

理想情况下可能接近对角矩阵：
$$
    \mathbf D \approx \operatorname{diag} \left(
    EA_{\mathrm{eq}}, EI_{y,\mathrm{eq}}, EI_{z,\mathrm{eq}}, 
    GA_{y,\mathrm{eq}}, GA_{z,\mathrm{eq}}, GJ_{\mathrm{eq}}
    \right).
$$

但是“根据对称性推测为零”与“有限元没有计算它们”是两回事。

比较严谨的做法是：
1. 先由对称性推导哪些项应严格为零；
2. 再用少量组合工况验证这些项接近零；
3. 报告其相对于主对角项的归一化大小。

例如定义
$$
    \eta_{ij} = \frac{|D_{ij}|} {\sqrt{D_{ii} D_{jj}}}.
$$

若$ \eta_{ij}\ll 1 $, 则可以认为该耦合项可忽略。

---

### 1.1.3 采用`FEM`计算截面刚度矩阵$D$的原理与方法

公式$\mathbf{f} = \mathbf{D} \mathbf{\alpha}$ 建立了截面刚度矩阵与单元内力之间的关系。
进一步地，由此可以获得单元内不应变能与截面刚度之间的关系。也即是说，可以根据如下思路获得
截面刚度矩阵$\mathbf{D}$:
1. 给周期单元施加广义应变$\alpha_i$
2. 获取周期单元内部的全部杆件的总应变能$U$
3. 计算对应的刚度矩阵元素$D_{ij}$

#### 1.1.3.1 截面应变能密度

单位长度等效梁的应变能为

$$
\mathcal U =\frac12\boldsymbol{\alpha}^{\mathrm T} \mathbf D \boldsymbol{\alpha}.
$$

注意这里的 $\mathcal U$ 是单位长度的应变能，量纲为$[\mathcal U]=\mathrm{N}.$

如果周期单元长度为 $L$，且广义应变在周期单元内保持常数，那么周期单元总应变能为

$$
    U = \int_0^L 
    \frac12\boldsymbol{\alpha}^{\mathrm T} \mathbf D \boldsymbol{\alpha} 
    \mathrm dx
$$

若 $\mathbf D$ 和 $\boldsymbol{\alpha}$ 沿 $x$轴不变，则

$$
    \boxed{
        U = \frac12 L \boldsymbol{\alpha}^{\mathrm T} \mathbf D \boldsymbol{\alpha}
    }
$$

这就是有限元识别方法的理论基础

展开后：

$$
    U= \frac12 L \left[
    \sum_{i=1}^{6}D_{ii}\alpha_i^2 + 2\sum_{i<j}D_{ij}\alpha_i\alpha_j
    \right]
$$

**这里要特别注意交叉项前面的系数 2**。

例如，只考虑 $\varepsilon_x$ 和 $\kappa_y$：

$$
    U= \frac12 L \left(
        D_{11}\varepsilon_x^2 + 2 D_{12}\varepsilon_x\kappa_y +D_{22} \kappa_y^2
    \right)
$$

---

#### 1.1.3.2 `FEM`识别$\mathbf{D}$的基本原理

精细有限元模型的总应变能为 
$$
U_{\mathrm{FE}} = \sum_e U_e 
$$

等效梁模型的周期单元应变能为

$$
U_{\mathrm{EBM}} = \frac12 L \boldsymbol{\alpha}^{\mathrm T} \mathbf D \boldsymbol{\alpha}.
$$

能量等效要求

$$
\boxed{ U_{\mathrm{FE}} = U_{\mathrm{EBM}}}
$$

因此，只要有限元模型中施加的边界条件确实对应某个给定的宏观广义应变 $\boldsymbol{\alpha}$，
就可以通过有限元总应变能反求 $\mathbf D$。

---
## 1.2 截面刚度矩阵的具体计算方法

矩阵 $\mathbf D$ 的系数分为对角项$D_{i,j} (i=j)$和交叉项$D_{i,j} (i \ne j)$。以下分别
介绍二者的计算方法

### 1.2.1 对角刚度项的计算

假设只施加第$i$个广义应变：$ \alpha_i=A, \alpha_{j\ne i}=0.$

此时, 周期单元的总应变能为
$$
    U_i = \frac12 L D_{ii} A^2.
$$

因此
$$
    \boxed{ D_{ii} = \frac{2 U_i}{L A^2} }
$$

具体而言，可以在`FEM`中分别施加
$\varepsilon_x, \kappa_y, \kappa_z, \gamma_{xy}, \gamma_{xz}, \kappa_x$, 
计算各自对应的总应变能，最终得到对角刚度项：
$$
    D_{11} = \frac{2U_{\varepsilon_x}}{L A^2}, \quad
    D_{22} = \frac{2U_{\kappa_y}}{L A^2}, \quad
    D_{33} = \frac{2U_{\kappa_z}}{L A^2}, \\
    D_{44} = \frac{2U_{\gamma_{xy}}}{L A^2}, \quad
    D_{55} = \frac{2U_{\gamma_{xz}}}{L A^2}, \quad
    D_{66} = \frac{2U_{\kappa_x}}{L A^2}.
$$

---

### 1.2.2 各对角刚度参数的量纲

#### 1.2.2.1 轴向刚度

$$
    N=D_{11} \varepsilon_x.
$$

因为 $\varepsilon_x$ 无量纲，所以

$$
    [D_{11}] = \mathrm N.
$$

对于普通梁，

$$
    D_{11} = EA.
$$

---

#### 1.2.2.2 弯曲刚度

$$
    M_y = D_{22} \kappa_y.
$$

因为
$$
    [\kappa_y] = \mathrm m^{-1}, \qquad [M_y] = \mathrm{N \cdot m},
$$

所以
$$
    [D_{22}] = \mathrm{N \cdot m^2}.
$$

经典梁中：
$$
    D_{22}=EI_y, \qquad D_{33}=EI_z.
$$

但具体是 $I_y$ 还是 $I_z$，取决于你对曲率符号和弯矩方向的定义。现在的定义中：
$$
    u_x=\varepsilon_x x+z\kappa_y x-y\kappa_z x,
$$

因此：

* $\kappa_y$ 对应轴向应变随$z$变化；
* $\kappa_z$ 对应轴向应变随$y$变化。

所以一般有：
$$
    D_{22} \sim EI_y, \qquad D_{33} \sim EI_z.
$$

---

#### 1.2.2.3 剪切刚度

$$
    V_y = D_{44} \gamma_{xy}.
$$

因 $\gamma_{xy}$ 无量纲，所以
$$
    [D_{44}] = \mathrm N.
$$

经典梁中通常写作
$$
    D_{44} = k_yGA_y, \qquad D_{55} = k_zGA_z.
$$

对于空间桁架，所谓“等效剪切刚度”并不等于材料剪切模量乘某个真实截面面积，而是由斜撑轴向变形等
微观机制综合形成。

---

#### 1.2.2.4 扭转刚度

$$
    T=D_{66}\kappa_x.
$$

因此
$$
    [D_{66}] = \mathrm{N \cdot m^2}.
$$

经典梁中为
$$
    D_{66} = GJ.
$$

对于空间桁架，它同样是等效参数。

---

### 1.2.3 非对角项的计算方法

*当前程序只做六个单分量工况，所以只能获得六个对角项。*
#### 1.2.3.1 直接工况组合法

要获得 $D_{ij}$，必须施加至少两个广义应变分量。

令
$$
    \alpha_i=A,\qquad \alpha_j=A.
$$

则
$$
    U_{ij}^{++} = \frac12 L \left( D_{ii} A^2 + D_{jj} A^2 + 2 D_{ij} A^2 \right).
$$

而单独加载时：
$$
    U_i = \frac12 L D_{ii} A^2, \quad U_j = \frac12 L D_{jj} A^2.
$$

所以
$$
    \boxed{ D_{ij} = \frac{ U_{ij}^{++} - U_i - U_j }{ L A^2 } }
$$

---

#### 1.2.3.2 正负组合工况法

即使用使用四点中心差分形式

分别计算：
$$
    U(+A,+A), \quad U(+A,-A), \quad U(-A,+A), \quad U(-A,-A). 
$$

那么
$$
    \boxed{ D_{ij} = \frac{ U(+A,+A) - U(+A,-A) - U(-A,+A) + U(-A,-A) }{ 4 L A^2 } }
$$

不过在线性有限元中，由于应变能关于全部广义应变是偶对称二次型，有
$$
    U(-A,-A) = U(+A,+A), \quad U(-A,+A) = U(+A,-A).
$$

因此也可以简化为

$$
    \boxed{ D_{ij} = \frac{ U(+A,+A) - U(+A,-A) }{ 2 L A^2 } }
$$

这种方法的优势在于：

* 对角项自动抵消；
* 不必依赖先前计算出的 $D_{ii}$、$D_{jj}$；
* 数值上通常更稳定；
* 更容易检查符号。

---

#### 1.2.3.3 更一般的矩阵识别方法

可以把每个有限元工况写为
$$
    2 U^{(k)} / L = \boldsymbol{\alpha}^{(k) \mathrm T} \mathbf D \boldsymbol{\alpha}^{(k)}.
$$

因为 $\mathbf D$ 对称，所以一个完整的 $6 \times 6$ 刚度矩阵只有$ \frac{6(6+1)}2=21$
个独立参数。理论上至少需要 21 个线性独立的能量工况，才能识别完整矩阵。

最简单的工况配置为：
* 6 个单分量工况，用于 $D_{ii}$；
* 15 个双分量组合工况，用于 $D_{ij}$。

若使用正负组合提高稳健性，则工况数会更多。

---

### 1.3 基于反力的识别方法

另一个思路是直接计算截面广义内力：
$$
    \mathbf f=\mathbf D\boldsymbol{\alpha}.
$$

对第 $j$ 个单位广义应变工况：
$$
    \boldsymbol{\alpha} = A \mathbf{e}_j,
$$

则
$$
    \mathbf{f} = A \mathbf{D} \mathbf{e}_j.
$$

所以
$$
    \boxed{ D_{ij} = \frac{f_i}{A} }
$$

也就是说，一次广义应变加载可以给出 $\mathbf D$ 的一整列，而不只是一个对角元素。

例如，施加 $\varepsilon_x = A$ 后，如果可以可靠提取：
$$
    N,\ M_y,\ M_z,\ V_y,\ V_z,\ T,
$$

则可以一次得到
$$
    D_{11},D_{21},D_{31},D_{41},D_{51},D_{61}.
$$

理论上只需六个工况便能获得完整矩阵。

但对复杂离散桁架而言，广义内力的提取比总应变能更容易出现问题：
* 端部结点反力需要正确合成；(**实际上很难做到**)
* 弯矩需考虑力对截面中心的力矩；
* 周期约束方程中的反力不总是容易直接解释；
* 需要严格区分左右端截面内力符号。

因此：
> 能量法更稳健，反力法更高效；最理想的做法是二者交叉验证。

---

## 1.3 `FEM`中的具体操作原理与方法

### 1.3.1 施加“宏观广义应变”

刚度计算公式本身其实不难。真正困难的是：
> 你在有限元边界上施加的位移差，是否真的对应定义中的 $\boldsymbol{\alpha}$。

对于一维梁，设截面参考点位移和转角为
$$
    \boldsymbol{\beta} = [u_x,u_y,u_z,\theta_x,\theta_y,\theta_z]^{\mathrm T}.
$$

根据广义应变定义，通常有(其中剪切应变与横向位移导数和截面转角有关)
$$
    \varepsilon_x=u_x',\quad 
    \gamma_{xy}=u_y'-\theta_z,\quad
    \gamma_{xz}=u_z'+\theta_y, \\
    \kappa_y=\theta_y',\qquad
    \kappa_z=\theta_z',\qquad
    \kappa_x=\theta_x',
$$

如果广义应变沿 $x$ 恒定，则积分后截面中性轴($y=0, z=0$)位移一般包含：
$$
    u_x(x) = \varepsilon_x x, \quad
    \theta_y(x)=\kappa_yx, \quad
    \theta_z(x)=\kappa_zx, \quad
    \theta_x(x)=\kappa_xx.
$$

横向位移由于弯曲曲率积分，会包含二次项：
$$
    u_y(x) = \gamma_{xy} x + \frac12 \kappa_z x^2 + C_y, \\
    u_z(x) =  \gamma_{xz} x - \frac12 \kappa_y x^2 + C_z,
$$

截面上任一点 $(x,y,z)$ 的位移还要加上刚性截面转动贡献：

$$
    u_x^{p} = u_x + z \theta_y - y \theta_z, \\
    u_y^{p} = u_y - z \theta_x, \\
    u_z^{p} = u_z + y \theta_x, \\
$$


- 若坐标原点位于模型左侧，即$x_L=0, x_R=L$， 则位移差公式如下：
$$
    \Delta u_x = L \left( \varepsilon_x + z \kappa_y - y \kappa_z \right), \\
    \Delta u_y = L \gamma_{xy} + \frac12 L^2 \kappa_z -z L \kappa_x, \\
    \Delta u_z = L \gamma_{xz} - \frac12 L^2 \kappa_y + y L \kappa_x, \\
    \Delta \theta_x = L \kappa_x, \\
    \Delta \theta_y = L \kappa_y, \\
    \Delta \theta_z = L \kappa_z.
$$

- 若坐标原点位于模型中心，即$x_L=-L/2, x_R=L/2$， 则位移差公式如下：
$$
    \Delta u_x = L \left( \varepsilon_x + z \kappa_y - y \kappa_z \right), \\
    \Delta u_y = L \gamma_{xy} - z L \kappa_x, \\
    \Delta u_z = L \gamma_{xz} + y L \kappa_x, \\
    \Delta \theta_x = L \kappa_x, \\
    \Delta \theta_y = L \kappa_y, \\
    \Delta \theta_z = L \kappa_z.
$$

- 更一般的位移差公式，对任意左右端点坐标$x_L, x_R$，令$L=x_R - x_L$，则
$$
    x_R^2 - x_L^2 = L (x_R + x_L), \\
    \Delta u_x = L \left( \varepsilon_x + z \kappa_y - y \kappa_z \right), \\
    \Delta u_y = L \gamma_{xy} + \frac12 L (x_R + x_L) \kappa_z - z L \kappa_x, \\
    \Delta u_z = L \gamma_{xz} - \frac12 L (x_R + x_L) \kappa_y + y L \kappa_x, \\
    \Delta \theta_x = L \kappa_x, \\
    \Delta \theta_y = L \kappa_y, \\
    \Delta \theta_z = L \kappa_z.
$$

**注意：** 
1. 这里的坐标原点不一定是建模时设定的坐标原点
2. 而是模型发生变形时的**参考点**，即刚体位移和刚体转动的参考点（不动点），换句话说：
   - 计算节点位移差时，选择以模型**左侧**为坐标原点的公式后，约束就应该设置在模型**左侧**
   - 计算节点位移差时，选择以模型**中心**为坐标原点的公式后，约束就应该设置在模型**中心**

### 1.3.2 周期性模型的约束设置

在`EBM`等效连续梁模型中，我们假定周期桁架单元的截面始终服从平截面假定，即一定程度上认为桁架单元
的截面内变形不变（注意：等效模型中我们还是引入了$\varepsilon_{y}, \varepsilon_{z}$两个自由度）。

因此，在模型刚性参数验证时，应当包含两个层面的验证：
1. 周期单元的截面保持刚性假定，验证等效连续梁模型本身的推导过程是否正确
2. 周期单元完全自由，说明平截面假定对刚性参数的具体影响

在第一个层面的验证中，需要考虑以下问题：
1. `EBM`推导时，虽然采用了平截面假定，但是也引入了截面变形自由度；也就是说周期单元内部的截面
   不是完全的刚性平面，
2. 在周期单元`FEM`建模时，如果用`CERIG`将内部横隔全部设置为刚性平面，可能会严重高估其扭转刚度；
   因此，只需在模型的两端建立刚性平面约束，内部允许自由变形；但是，这样又无法确保周期单元内部
   的节点按照`EBM`梁位移场发生变形。这里可能会导致一定的误差（随$n$的增加而增加）

这里必须把两类边界条件严格区分，因为它们对应的物理问题不同：

1. **只消除整体刚体运动**：周期单元两端允许截面畸变、翘曲和局部变形；
2. **两端保持刚性平面**：端截面四个角点只能随一个刚性参考截面平移和转动。

**二者得出的剪切刚度和扭转刚度应该不同。**

除此之外，为了确保模型可以正常求解（即不存在奇异方程），还需要约束周期单元的全部刚体运动。

#### 1.3.2.1 “宏观广义应变”对模型的约束

在周期单元施加广义应变的本质是在模型两端施加位移差：
$$
    \mathbf u_R-\mathbf u_L = \Delta\mathbf u(\boldsymbol\alpha), \\
    \boldsymbol \theta_R - \boldsymbol \theta_L = \Delta \boldsymbol \theta(\boldsymbol \alpha).
$$

这些约束规定的是**左右端差值**，但不会规定模型的绝对位置。因此，整个模型仍然可以叠加任意刚体运动：

$$
    \mathbf u^{\mathrm{rb}} = \mathbf a + \boldsymbol \omega \times \mathbf r
$$

其中：

* \(\mathbf a\) 为三个刚体平移；
* \(\boldsymbol\omega\) 为三个刚体转动。

所以必须另外消除 6 个刚体自由度。关键原则是：

> 消除刚体运动的附加约束不能限制微观周期变形。

---

#### 1.3.2.2 工况一：只限制刚体运动

根据[1.3.1节](#131-施加宏观广义应变)中所提到的内容，周期单元的刚体运动约束必须施加到模型广义
应变计算的参考位置处。

因此，此处我们约定：
> 始终以模型左侧为参考位置，计算广义应变（即需要施加的位移差）
> 刚体运动约束也施加到模型左侧

如果只限制周期单元刚体运动，那么可以在模型左右端建立`RBE3`约束，将左右端的节点运动关系绑定到
两端节点中心。如果左端中心节点 `5001` 通过合适的 RBE3 关系表示左端截面的平均运动，那么可以
直接采用：

```apdl
D,5001,UX,0
D,5001,UY,0
D,5001,UZ,0
D,5001,ROTX,0
D,5001,ROTY,0
D,5001,ROTZ,0
```

或者：
```apdl
D,5001,ALL,0
```

这一做法的物理含义不是把左端整个截面固定，而是选择一个刚体运动基准：

$$
    \mathbf u_c(x_L)=\mathbf0, \qquad
    \boldsymbol\theta_c(x_L)=\mathbf0.
$$

由于周期约束只规定两端运动差，绝对平移和绝对转角本来就是任意的。把左端参考运动取为零，
相当于选定一个“坐标规约”，理论上不改变应变能。

例如纯弯曲工况：
$$
    \theta_z(x_R) - \theta_z(x_L) = L\kappa_z.
$$

虽然以模型中点为原点的对称表示是
$$
    \theta_z(x_L) = -\frac{L\kappa_z}{2}, \qquad
    \theta_z(x_R) = +\frac{L\kappa_z}{2},
$$

也可以整体叠加刚体转角 \(L\kappa_z/2\)，写成

$$
    \theta_z(x_L) = 0, \qquad \theta_z(x_R) = L\kappa_z.
$$

两者应变完全相同，只相差一个刚体转动。

---

#### 1.3.2.3 工况二：保证两端截面为刚性平面

让左右端四个角点的位移完全由各自截面中心参考节点的 6 个自由度决定。

对于端截面中心节点 (c)，角点 (k) 的刚性运动在线性小转动下为：

$$
    u_x^{(k)} = u_{x,c} + z_k \theta_{y,c} - y_k \theta_{z,c}, \\
    u_y^{(k)} = u_{y,c} - z_k \theta_{x,c}, \\
    u_z^{(k)} = u_{z,c} + y_k \theta_{x,c}.
$$

如果同时要求角点梁节点的转角与截面转角一致，则：

$$
    \theta_x^{(k)} = \theta_{x,c},\\
    \theta_y^{(k)} = \theta_{y,c},\\
    \theta_z^{(k)} = \theta_{z,c}.
$$

要保证端截面刚性，应改用以下方式之一：

* `CERIG`；
* MPC184 刚性梁/刚性区域；

本例采用`CERIG`，对左端，可建立中心节点为主节点、四个角点为从节点的刚性区域：

```apdl
NSEL,S,LOC,X,-LCELL/2
NSEL,U,NODE,,5001
CERIG,5001,ALL,ALL
ALLSEL,ALL
```

右端类似：
```apdl
NSEL,S,LOC,X,LCELL/2
NSEL,U,NODE,,5000+NUM_NODE_PLANES
CERIG,5000+NUM_NODE_PLANES,ALL,ALL
ALLSEL,ALL
```

在这种情况下：

* 左端四角节点组成刚体截面；
* 右端四角节点组成刚体截面；
* 中间截面不需要刚化；
* 宏观广义应变可直接施加在两个中心参考节点之间

---

刚性端面情况下，周期方程可以简化。设左、右中心参考节点分别为 \(C_L,C_R\)。

只需要对中心节点建立：

$$
    u_{x,R}^c - u_{x,L}^c = L \varepsilon_x, \\
    u_{y,R}^c - u_{y,L}^c = L \gamma_{xy},\\
    u_{z,R}^c - u_{z,L}^c = L \gamma_{xz},\\
    \theta_{x,R}^c - \theta_{x,L}^c = L \kappa_x,\\
    \theta_{y,R}^c - \theta_{y,L}^c = L \kappa_y,\\
    \theta_{z,R}^c - \theta_{z,L}^c = L \kappa_z.
$$

因为刚性区域自动保证角点位移满足

$$
    u_x^{(k)} = u_x^c + z_k \theta_y^c - y_k \theta_z^c,
$$

等关系，所以不需要再逐个角点施加周期位移差。

然后固定左端中心节点：

```apdl
D,5001,ALL,0
```

右端中心节点直接施加对应位移：

```apdl
D,NRC,UX,LCELL*EX
D,NRC,UY,LCELL*GXY
D,NRC,UZ,LCELL*GXZ
D,NRC,ROTX,LCELL*KX
D,NRC,ROTY,LCELL*KY
D,NRC,ROTZ,LCELL*KZ
```

这里由于已经把左中心节点固定为零，不一定再需要 CE，可以直接使用 `D`。

---

#### 1.3.2.4 这两种边界条件的物理区别

##### 工况1：仅消除刚体运动

允许端部截面产生：

* 面内畸变；
* 翘曲；
* 角点相对平移；
* 角点相对转动；
* 构件端部自然弯曲。

它求得的实际上是：

$$
    \boxed{ \text{周期单元在允许微观松弛条件下的有效刚度} }
$$

从变分角度说，内部和边界微观自由度会自动选择使应变能最小的状态：

$$
    U_{\mathrm{per}} = \min_{\widetilde{\mathbf u}\ \mathrm{periodic}} U_{\mathrm{FE}}.
$$

因此它通常更柔。

---

##### 工况2：两端刚性平面

端部四个角点不允许相对变形，端面必须保持刚体。

它求得的是：

$$
    \boxed{ \text{刚性端板约束下周期结构段的等效端部刚度} }
$$

由于可容许位移空间变小，根据最小势能原理，一般有：

$$
    U_{\mathrm{rigid}} \ge U_{\mathrm{per}},
$$

进而通常得到：

[
D_{ii}^{\mathrm{rigid}}
\ge
D_{ii}^{\mathrm{per}}.
]

差异通常在以下参数上更明显：

* 剪切刚度；
* 扭转刚度；
* 短周期结构段的弯曲刚度。

轴向刚度受影响可能较小。

---

## 1.4 刚性参数验证工况安排

为了把两类误差区分开，论文中的验证逻辑可以概括为：

$$
    \boxed{ 
        \text{理论模型} \longleftrightarrow 
        \text{刚性平面 FEM} \longleftrightarrow
        \text{周期松弛 FEM}
    }
$$

明确设置三组刚度矩阵：

$$
    \mathbf D^{\mathrm{theory}}(n),\qquad
    \mathbf D^{\mathrm{FEM\text{-}RP}}(n),\qquad
    \mathbf D^{\mathrm{FEM\text{-}PBC}}(n).
$$

其中：
* \(\mathbf D^{\mathrm{theory}}\)：理论等效梁模型；
* \(\mathbf D^{\mathrm{FEM\text{-}RP}}\)：两端刚性平面条件下的精细 `FEM`；
* \(\mathbf D^{\mathrm{FEM\text{-}PBC}}\)：允许截面周期性微观畸变、仅排除刚体运动的精细 `FEM`。

---

### 1.4.1 三组结果的关系

理想情况下应看到：

$$
    \mathbf D^{\mathrm{theory}} \approx \mathbf D^{\mathrm{FEM\text{-}RP}}
$$

而
$$
    \mathbf D^{\mathrm{FEM\text{-}RP}} \ne \mathbf D^{\mathrm{FEM\text{-}PBC}}.
$$

因此：
$$
    \boxed{
    \mathbf D^{\mathrm{theory}} \approx 
    \mathbf D^{\mathrm{FEM\text{-}RP}} \ge 
    \mathbf D^{\mathrm{FEM\text{-}PBC}}
    }   
$$

对各对角项可以预期：

* 轴向刚度 \(D_{11}\)：差异通常很小；
* 弯曲刚度 \(D_{22},D_{33}\)：取决于横隔稀疏度和弦杆局部弯曲；
* 剪切刚度 \(D_{44},D_{55}\)：可能较敏感；
* 扭转刚度 \(D_{66}\)：通常最值得关注，因为截面翘曲和畸变会显著影响扭转机制。

对于方形对称结构，还应检查：

$$
    D_{22}\approx D_{33}, \qquad D_{44}\approx D_{55}.
$$

---

### 1.4.2 具体边界条件的实现

#### 一、刚性平面模型的推荐实现

对左右端分别设置中心参考节点，并用 `CERIG` 将端部四个角点刚性连接到中心节点。

左端：
$$
    \mathbf q_L = [
        u_{xL}, u_{yL}, u_{zL}, \theta_{xL},\theta_{yL},\theta_{zL}
    ]^{\mathrm T}
$$

右端：

$$
    \mathbf q_R = [
        u_{xR}, u_{yR}, u_{zR}, \theta_{xR}, \theta_{yR}, \theta_{zR}
    ]^{\mathrm T}
$$

固定左端参考节点：

$$
    \mathbf q_L = \mathbf 0
$$

在右端施加：

$$
    \mathbf q_R  -\mathbf q_L = L \begin{bmatrix}
        \varepsilon_x, \gamma_{xy}, \gamma_{xz},
        \kappa_x, \kappa_y, \kappa_z
    \end{bmatrix},
$$

按照你的实际自由度顺序实施即可。

由于端面刚性关系会自动生成角点轴向位移：

$$
    u_{x,k} = u_{x,c} + z_k \theta_y - y_k \theta_z
$$

所以无需再给各角点单独施加弯曲位移差。

---

#### 二、自由桁架模型的推荐实现

这里建议采用真正的周期边界条件，而不是简单地“左端自由、右端加载”。

对每对左右端对应节点设置：

$$
    u_{x,R}^{(k)} - u_{x,L}^{(k)} = L (\varepsilon_x + z_k \kappa_y - y_k \kappa_z), \\
    u_{y,R}^{(k)} - u_{y,L}^{(k)} = L \gamma_{xy} - z_k L \kappa_x, \\
    u_{z,R}^{(k)} - u_{z,L}^{(k)} = L \gamma_{xz} + y_k L \kappa_x,\\
    \theta_{x,R}^{(k)} - \theta_{x,L}^{(k)} = L \kappa_x, \\
    \theta_{y,R}^{(k)} - \theta_{y,L}^{(k)} = L \kappa_y,\\
    \theta_{z,R}^{(k)} - \theta_{z,L}^{(k)} = L \kappa_z.
$$

然后只使用适当的最小约束排除整体刚体运动。

---

### 1.4.4 工况安排

对每个 (n) 和每个刚度分量，表格可以这样组织：

| 参数      | 理论模型 | FEM-RP | 模型误差 | FEM-PBC | 平截面误差 | 总误差 |
| -------- | ---: | -----: | ---: | ------: | ----: | --: |
| $D_{11}$ |      |        |      |         |       |     |
| $D_{22}$ |      |        |      |         |       |     |
| $D_{33}$ |      |        |      |         |       |     |
| $D_{44}$ |      |        |      |         |       |     |
| $D_{55}$ |      |        |      |         |       |     |
| $D_{66}$ |      |        |      |         |       |     |

其中：

$$
    e^{\mathrm{model}} = \frac{D^{\mathrm{theory}} - D^{\mathrm{RP}}}{D^{\mathrm{RP}}}, \\
    e^{\mathrm{plane}} = \frac{D^{\mathrm{RP}} - D^{\mathrm{PBC}}}{D^{\mathrm{PBC}}}, \\
    e^{\mathrm{total}} = \frac{D^{\mathrm{theory}} - D^{\mathrm{PBC}}}{D^{\mathrm{PBC}}}.
$$

论文主文未必需要列出所有 (n) 的完整大表，可以用曲线展示：

$$
    e_i^{\mathrm{model}}(n),\qquad
    e_i^{\mathrm{plane}}(n),\qquad
    e_i^{\mathrm{total}}(n).
$$

---

### 1.16 对你当前程序的阶段性判断


## 后续真正需要重点检查之处

接下来不是公式本身，而是有限元实现层面：

1. 每个截面平面都设置 RBE3 是否改变了原桁架的真实变形模式；
2. 当前刚体位移和刚体转动约束是否足够且不过约束；
3. 周期约束中的节点转角条件是否适用于 `LINK180` 与 `BEAM188` 混合模型；
4. 横隔密度减半与刚度计算本身无关，但模型中的共享横隔刚度是否重复或正确归属；
5. `SENE` 求和是否完整包含所有需要计入的构件应变能。

其中第一点尤其关键：**如果每一个中间节点平面都通过 RBE3 强制为刚性截面，那么你识别到的可能不是自由离散桁架的等效刚度，而是附加了刚性横截面约束后的刚度。**这需要下一步仔细审查 `RBE3` 的实际约束效果和你的建模意图。


---

## 1.5 `ANSYS`实现细节

### 1.5.1 `RBE3`（分布式约束 / 加权平均约束）

#### ✔ 基本原理

RBE3 = **柔性分配约束（不引入刚体）**

核心思想：

> 主节点运动 = 从节点运动的加权平均

$$
    u_m = \sum w_i u_i
$$

但关键点：

* 不强制 slave 之间刚性连接
* 不提高结构刚度
* 主要用于“载荷/惯性分配”

---

#### ✔ 作用

* 载荷分布（force/moment distribution）
* 建立“等效参考点”
* 模拟 remote point（柔性）

---

#### ✔ APDL用法

```apdl
RBE3, master, DOF, slave_nodes
```

或（简化理解）：

```apdl
RBE3,1000,UX,ALL_SLAVES
```

---

#### ✔ 特点

* ❗ 不形成刚体
* ❗ 不增加结构刚度（很关键）
* ✔ 只“传递力/运动平均”
* ✔ 更接近“柔性连接”

### 1.5.2 `CERIG`（Rigid Region，刚性区域）

#### ✔ 基本原理

CERIG = **刚性多点约束（强约束）**

核心假设：

> 一组从节点严格跟随主节点的刚体运动

数学关系：

$$
    \mathbf u_i = \mathbf u_m + \boldsymbol\theta_m \times \mathbf r_i
$$

* 主节点：master
* 从节点：slaves
* 刚性约束（无限刚）

---

#### ✔ 作用

* 构造刚性端板 / 刚性截面
* 模拟 rigid link / rigid body
* 强制“平截面”

---

#### ✔ APDL用法

```apdl
CERIG, master_node, slave_set, DOF
```

例如：

```apdl
CERIG,1000,ALL
```

---

#### ✔ 特点

* **刚性约束（不允许变形）**
* 等价于“无限刚的梁/板”
* 会增加体系刚度
* 适合“刚性端面”“刚性加载板”

---

### 1.5.3 `CE`（Constraint Equation，约束方程）

#### ✔ 基本原理

CE 是**最通用的多点约束表达形式**，本质是一条线性方程：

$$
    \sum_i a_i , u_i = c
$$

* \(u_i\)：各节点自由度（`UX, UY, ROTX` 等）
* \(a_i\)：系数
* \(c\)：常数项

👉 本质：**手工确定“自由度之间的线性关系”**

---

#### ✔ 作用

* 任意多节点自由度耦合
* 定义复杂运动学关系（比如你的周期边界）
* 可以精确控制每个 DOF 的关系

---

#### ✔ APDL用法

```apdl
CE, EID, NODE1, DOF1, C1, NODE2, DOF2, C2, ..., CONSTANT
```

例子：

```apdl
CE,1,10,UX,1,20,UX,-1,0
```

表示：
$$
    u_{10} - u_{20} = 0
$$

---

#### ✔ 特点

* 最“数学化”
* 最灵活
* 但需要自己写关系式
* 不自动分配刚度

---

### 1.5.4 三者核心区别

| 方法    | 本质     | 是否刚性 | 是否影响刚度  | 典型用途                |
| ----- | ------ | ---- | ------- | ------------------- |
| CE    | 手写线性方程 | 不一定  | 视情况     | 周期边界 / 精确约束         |
| CERIG | 刚体运动约束 | ✔ 是  | ✔ 增强刚度  | 刚性端板 / rigid截面      |
| RBE3  | 加权平均传递 | ✘ 否  | ✘ 不增强刚度 | 载荷分配 / remote point |

---

### 1.5.5 和当前研究的直接关联

#### （1）CE → 周期边界（你的主力工具）

用于施加广义应变：

$$
    u_R - u_L = \Delta u(\alpha)
$$

👉 用来构造：

* 周期单元
* 广义应变加载
* 能量识别


---

#### （2）CERIG → 两端刚性平截面模型（RP模型）

用于构造端部平截面假定：

* 两端截面不允许翘曲
* 完全符合“梁假设”

👉 对应：

> Euler-Bernoulli / Timoshenko 假设验证

---

#### （3）RBE3 → 真实桁架“自由截面行为”

用于提供端部约束：

* 让节点自由变形
* 只提供参考点
* 不强制平截面

👉 对应：

> PBC（周期均质化）或“真实结构松弛状态”

---

 # 2. 截面惯性参数计算

---

## 2.1 惯性参数的本质

在连续体力学里，惯性不是一个“单个数”，而是一个**二阶张量结构**：

- 质量（标量）
$$
    m = \int_V \rho , dV
$$

- 质心
$$
    \mathbf r_c = \frac{1}{m} \int_V \rho \mathbf r , dV
$$

- 惯性张量 (关于质心)：
$$
    \mathbf I = \int_V \rho \left[
        (\mathbf r\cdot \mathbf r)\mathbf I_3 - \mathbf r \otimes \mathbf r
    \right] dV
$$

展开就是：
$$
    \mathbf I = \begin{bmatrix}
         I_{xx} & -I_{xy} & -I_{xz} \\
        -I_{yx} & I_{yy} & -I_{yz} \\
        -I_{zx} & -I_{zy} & I_{zz}
    \end{bmatrix}
$$

- 物理意义一句话
  * 质量：抗平动能力
  * 惯性张量：抗转动能力（绕不同轴“有多难转”）

---

## 2.2 `FEM`中计算惯性参数的原理

ANSYS不会直接做积分，而是：

> 用“单元质量矩阵”拼出整个结构的惯性信息。

核心结构是：

$$
    \mathbf M = \sum_e \mathbf M_e
$$

然后可以分解为：
$$
    \mathbf M = \begin{bmatrix}
        M_t & M_{tr}\\
        M_{rt} & M_r
    \end{bmatrix}
$$

---

### 2.2.1 需要求取的参数

- 平动质量矩阵 $ M_t $

- 转动惯性矩阵 $ M_r \Rightarrow I_{xx}, I_{yy}, I_{zz}, I_{xy}... $

---

### 2.2.2 关键关系

ANSYS理论里：

$$
    \boxed{ \text{惯性参数 = 质量矩阵中“转动自由度部分”} }
$$

也就是说：

* `UX/UY/UZ` → 质量
* `ROTX/ROTY/ROTZ` → 转动惯性

---

### 2.2.3 ANSYS如何计算惯性

#### 2.2.3.1 精确法（3D实体/梁常用）

来源于：
* 单元质量矩阵
* shape function积分

特点：
* 自动考虑转动惯量
* 考虑真实几何分布

文档中就是这一套：

> “Precise calculation uses element mass matrices” ([mm.bme.hu][1])

---

#### 2.2.3.2 集中质量法（lumped）

假设：
* 质量集中在节点
* 转动惯性近似处理

特点：
* 快
* 但可能低估/忽略惯性耦合项

---

## 2.3 ANSYS输出惯性参数的方法

### 2.3.1 输出精确质量

使用`IRLF`命令，可在 `ANSYS` 中输出精确质量汇总：

```apdl
RESUME,cell_n2_base,DB

/SOLU
ANTYPE,STATIC
ALLSEL,ALL

IRLF,-1
PSOLVE,ELFORM
IRLIST

FINISH
```

`IRLF,-1` 配合 `PSOLVE,ELFORM` 和 `IRLIST` 可以输出精确质量汇总，包括：

* 总质量；
* 质心；
* 关于质心和原点的惯性矩；
* 惯性积。([Ansys Help][3])

- 输出的是：$ \boxed{ \text{整体结构刚体惯性（rigid body inertia）} } $， 即
    * 一个“等效刚体”
    * 用于动力学平衡
    * 注意：它和坐标原点位置相关

- 不考虑：
    * CE（约束方程）
    * RBE3
    * CERIG

👉 注意：这里输出的惯性参数与**坐标系**相关，为了和理论推导保持一致，取**周期单元的中心**为坐标
        原点建模


---

### 2.3.2 计算截面惯性参数

上一步中输出的惯性参数是整体结构的惯性参数：
$$
    m_c,\quad I_{xx}^{c},\quad I_{yy}^{c},\quad I_{zz}^{c}.
$$

需要计算单位长度质量：
$$
    \boxed{ \bar m = \frac{m_c}{L_c} }
$$

对于以周期单元质心为参考点的均匀等效梁：
$$
    \boxed{ \bar J_x = \frac{I_{xx}^{c}}{L_c} }
$$

$$
    \boxed{ \bar J_y = \frac{I_{yy}^{c} - m_c L_c^2 / 12}{L_c}}
$$

$$
    \boxed{ \bar J_z = \frac{I_{zz}^{c} - m_c L_c^2 / 12}{L_c}}
$$

其中减去的 \(m_cL_c^2/12\) 是等效梁质量沿轴向分布产生的惯性贡献。

这组参数可以与理论惯性矩阵中的：

* 单位长度质量；
* 扭转质量惯量；
* 两个弯曲质量惯量；

---
