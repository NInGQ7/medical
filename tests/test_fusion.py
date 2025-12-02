# -*- coding: utf-8 -*-
"""
测试文件 - 测试融合功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fusion_engine import FusionEngine
from src.text_processor import TextProcessor
from src.numeric_processor import NumericProcessor


def test_exact_match():
    """测试精确匹配"""
    print("\n=== 测试精确匹配 ===")
    engine = FusionEngine()
    
    # 测试用例1: 完全相同
    data = ["1920x1080", "1920x1080", "1920x1080"]
    result, fusion_type = engine.try_exact_match(data)
    print(f"输入: {data}")
    print(f"结果: {result}, 类型: {fusion_type}")
    
    # 测试用例2: 忽略大小写和标点
    data = ["High Speed", "high-speed", "HIGH SPEED"]
    result, fusion_type = engine.try_exact_match(data)
    print(f"\n输入: {data}")
    print(f"结果: {result}, 类型: {fusion_type}")


def test_similarity_fusion():
    """测试相似度融合"""
    print("\n=== 测试相似度融合 ===")
    engine = FusionEngine()
    
    # 测试用例: 高相似度
    data = ["高精度测量", "高精度", "精度高"]
    result, fusion_type = engine.try_similarity_fusion(data, threshold=0.6)
    print(f"输入: {data}")
    print(f"结果: {result}, 类型: {fusion_type}")


def test_numeric_fusion():
    """测试数字融合"""
    print("\n=== 测试数字融合 ===")
    engine = FusionEngine()
    
    # 测试用例1: 范围融合
    data = ["5m/s", "10m/s", "8m/s"]
    result, fusion_type = engine.try_numeric_fusion(data, "扫描速度")
    print(f"输入: {data}")
    print(f"结果: {result}, 类型: {fusion_type}")
    
    # 测试用例2: 单位转换
    data = ["5kg", "5000g", "5公斤"]
    result, fusion_type = engine.try_numeric_fusion(data, "设备重量")
    print(f"\n输入: {data}")
    print(f"结果: {result}, 类型: {fusion_type}")


def test_text_processor():
    """测试文本处理器"""
    print("\n=== 测试文本处理器 ===")
    processor = TextProcessor()
    
    # 测试相似度计算
    text1 = "最大分辨率"
    text2 = "最高分辨率"
    similarity = processor.calculate_similarity(text1, text2)
    print(f"'{text1}' vs '{text2}' 相似度: {similarity}%")
    
    # 测试标准化
    text = "  High-Speed  Scanning  "
    normalized = processor.normalize_text(text)
    print(f"\n原文: '{text}'")
    print(f"标准化: '{normalized}'")


def test_numeric_processor():
    """测试数字处理器"""
    print("\n=== 测试数字处理器 ===")
    processor = NumericProcessor()
    
    # 测试数字提取
    text = "尺寸: 100mm x 50mm"
    numeric_info = processor.extract_numeric_info(text)
    print(f"文本: {text}")
    print(f"提取结果: {numeric_info}")
    
    # 测试单位转换
    value = 5
    from_unit = "kg"
    to_unit = "g"
    converted = processor.convert_unit(value, from_unit, to_unit)
    print(f"\n单位转换: {value}{from_unit} = {converted}{to_unit}")
    
    # 测试范围提取
    text = "温度范围: 5℃ 至 50℃"
    range_info = processor.extract_range(text)
    print(f"\n文本: {text}")
    print(f"范围: {range_info}")


def test_full_process():
    """测试完整流程"""
    print("\n=== 测试完整处理流程 ===")
    engine = FusionEngine()
    
    test_cases = [
        ("最大分辨率", ["1920x1080", "1920x1080像素", "1920*1080"]),
        ("扫描速度", ["5m/s", "10m/s", "8m/s"]),
        ("设备重量", ["5kg", "5000g", "5公斤"]),
        ("测量精度", ["高精度", "精确度高", "精度优秀"]),
        ("工作电压", ["220V", "-", "-"]),
        ("响应时间", ["快速", "慢速", "中等"]),
    ]
    
    for param_name, vendor_data in test_cases:
        result, fusion_type = engine.process_row(param_name, vendor_data)
        print(f"\n参数: {param_name}")
        print(f"供应商数据: {vendor_data}")
        print(f"融合结果: {result}")
        print(f"融合类型: {fusion_type}")


if __name__ == '__main__':
    print("="*60)
    print("医疗设备数据融合功能测试")
    print("="*60)
    
    test_exact_match()
    test_similarity_fusion()
    test_numeric_fusion()
    test_text_processor()
    test_numeric_processor()
    test_full_process()
    
    print("\n" + "="*60)
    print("所有测试完成!")
    print("="*60)
