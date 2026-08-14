# 支持向量机 (SVM) 详解

## 1. 核心思想

支持向量机是一种二分类模型，目标是找到一个超平面，使两类样本之间的间隔最大化。

## 2. 数学原理

### 2.1 线性可分情况
- 超平面方程: w^T·x + b = 0
- 函数间隔: γ̂ = y(w^T·x + b)
- 几何间隔: γ = γ̂ / ||w||

### 2.2 优化目标
最大化间隔等价于最小化 ||w||²/2，约束条件: y_i(w^T·x_i + b) ≥ 1

### 2.3 拉格朗日对偶
通过拉格朗日乘子法转化为对偶问题:
- 引入拉格朗日乘子 α_i ≥ 0
- 对偶问题: max Σα_i - ½ΣΣα_iα_j y_i y_j (x_i·x_j)

## 3. 核技巧 (Kernel Trick)

当数据线性不可分时，通过核函数将数据映射到高维空间。

### 常用核函数:
- **线性核**: K(x,z) = x^T·z — 适用于线性可分数据
- **多项式核**: K(x,z) = (γ·x^T·z + r)^d — 适合图像识别
- **RBF/高斯核**: K(x,z) = exp(-γ||x-z||²) — 最常用，适合非线性数据
- **Sigmoid核**: K(x,z) = tanh(γ·x^T·z + r) — 近似神经网络

### 核函数选择指南:
1. 特征数远大于样本数 → 线性核
2. 特征数和样本数都适中 → RBF核
3. 样本数远大于特征数 → 手动添加特征后用线性核

## 4. 软间隔

引入松弛变量 ξ_i 允许少量误分类:
- C 参数控制对误分类的惩罚力度
- C 越大 → 越不愿意容忍误分类 → 容易过拟合
- C 越小 → 更宽松 → 模型更简单

## 5. SVM 优缺点

### 优点:
- 在高维空间表现优秀
- 核技巧处理非线性问题
- 只依赖支持向量，内存效率高
- 理论保证：凸优化有全局最优解

### 缺点:
- 大规模数据训练慢 (O(n²) ~ O(n³))
- 对参数和核函数选择敏感
- 不直接支持多分类（需 OvO/OvR）
- 概率解释不直接（需额外校准）

## 6. Scikit-learn 示例

```python
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

# SVM 对特征尺度敏感，需先标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 网格搜索最佳参数
param_grid = {
    'C': [0.1, 1, 10, 100],
    'gamma': ['scale', 'auto', 0.1, 0.01],
    'kernel': ['rbf', 'linear']
}
svm = SVC()
grid = GridSearchCV(svm, param_grid, cv=5)
grid.fit(X_train_scaled, y_train)
print(f"Best params: {grid.best_params_}")
print(f"Test accuracy: {grid.score(X_test_scaled, y_test):.3f}")
```
