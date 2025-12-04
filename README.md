

## 主要功能

### 融合模式
- **精确匹配融合**: 标准化处理后完全相同的数据
- **高相似度融合**: 使用多种相似度算法（Fuzz、Token Sort、Token Set）
- **中等相似度融合**: 适用于部分相似的数据（相似度≥60%）
- **语义匹配融合**: 基于医疗领域同义词库的语义理解
- **数字范围融合**: 自动创建数值范围，支持单位转换
- **误差结构融合**: 针对含±符号的误差数据，采用最大数值



### 环境要求
- Python 3.7+
- 依赖包：pandas, openpyxl, fuzzywuzzy, jieba


### 运行方式

#### 方式1: 命令行模式
```bash
python main.py input.xlsx
```

#### 方式2: GUI图形界面
```bash
python gui_app.py
```
或直接双击 `启动GUI.bat`

## 项目结构

```
medical-device-fusion/
├── config/               # 配置文件
│   ├── config.py        # 主配置和参数规则(PARAM_RULES)
│   └── synonyms.py      # 医疗领域同义词库
├── src/                 # 核心代码
│   ├── fusion_engine.py           # 融合引擎
│   ├── numeric_processor.py       # 数字处理器
│   ├── text_processor.py          # 文本处理器
│   └── parameter_preprocessor.py  # 参数预处理器
├── main.py              # 命令行主程序
├── gui_app.py           # GUI图形界面
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明
```

## 输入格式

Excel文件格式：
- **第1列**: 技术参数名称
- **第2列及以后**: 各供应商数据

## 输出格式

系统会在输入文件同目录生成融合结果Excel文件，包含：
- **说明行**: 颜色说明和注意事项（黄色背景、加粗、14磅字体）
- **原始列**: 保留所有原始供应商数据
- **融合数据列**: 智能融合后的结果
- **融合类型列**: 使用的融合策略（后续正式使用将删除）
- **合并数据列**: 所有参数融合结果汇总
- **颜色标记**: 
  - 蓝色=供应商数据较接近融合数据
  - 灰色=供应商无数据
  - 黄色=需人工审核




