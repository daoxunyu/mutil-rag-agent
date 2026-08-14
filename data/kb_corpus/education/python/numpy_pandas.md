# NumPy 与 Pandas 数据处理

## 1. NumPy 核心

NumPy 是 Python 科学计算的基础库，核心是 ndarray（N维数组对象）。

### 数组创建
```python
import numpy as np

a = np.array([1, 2, 3, 4])                    # 从列表创建
b = np.zeros((3, 4))                            # 全零矩阵
c = np.ones((2, 3))                             # 全一矩阵
d = np.arange(0, 10, 2)                         # 等差数列 [0,2,4,6,8]
e = np.linspace(0, 1, 5)                        # 等间距 [0., 0.25, 0.5, 0.75, 1.]
f = np.random.randn(100)                        # 标准正态分布
g = np.random.randint(0, 10, size=(3, 3))       # 随机整数矩阵
```

### 数组运算（向量化）
```python
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
a + b      # [5, 7, 9]
a * b      # [4, 10, 18] (逐元素)
a @ b      # 32 (点积)
np.dot(a, b) # 同 @
a.mean()   # 平均值
a.std()    # 标准差
a.sum()    # 求和
```

### 索引与切片
```python
a = np.arange(12).reshape(3, 4)
a[0, 0]         # 单个元素
a[:, 1]         # 第二列
a[0:2, 1:3]     # 子矩阵
a[a > 5]        # 布尔索引
a[(a > 3) & (a < 8)]  # 组合条件
```

## 2. Pandas 核心

Pandas 提供 DataFrame 和 Series，专为表格数据处理设计。

### Series 与 DataFrame
```python
import pandas as pd

# Series: 一维带标签数组
s = pd.Series([0.1, 0.2, 0.3], index=['a', 'b', 'c'])

# DataFrame: 二维表格
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [20, 21, 19],
    'score': [88.5, 92.0, 76.3],
    'major': ['CS', 'Math', 'CS']
})
```

### 数据操作
```python
# 查看
df.head(3)           # 前3行
df.describe()         # 统计摘要
df.info()             # 列信息
df['score'].mean()    # 某列平均值
df.groupby('major')['score'].mean()  # 按专业分组求平均分

# 筛选
df[df['score'] > 80]                    # 分数>80
df[(df['major'] == 'CS') & (df['age'] >= 20)]  # CS专业且>=20岁
df.sort_values('score', ascending=False)  # 按分数降序

# 增删改
df['passed'] = df['score'] >= 60       # 新增列
df.drop('passed', axis=1)              # 删除列
df.rename(columns={'score': 'grade'})  # 重命名列
```

### 处理缺失值
```python
df.isnull().sum()           # 统计缺失值
df.dropna()                 # 删除含缺失值的行
df.fillna(0)                # 用0填充
df.fillna(df.mean())        # 用均值填充
```

### 数据合并
```python
pd.concat([df1, df2])               # 纵向拼接
pd.merge(df1, df2, on='student_id') # 按key横向合并（类似SQL JOIN）
```
