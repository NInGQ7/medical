# -*- coding: utf-8 -*-
"""
配置文件
"""

# 数据融合配置
CONFIG = {
    # 相似度阈值
    'similarity_threshold': 0.8,           # 高相似度阈值
    'medium_similarity_threshold': 0.6,    # 中等相似度阈值
    'text_match_threshold': 0.7,           # 供应商文本判定阈值
    
    # 功能开关
    'unit_conversion': True,               # 单位转换开关
    'enable_chinese_segmentation': True,   # 中文分词
    'numeric_range_format': True,          # 启用数字范围格式
    'semantic_matching': True,             # 语义匹配开关
    
    # 数据处理
    'min_vendor_count': 2,                 # 最小供应商数量
    'ignore_case': True,                   # 忽略大小写
    'ignore_punctuation': True,            # 忽略标点符号
    'ignore_whitespace': True,             # 忽略空格
    
    # 数字处理
    'numeric_precision': 2,                # 数字精度
    'numeric_tolerance': 0.05,             # 数字误差容忍度(5%)
    'enable_unit_normalization': True,     # 单位标准化
    'enable_range_merge': True,            # 范围合并
    
    # 噪声检测
    'noise_detection_enabled': True,       # 启用噪声检测
    'noise_median_ratio': 0.5,             # 噪声阈值（中位数的50%）
    'noise_min_samples': 2,                # 最少样本数
    
    # 性能优化
    'enable_cache': True,                  # 启用缓存
    'cache_size': 1024,                    # 缓存大小
    
    # 输出配置
    'output_log': True,                    # 输出日志
    'output_statistics': True,             # 输出统计信息
    'keep_original_columns': True,         # 保留原始列
    'log_level': 'detailed',               # 日志级别: simple/detailed/debug
    
    # 冲突处理
    'conflict_resolution_method': 'majority',  # 冲突解决方法: majority, first, manual
    'vendor_priority': [],                 # 供应商优先级列表（可选）
}

# 融合类型定义
FUSION_TYPES = {
    'exact_match': '精确匹配',
    'high_similarity': '高相似度融合', 
    'semantic_match': '语义匹配',
    'numeric_range': '数字范围融合',
    'unit_conversion': '单位转换融合',
    'multi_value': '多值融合',
    'single_supplier': '单供应商',
    'conflict_resolved': '冲突解决',
    'manual_review': '需人工审核',
    'insufficient_data': '数据不足',
    'medium_similarity': '中等相似度融合',
}

# 参数名称驱动的融合规则
# 根据参数名称自动选择融合策略
PARAM_RULES = {
    # 数字类参数
    '电池容量': {'type': 'numeric', 'unit': 'mAh', 'allow_range': True, 'tolerance': 0.05},
    '波长': {'type': 'numeric', 'unit': 'nm', 'allow_range': True, 'tolerance': 0.02},
    '功率': {'type': 'numeric', 'unit': 'W', 'allow_range': True, 'tolerance': 0.1},
    '电压': {'type': 'numeric', 'unit': 'V', 'allow_range': False, 'tolerance': 0.05},
    '频率': {'type': 'numeric', 'unit': 'Hz', 'allow_range': True, 'tolerance': 0.05},
    '容量': {'type': 'numeric', 'unit': 'L', 'allow_range': True, 'tolerance': 0.05},
    '重量': {'type': 'numeric', 'unit': 'kg', 'allow_range': True, 'tolerance': 0.1},
    
    # 尺寸类参数（保持整体）
    '尺寸': {'type': 'dimension', 'unit': 'mm', 'allow_range': False},
    '外形尺寸': {'type': 'dimension', 'unit': 'mm', 'allow_range': False},
    
    # 文本类参数
    '探头类型': {'type': 'text', 'similarity_threshold': 0.8},
    '显示屏': {'type': 'text', 'similarity_threshold': 0.7, 'conflict_words': [('彩色', '黑白'), ('触摸', '非触摸')]},
    '材质': {'type': 'text', 'similarity_threshold': 0.75},
    '型号': {'type': 'text', 'similarity_threshold': 0.9},
    
    # 多值类参数
    '接口': {'type': 'multi_value', 'separator': '×', 'keys': ['USB', 'HDMI', 'VGA', '网口'], 'merge_mode': 'max'},
    '附加功能': {'type': 'multi_value', 'separator': '/', 'merge_mode': 'union'},
    '探头': {'type': 'multi_value', 'separator': '/', 'keys': ['A', 'B', 'M', 'CFM'], 'merge_mode': 'union'},
}

# 日志配置
LOG_CONFIG = {
    'log_file': 'output/fusion_log.txt',
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
}
