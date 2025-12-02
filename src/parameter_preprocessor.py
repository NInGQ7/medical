# -*- coding: utf-8 -*-
"""
参数预处理模块
用于在融合前拆分整合参数，防止不同参数的数据混淆
"""

from src.parameter_parser import ParameterParser
from typing import Dict, List, Optional


class ParameterPreprocessor:
    """参数预处理器 - 拆分整合参数"""
    
    def __init__(self):
        """初始化"""
        self.parser = ParameterParser()
        
        # 参数名称与参数类型的映射
        # 注意：参数类型必须与ParameterParser返回的类型完全匹配！
        self.param_type_mapping = {
            'CPU': ['CPU'],  # ParameterParser返回的是'CPU'
            '内存': ['内存'],
            '硬盘': ['存储'],  # ParameterParser返回的是'存储'，不是'硬盘'！
            '存储': ['存储'],  # 也支持用'存储'查询
            '显示器': ['显示器'],
            '显卡': ['显卡'],
            '操作系统': ['操作系统'],
            '电源': ['电源'],
            '散热': ['冷却'],
        }
    
    def is_integrated_params(self, text: str) -> bool:
        """
        判断是否为整合参数
        
        整合参数特征：
        - 包含多个分隔符（逗号、顿号等）
        - 包含多个参数类型的关键词
        
        Args:
            text: 待判断的文本
            
        Returns:
            是否为整合参数
        """
        if not isinstance(text, str):
            return False
        
        # 整合参数通常有多个分隔符
        separator_count = text.count(',') + text.count('，') + text.count('、')
        
        # 如果有2个或以上的分隔符，认为是整合参数
        return separator_count >= 2
    
    def preprocess(self, value: str, parameter_name: str = '') -> str:
        """
        预处理数据 - 如果是整合参数则拆分并提取相关部分
        
        Args:
            value: 原始值
            parameter_name: 参数名称（用于识别相关参数类型）
            
        Returns:
            处理后的值（如果是整合参数则返回相关部分，否则返回原值）
        """
        if not isinstance(value, str) or not value.strip():
            return value
        
        # 检查是否为整合参数
        if not self.is_integrated_params(value):
            # 不是整合参数，直接返回
            return value
        
        # 是整合参数，拆分并提取相关部分
        try:
            parsed = self.parser.parse_integrated_params(value)
            grouped = self.parser.group_by_param_type(parsed)
            
            # 提取相关的参数
            relevant_value = self._extract_relevant_value(grouped, parameter_name)
            
            if relevant_value:
                return relevant_value
            else:
                # 无法找到相关参数，返回原值
                return value
        except Exception as e:
            # 解析失败，返回原值
            print(f"参数预处理出错: {str(e)}", flush=True)
            return value
    
    def _extract_relevant_value(self, grouped_params: Dict, parameter_name: str) -> Optional[str]:
        """
        从分组参数中提取相关的值
        
        Args:
            grouped_params: 按类型分组的参数
            parameter_name: 参数名称
            
        Returns:
            相关参数的内容，或None
        """
        if not parameter_name:
            return None
        
        # 查找对应的参数类型
        target_types = self.param_type_mapping.get(parameter_name, [parameter_name])
        
        for target_type in target_types:
            if target_type in grouped_params:
                items = grouped_params[target_type]
                if items:
                    # 返回第一个相关参数的内容
                    return items[0]['content']
        
        # 尝试模糊匹配
        for target_type in target_types:
            for param_type, items in grouped_params.items():
                if target_type.lower() in param_type.lower() or param_type.lower() in target_type.lower():
                    if items:
                        return items[0]['content']
        
        return None
    
    def preprocess_batch(self, data_list: List[str], parameter_name: str = '') -> List[str]:
        """
        批量预处理数据
        
        Args:
            data_list: 数据列表
            parameter_name: 参数名称
            
        Returns:
            处理后的数据列表
        """
        return [self.preprocess(value, parameter_name) for value in data_list]
