# Python 编程基础

## 1. Python 概述

Python 是解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年发布。特点：简洁易读、跨平台、丰富的标准库和第三方库。

## 2. 数据类型

### 基本类型
- **int**: 整数，Python 3 中整数无上限
- **float**: 浮点数，双精度
- **bool**: 布尔值 True/False
- **str**: 字符串，不可变序列
- **None**: 空值

### 容器类型
- **list**: 有序可变序列 `[1, 2, 3]`
- **tuple**: 有序不可变序列 `(1, 2, 3)`
- **dict**: 键值对映射 `{'a': 1, 'b': 2}`
- **set**: 无序不重复集合 `{1, 2, 3}`

## 3. 函数与类

```python
def greet(name: str, greeting: str = "Hello") -> str:
    """返回问候语"""
    return f"{greeting}, {name}!"

class Student:
    def __init__(self, name: str, grade: int):
        self.name = name
        self.grade = grade
        self.courses = []

    def enroll(self, course: str) -> None:
        self.courses.append(course)

    @property
    def gpa(self) -> float:
        return sum(c.score for c in self.courses) / len(self.courses) if self.courses else 0.0
```

## 4. 常用标准库

| 库 | 用途 |
|----|------|
| os / pathlib | 文件和路径操作 |
| json / csv | 数据序列化 |
| collections | Counter, defaultdict, deque 等 |
| itertools | 迭代器工具 |
| functools | 高阶函数 (reduce, partial, lru_cache) |
| typing | 类型提示 |

## 5. 列表推导式

```python
# 基本语法: [expression for item in iterable if condition]
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
matrix = [[i*j for j in range(5)] for i in range(5)]
```

## 6. 异常处理

```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
except (ValueError, TypeError) as e:
    print(f"Type/Value error: {e}")
else:
    print(f"Result: {result}")
finally:
    print("Always executed")
```
