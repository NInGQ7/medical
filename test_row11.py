import sys
import pandas as pd
sys.path.insert(0, '.')
from src.numeric_processor import NumericProcessor

# 读取第11行的数据
df = pd.read_excel("E:/LXL/云采鏞工作/EXCEL/python参数融合数据/便携式彩色多普勒超声系统.xlsx")

print("\n所有参数:")
for i, row_data in df.iterrows():
    print(f"  Row {i+2}: {row_data.get('参数名称')}")

row = df.iloc[10]  # 第11行（0-indexed）

param_name = row['参数名称']
print(f"参数名称: {param_name}")
print(f"\n供应商数据:")
for col in df.columns[2:7]:
    value = row[col]
    if pd.notna(value):
        print(f"  {col}: {value}")

# 测试is_relevant_data
np = NumericProcessor()
print(f"\n相关性检测:")
for col in df.columns[2:7]:
    value = row[col]
    if pd.notna(value):
        is_rel = np.is_relevant_data(str(value), param_name)
        print(f"  {col}: {is_rel}")
