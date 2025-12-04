# -*- coding: utf-8 -*-
"""
数据融合引擎核心模块
实现各种融合策略
"""

import pandas as pd
from typing import List, Tuple, Optional
from collections import Counter
from config.config import CONFIG, FUSION_TYPES, PARAM_RULES
from config.synonyms import MEDICAL_SYNONYMS, NEGATIVE_WORDS
from src.text_processor import TextProcessor
from src.numeric_processor import NumericProcessor


class FusionEngine:
    """数据融合引擎"""
    
    def __init__(self):
        """初始化"""
        self.text_processor = TextProcessor()
        self.numeric_processor = NumericProcessor()
        self.config = CONFIG
        self.param_rules = PARAM_RULES
        self.fusion_stats = {
            'exact_match': 0,
            'high_similarity': 0,
            'semantic_match': 0,
            'numeric_range': 0,
            'unit_conversion': 0,
            'single_supplier': 0,
            'conflict_resolved': 0,
            'manual_review': 0,
            'insufficient_data': 0,
            'medium_similarity': 0,
        }
    
    def process_row(self, parameter_name: str, vendor_data: List) -> Tuple[str, str]:
        """
        处理单行数据
        
        【增强】数字融合优先：
        - 若供应商数据存在数值，则必需优先按数字范围/大小/比较符号判断是否满足衸合参数要求
        
        Args:
            parameter_name: A列技术参数名称
            vendor_data: B~n列供应商数据列表
            
        Returns:
            (融合数据, 融合类型)
        """
        # 1. 数据清洗 - 移除空值和无效数据
        # 注意: 空值不做预处理，不做融合处理
        valid_data = []
        for x in vendor_data:
            # 空值或无效数据不添加到valid_data
            if pd.notna(x) and str(x).strip() and str(x).strip() not in NEGATIVE_WORDS:
                valid_data.append(str(x).strip())
        
        # 2. 检查数据充足性
        if len(valid_data) == 0:
            self.fusion_stats['insufficient_data'] += 1
            return "无有效数据", FUSION_TYPES['insufficient_data']
        elif len(valid_data) == 1:
            self.fusion_stats['single_supplier'] += 1
            # 【新增】统一比较符号
            result = self._normalize_comparison_operators(valid_data[0])
            return result, FUSION_TYPES['single_supplier']
        
        # 3. 按优先级尝试融合
        # 数字融合优先于文本相似度融合
        # 精确匹配
        result, fusion_type = self.try_exact_match(valid_data)
        if result:
            self.fusion_stats['exact_match'] += 1
            # 【新增】统一比较符号
            result = self._normalize_comparison_operators(result)
            return result, fusion_type
        
        # ... existing code ...
        # 数字融合比文本相似度融合优先级高
        if self.config['unit_conversion']:
            all_have_numbers = all(self.numeric_processor.is_numeric(d) for d in valid_data)
            # 检查是否包含型号关键词（如i5、RTX、第12代等）
            has_model_keyword = any(self.numeric_processor.has_model_keywords(d) for d in valid_data)
            # 【新增】检查是否是尺寸规格类参数（如280mm×240mm等）
            is_dimension = any(self.numeric_processor.is_dimension_specification(d) for d in valid_data)
            # 【新增】检查是否是误差范围/容差（如±5%等）
            is_tolerance = any(self.numeric_processor.is_error_tolerance(d) for d in valid_data)
            
            # 【修改】只有参数名称包含"误差"时，才进行误差融合
            if is_tolerance and '误差' in parameter_name:
                result, fusion_type = self._try_tolerance_fusion(valid_data)
                if result:
                    return result, fusion_type
            
            if all_have_numbers and not has_model_keyword and not is_dimension and not is_tolerance:
                # 数据都是数字，且不包含型号、不是尺寸规格，才适合数字融合
                result, fusion_type = self.try_numeric_fusion(valid_data, parameter_name)
                if result:
                    # 【新增】统一比较符号
                    result = self._normalize_comparison_operators(result)
                    if '范围' in fusion_type:
                        self.fusion_stats['numeric_range'] += 1
                    else:
                        self.fusion_stats['unit_conversion'] += 1
                    return result, fusion_type
        # ... existing code ...
        
        # 高相似度融合
        result, fusion_type = self.try_similarity_fusion(valid_data, threshold=self.config['similarity_threshold'])
        if result:
            self.fusion_stats['high_similarity'] += 1
            # 【新增】统一比较符号
            result = self._normalize_comparison_operators(result)
            return result, fusion_type
        
        # 中等相似度融合
        result, fusion_type = self.try_similarity_fusion(valid_data, threshold=self.config['medium_similarity_threshold'])
        if result:
            self.fusion_stats['medium_similarity'] += 1
            # 【新增】统一比较筦号
            result = self._normalize_comparison_operators(result)
            return result, FUSION_TYPES['medium_similarity']
        
        # 语义匙配
        if self.config['semantic_matching']:
            result, fusion_type = self.try_semantic_fusion(valid_data, parameter_name)
            if result:
                self.fusion_stats['semantic_match'] += 1
                # 【新增】统一比较符号
                result = self._normalize_comparison_operators(result)
                return result, fusion_type
        
        # 4. 无法自动融合的情况
        result = self.handle_conflict(valid_data)
        self.fusion_stats['manual_review'] += 1
        return result, FUSION_TYPES['manual_review']
    
    def _try_tolerance_fusion(self, data: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        误差类参数融合：取最大误差值
        
        例如：
        - ±10%、±5%、±10% -> ≤±10%
        - 误差不超过±10%、≤10% -> ≤±10%
        
        Args:
            data: 供应商数据列表
            
        Returns:
            (融合结果, 融合类型) 或 (None, None)
        """
        import re
        
        max_error_val = None
        max_unit = '%'  # 默认单位
        
        for val in data:
            if pd.isna(val) or str(val).strip() == '':
                continue
            val_str = str(val).strip()
            
            # 提取误差值：匹配±数字或数字%
            # 模式1: ±数字%
            pattern1 = r'[±\+\-/]+\s*(\d+\.?\d*)\s*(%|dB|db|\u2103|°C)?'
            # 模式2: ≤±数字%
            pattern2 = r'[≤<]\s*[±\+\-/]*\s*(\d+\.?\d*)\s*(%|dB|db|\u2103|°C)?'
            # 模式3: 误差不超过数字%
            pattern3 = r'误差[^±\d]*[±]*\s*(\d+\.?\d*)\s*(%|dB|db|\u2103|°C)?'
            
            for pattern in [pattern1, pattern2, pattern3]:
                matches = re.findall(pattern, val_str, re.IGNORECASE)
                for match in matches:
                    try:
                        error_val = float(match[0])
                        unit = match[1] if len(match) > 1 and match[1] else '%'
                        if max_error_val is None or error_val > max_error_val:
                            max_error_val = error_val
                            max_unit = unit
                    except (ValueError, IndexError):
                        continue
        
        if max_error_val is not None:
            # 格式化结果：≤±最大值单位
            result = f"≤±{max_error_val:g}{max_unit}"
            return result, '误差融合'
        
        return None, None
    
    def try_exact_match(self, data: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        尝试精确匹配融合
        
        Args:
            data: 数据列表
            
        Returns:
            (融合结果, 融合类型) 或 (None, None)
        """
        # 标准化处理
        normalized = []
        for text in data:
            norm_text = self.text_processor.normalize_text(text)
            # 移除标点符号后的文本
            no_punct = self.text_processor.remove_punctuation(norm_text)
            normalized.append(no_punct)
        
        # 统计出现次数
        counter = Counter(normalized)
        most_common = counter.most_common(1)[0]
        
        # 至少两个相同
        if most_common[1] >= 2:
            # 返回原始文本（保持格式）
            original_index = normalized.index(most_common[0])
            return data[original_index], FUSION_TYPES['exact_match']
        
        return None, None
    
    def try_similarity_fusion(self, data: List[str], threshold: float = 0.8) -> Tuple[Optional[str], Optional[str]]:
        """
        尝试相似度融合
        
        Args:
            data: 数据列表
            threshold: 相似度阈值 (0-1)
            
        Returns:
            (融合结果, 融合类型) 或 (None, None)
        """
        threshold_percent = threshold * 100
        
        # 计算所有配对的相似度
        similar_groups = []
        used_indices = set()
        
        for i in range(len(data)):
            if i in used_indices:
                continue
            
            current_group = [i]
            for j in range(i + 1, len(data)):
                if j in used_indices:
                    continue
                
                # 使用多种相似度算法取最高值
                similarity_fuzz = self.text_processor.calculate_similarity(data[i], data[j], 'fuzz')
                similarity_token_sort = self.text_processor.calculate_similarity(data[i], data[j], 'token_sort')
                similarity_token_set = self.text_processor.calculate_similarity(data[i], data[j], 'token_set')
                
                max_similarity = max(similarity_fuzz, similarity_token_sort, similarity_token_set)
                
                if max_similarity >= threshold_percent:
                    current_group.append(j)
                    used_indices.add(j)
            
            if len(current_group) >= 2:
                similar_groups.append(current_group)
                used_indices.update(current_group)
        
        # 找到最大的相似组
        if similar_groups:
            largest_group = max(similar_groups, key=len)
            # 返回该组中第一个元素
            return data[largest_group[0]], FUSION_TYPES['high_similarity']
        
        return None, None
    
    def try_semantic_fusion(self, data: List[str], parameter_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        尝试语义匹配融合
        
        Args:
            data: 数据列表
            parameter_name: 参数名称
            
        Returns:
            (融合结果, 融合类型) 或 (None, None)
        """
        # 检查参数名称是否在同义词库中
        synonyms = None
        for key, values in MEDICAL_SYNONYMS.items():
            if key in parameter_name or parameter_name in values:
                synonyms = [key] + values
                break
        
        if not synonyms:
            return None, None
        
        # 检查数据中是否有匹配同义词的
        matched_items = []
        for item in data:
            for synonym in synonyms:
                if synonym in item:
                    matched_items.append(item)
                    break
        
        if len(matched_items) >= 2:
            # 选择最常见的
            counter = Counter(matched_items)
            most_common = counter.most_common(1)[0]
            return most_common[0], FUSION_TYPES['semantic_match']
        
        # 尝试关键词匹配
        for item in data:
            item_keywords = self.text_processor.extract_keywords(item)
            if self.text_processor.has_keyword(parameter_name, item_keywords):
                return item, FUSION_TYPES['semantic_match']
        
        return None, None
    
    def try_numeric_fusion(self, data: List[str], parameter_name: str = '') -> Tuple[Optional[str], Optional[str]]:
        """
        尝试数字参数融合
        
        根据数字后面的单位进行匹配：
        - 单位相同的数字进行融合
        - 单位不同的数字按最大数据量融合（余下数据需人工审查）
        
        Args:
            data: 数据列表
            parameter_name: 参数名称
            
        Returns:
            (融合结果, 融合类型) 或 (None, None)
        """
        # 第一步：过滤掉不相关的数据
        relevant_data = []
        for d in data:
            if self.numeric_processor.is_relevant_data(d, parameter_name):
                relevant_data.append(d)
        
        # 如果没有相关数据，返回失败
        if not relevant_data:
            return None, None
        
        # 第二步：提取每条数据的数字和单位信息
        data_with_units = []
        for d in relevant_data:
            numeric_info = self.numeric_processor.extract_numeric_info(d)
            if numeric_info:
                # 为每条数据存储其数字和单位信息
                data_with_units.append({
                    'original': d,
                    'numeric_info': numeric_info
                })
        
        if not data_with_units:
            return None, None
        
        # 第三步：全局检查每个供应商的单位是否兼容
        # 规则：
        # 1. 单位一致或都为空：可以融合
        # 2. 存在不同的非空单位但可以转换（如W和kW）：可以融合
        # 3. 存在不同的非空单位且无法转换：拒绝融合（不能混淆Hz和s、%和s等）
        all_non_empty_units = set()
        for item in data_with_units:
            units_in_item = [n['unit'].lower() for n in item['numeric_info'] if n['unit']]
            all_non_empty_units.update(units_in_item)
        
        # 检查是否存在不同的非空单位
        if len(all_non_empty_units) > 1:
            # 存在多个不同的非空单位，尝试判断是否可转换
            # 例如：w 和 kw 可以相互转换
            first_unit = list(all_non_empty_units)[0]
            units_compatible = True
            for unit in list(all_non_empty_units)[1:]:
                # 尝试单位转换
                converted = self.numeric_processor.convert_unit(1.0, unit, first_unit)
                if converted is None:
                    # 无法转换，说明是不同的物理量，拒绝融合
                    units_compatible = False
                    break
            
            if not units_compatible:
                return None, None
        
        # 按单位分组数据
        unit_groups = {}
        for item in data_with_units:
            # 从第一个数字信息中提取单位
            unit = item['numeric_info'][0]['unit'] if item['numeric_info'] else ''
            # ... existing code ...
            unit_key = unit.lower()  # 小写化作为key，以处理W和kW的大小写差异
            if unit_key not in unit_groups:
                unit_groups[unit_key] = []
            unit_groups[unit_key].append(item['original'])
        
        # 第五步：融合
        if len(unit_groups) == 1:
            # 单位一致，仅有一类数据
            unit_data = list(unit_groups.values())[0]
            
            # 整数值融合
            result, fusion_type = self.numeric_processor.merge_numeric_values(unit_data, parameter_name)
            
            if result:
                return result, fusion_type
        else:
            # 单位不一致：如果所有供应商都有不同的单位，则拒绝融合
            # 这样可以避免混淆 Hz 和 s（频率和时间）等不同物理量
            if len(unit_groups) == len(data_with_units):
                # 每个供应商都是不同的单位，无法融合
                return None, None
            
            # 如果部分供应商单位相同，则融合单位相同的数据
            largest_unit = max(unit_groups.keys(), key=lambda u: len(unit_groups[u]))
            largest_unit_data = unit_groups[largest_unit]
            
            if len(largest_unit_data) >= 2:
                # 对数据量最多的单位组进行融合
                result, fusion_type = self.numeric_processor.merge_numeric_values(largest_unit_data, parameter_name)
                
                if result:
                    return result, fusion_type
        
        return None, None
    
    def handle_conflict(self, data: List[str]) -> str:
        """
        处理冲突情况
        
        Args:
            data: 数据列表
            
        Returns:
            处理结果
        """
        method = self.config.get('conflict_resolution_method', 'majority')
        
        if method == 'first':
            # 使用第一个值
            return data[0]
        elif method == 'majority':
            # 使用出现最多的值
            counter = Counter(data)
            most_common = counter.most_common(1)[0]
            if most_common[1] >= 2:
                return most_common[0]
            # 如果没有多数，返回第一个供应商的数据（需人工审核）
            return data[0]
        else:
            # 手动审核 - 返回第一个供应商的数据
            return data[0]
    
    def get_statistics(self) -> dict:
        """
        获取融合统计信息
        
        Returns:
            统计字典
        """
        total = sum(self.fusion_stats.values())
        stats_with_percent = {}
        
        for key, value in self.fusion_stats.items():
            percent = (value / total * 100) if total > 0 else 0
            stats_with_percent[FUSION_TYPES.get(key, key)] = {
                'count': value,
                'percent': round(percent, 2)
            }
        
        return stats_with_percent
    
    def reset_statistics(self):
        """重置统计信息"""
        for key in self.fusion_stats:
            self.fusion_stats[key] = 0
    
    def _normalize_comparison_operators(self, text: str) -> str:
        """
        【新增】统一比较符号：将 > < 等符号替换为 ≥ ≤
        
        Args:
            text: 原始文本
            
        Returns:
            替换后的文本
        """
        if not text:
            return text
        
        result = str(text)
        
        # 替换比较符号：> → ≥，< → ≤
        # 注意：保留已经是≥、≤的符号
        # 处理全角符号
        result = result.replace('＞=', '≥')  # ＞= → ≥
        result = result.replace('＜=', '≤')  # ＜= → ≤
        result = result.replace('＞', '≥')   # ＞ → ≥
        result = result.replace('＜', '≤')   # ＜ → ≤
        
        # 处理半角符号
        result = result.replace('>=', '≥')  # >= → ≥
        result = result.replace('<=', '≤')  # <= → ≤
        result = result.replace('>', '≥')   # > → ≥
        result = result.replace('<', '≤')   # < → ≤
        
        return result
    
    def get_rule_for_parameter(self, param_name: str) -> dict:
        """
        【新增】获取参数对应的融合规则
        
        Args:
            param_name: 参数名称
            
        Returns:
            规则字典
        """
        # 精确匹配
        if param_name in self.param_rules:
            return self.param_rules[param_name]
        
        # 模糊匹配
        for key in self.param_rules:
            if key in param_name or param_name in key:
                return self.param_rules[key]
        
        # 默认规则
        return {'type': 'auto'}
