# -*- coding: utf-8 -*-
"""
数字和单位处理模块
包含数字提取、单位识别、单位转换、范围处理等功能
"""

import re
from typing import List, Tuple, Optional, Dict
from config.synonyms import MEDICAL_UNITS, RANGE_KEYWORDS


class NumericProcessor:
    """数字处理器"""
    
    def __init__(self):
        """初始化"""
        self.units_mapping = MEDICAL_UNITS
        self.range_pattern = '|'.join([re.escape(kw) for kw in RANGE_KEYWORDS])
        # 【新增】预编译正则表达式（性能优化）
        self.scientific_pattern = re.compile(r'(\d+\.?\d*)[eE]([+-]?\d+)')
        self.multi_value_pattern = re.compile(r'([A-Za-z一-龥]+)×?(\d+)')
    
    def extract_numeric_info(self, text: str) -> List[Dict]:
        """
        提取数字和单位信息
        
        注意：不将范围符号"-"误认为负号
        例如："0.5-13000"中的"-"是范围符号不是负号
        
        【增强】括号内单位优先级：
        - 若数字后紧跟括号，括号内有单位，则优先使用括号内单位
        - 例如："300(mL)" 或 "300(mL/min)" 中括号内的单位为主要判断依据
        
        Args:
            text: 原始文本
            
        Returns:
            数字信息列表 [{'value': float, 'unit': str, 'original': str, 'has_paren_unit': bool}, ...]
        """
        results = []
        processed_positions = set()  # 记录已处理的位置，避免重复
        
        # 步骤1：优先处理括号内单位 (\u6700高优先级)
        # 模式1：数字(\u5355位) - \u4f8b如 "100(mm)", "300(mL)"
        # 模式2：\u6570\u5b57-\u6570\u5b57(\u5355\u4f4d) - \u4f8b\u5982 "100-200(mm)"
        paren_number_pattern = r'(\d+[,\d]*\.?\d*)\s*[-~\u81f3]\s*(\d+[,\d]*\.?\d*)\s*\(\s*([a-zA-Z\u00b0\u2103\u03bc/]+|[\u4e00-\u9fff]+)\s*\)'
        for match in re.finditer(paren_number_pattern, text):
            paren_unit = match.group(3).strip()
            # \u8fd9\u662f\u8303\u56f4\u5f62\u5f0f\uff1a\u4e24\u4e2a\u6570\u5b57
            val1 = float(match.group(1).replace(',', ''))
            val2 = float(match.group(2).replace(',', ''))
            results.append({
                'value': val1,
                'unit': paren_unit,
                'original': match.group(0).strip(),
                'has_paren_unit': True
            })
            results.append({
                'value': val2,
                'unit': paren_unit,
                'original': match.group(0).strip(),
                'has_paren_unit': True
            })
            processed_positions.add(match.start())
        
        # 模式3：单个数字(单位) - 例如 "100(mm)"
        single_paren_pattern = r'(\d+[,\d]*\.?\d*)\s*\(\s*([a-zA-Z°℃μ/]+|[\u4e00-\u9fff]+)\s*\)'
        for match in re.finditer(single_paren_pattern, text):
            if match.start() not in processed_positions:
                paren_unit = match.group(2).strip()
                value = float(match.group(1).replace(',', ''))
                results.append({
                    'value': value,
                    'unit': paren_unit,
                    'original': match.group(0).strip(),
                    'has_paren_unit': True
                })
                processed_positions.add(match.start())
        
        # 步骤2：检查是否有括号内数字对应的单位（用于识别"(数字-数字)单位"格式）
        # 模式：(数字-数字)单位 或 (数字)单位
        paren_unit_pattern = r'\(([\d\s\-.,]+)\)\s*([a-zA-Z°℃μ/]+|[\u4e00-\u9fff]+)'
        paren_unit_map = {}  # 用于跟踪括号内数字对应的单位
        
        for match in re.finditer(paren_unit_pattern, text):
            paren_content = match.group(1)
            unit = match.group(2).strip()
            # 存储括号内容和单位的一一对应
            paren_unit_map[paren_content] = unit
        
        # 步骤3：匹配不带前导"-"的所有数字（避免"-"被认为是负号）
        # 支持: 100mm, 100 mm, 100毫米, 1.5kg, 1,000g 等
        pattern = r'(\d+[,\d]*\.?\d*)\s*([a-zA-Z°℃μ/]+|[\u4e00-\u9fff]+)?'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            if match.start() in processed_positions:
                continue  # 跳过已经处理过的数字
            
            value_str = match.group(1).replace(',', '')  # 移除千位分隔符
            unit_str = match.group(2) if match.group(2) else ''
            
            # 检查这个数字是否在括号内
            # 如果在括号内，使用括号后的单位
            is_in_paren = False
            for paren_content, paren_unit in paren_unit_map.items():
                if value_str in paren_content.replace(' ', '').replace('.', ''):
                    # 这个数字在括号内
                    is_in_paren = True
                    unit_str = paren_unit  # 使用括号后的单位
                    break
            
            try:
                value = float(value_str)
                results.append({
                    'value': value,
                    'unit': unit_str.strip(),
                    'original': match.group(0).strip(),
                    'has_paren_unit': is_in_paren
                })
            except ValueError:
                continue
        
        # 步骤4：处理明确的负数（空白或比较符号后接负号）
        # 例如："≥-10"、"> -5" 中的"-10"、"-5"是真正的负数
        negative_pattern = r'([\s≥≤><=])([-+])(\d+[,\d]*\.?\d*)\s*([a-zA-Z°℃μ/]+|[\u4e00-\u9fff]+)?'
        neg_matches = re.finditer(negative_pattern, text)
        
        for match in neg_matches:
            sign = match.group(2)  # '-' 或 '+'
            value_str = (sign + match.group(3)).replace(',', '')
            unit_str = match.group(4) if match.group(4) else ''
            
            try:
                value = float(value_str)
                results.append({
                    'value': value,
                    'unit': unit_str.strip(),
                    'original': match.group(0).strip(),
                    'has_paren_unit': False
                })
            except ValueError:
                continue
        
        return results
    
    def identify_unit_category(self, unit: str) -> Optional[str]:
        """
        识别单位类别（大小写不敏感）
        
        Args:
            unit: 单位字符串
            
        Returns:
            单位类别名称
        """
        if not unit:
            return None
        
        unit_lower = unit.lower()
        
        # 逐个类别进行匹配
        for category, info in self.units_mapping.items():
            # 处理普通类别
            if 'units' in info:
                for std_unit in info['units']:
                    if std_unit.lower() == unit_lower:
                        return category
            
            # 对于电学类特殊处理（包含子类型）
            if category == '电学类':
                for sub_type, sub_info in info.items():
                    if isinstance(sub_info, dict) and 'conversions' in sub_info:
                        for std_unit in sub_info['conversions'].keys():
                            if std_unit.lower() == unit_lower:
                                return f"{category}_{sub_type}"
        
        return None
    
    def convert_unit(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """
        单位转换（大小写不敏感）
        
        Args:
            value: 数值
            from_unit: 源单位
            to_unit: 目标单位
            
        Returns:
            转换后的值
        """
        # 找到单位所属类别
        from_category = self.identify_unit_category(from_unit)
        to_category = self.identify_unit_category(to_unit)
        
        if not from_category or not to_category:
            return None
        
        # 必须是同一类别
        if from_category != to_category:
            return None
        
        # 获取转换信息
        category_base = from_category.split('_')[0]
        category_info = self.units_mapping.get(category_base)
        
        if not category_info:
            return None
        
        # 电学类特殊处理
        if category_base == '电学类':
            # 检查是否有下划线（表示子类型）
            if '_' in from_category:
                sub_type = from_category.split('_')[1]
                conversions = category_info[sub_type]['conversions']
            else:
                # 没有子类型，查找该单位属于哪个子类型
                conversions = None
                for sub_type_name, sub_type_info in category_info.items():
                    if isinstance(sub_type_info, dict) and 'conversions' in sub_type_info:
                        # 大小写不敏感匹配
                        from_unit_lower = from_unit.lower()
                        to_unit_lower = to_unit.lower()
                        conversions_keys_lower = {k.lower(): k for k in sub_type_info['conversions'].keys()}
                        
                        if from_unit_lower in conversions_keys_lower and to_unit_lower in conversions_keys_lower:
                            conversions = sub_type_info['conversions']
                            break
                if conversions is None:
                    return None
        else:
            conversions = category_info.get('conversions')
        
        if not conversions:
            return None
        
        # 大小写不敏感地查找转换系数
        from_unit_lower = from_unit.lower()
        to_unit_lower = to_unit.lower()
        conversions_lower = {k.lower(): v for k, v in conversions.items()}
        
        if from_unit_lower not in conversions_lower or to_unit_lower not in conversions_lower:
            return None
        
        # 温度类需要特殊处理
        if category_base == '温度类':
            return self._convert_temperature(value, from_unit, to_unit)
        
        # 转换: 先转为基准单位,再转为目标单位
        base_value = value * conversions_lower[from_unit_lower]
        result = base_value / conversions_lower[to_unit_lower]
        
        return round(result, 4)
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """
        温度转换
        
        Args:
            value: 温度值
            from_unit: 源单位
            to_unit: 目标单位
            
        Returns:
            转换后的温度
        """
        # 标准化单位表示
        celsius_units = ['℃', '°C', 'C', '摄氏度']
        fahrenheit_units = ['°F', 'F', '华氏度']
        
        is_from_celsius = from_unit in celsius_units
        is_to_celsius = to_unit in celsius_units
        
        if is_from_celsius and not is_to_celsius:
            # 摄氏度转华氏度
            return round(value * 9/5 + 32, 2)
        elif not is_from_celsius and is_to_celsius:
            # 华氏度转摄氏度
            return round((value - 32) * 5/9, 2)
        else:
            # 相同单位
            return value
    
    def normalize_unit(self, value: float, unit: str) -> Tuple[float, str]:
        """
        单位标准化（转换为基准单位）
        
        Args:
            value: 数值
            unit: 单位
            
        Returns:
            (标准化后的值, 基准单位)
        """
        category = self.identify_unit_category(unit)
        if not category:
            return value, unit
        
        category_base = category.split('_')[0]
        category_info = self.units_mapping.get(category_base)
        
        if not category_info:
            return value, unit
        
        # 电学类特殊处理
        if category_base == '电学类':
            # 检查是否有下划线
            if '_' in category:
                sub_type = category.split('_')[1]
                base_unit = category_info[sub_type]['base_unit']
                conversions = category_info[sub_type]['conversions']
            else:
                # 没有子类型，查找该单位属于哪个子类型
                base_unit = unit
                conversions = None
                for sub_type_name, sub_type_info in category_info.items():
                    if isinstance(sub_type_info, dict) and 'conversions' in sub_type_info:
                        if unit in sub_type_info['conversions']:
                            base_unit = sub_type_info['base_unit']
                            conversions = sub_type_info['conversions']
                            break
                if conversions is None:
                    return value, unit
        else:
            base_unit = category_info.get('base_unit', unit)
            conversions = category_info.get('conversions', {})
        
        if not conversions or unit not in conversions:
            return value, unit
        
        # 转换为基准单位
        base_value = value * conversions[unit]
        return round(base_value, 4), base_unit
    
    def is_range_value(self, text: str) -> bool:
        """
        判断是否为范围值
        
        Args:
            text: 文本
            
        Returns:
            是否为范围
        """
        # 检查是否包含范围关键词
        for keyword in RANGE_KEYWORDS:
            if keyword in text:
                return True
        
        # 检查是否包含范围模式：\d+-\d+ 或 \d+~\d+
        if re.search(r'\d+\s*[-~符]\s*\d+', text):
            return True
        
        return False
    
    def extract_range(self, text: str) -> Optional[Tuple[float, float, str]]:
        """
        提取数值范围
        
        Args:
            text: 文本
            
        Returns:
            (最小值, 最大值, 单位) 或 None
        """
        # 提取所有数字信息
        numeric_info = self.extract_numeric_info(text)
        
        if len(numeric_info) < 2:
            return None
        
        # 假设前两个数字是范围
        min_val = numeric_info[0]['value']
        max_val = numeric_info[1]['value']
        unit = numeric_info[0]['unit'] or numeric_info[1]['unit']
        
        # 确保min < max
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        
        return (min_val, max_val, unit)
    
    def format_range(self, min_val: float, max_val: float, unit: str, 
                     prefix: str = '') -> str:
        """
        格式化范围值
        
        Args:
            min_val: 最小值
            max_val: 最大值
            unit: 单位
            prefix: 前缀（如参数名称）
            
        Returns:
            格式化后的字符串
        """
        # 移除小数点后多余的0
        min_str = f"{min_val:g}"
        max_str = f"{max_val:g}"
        
        if prefix:
            return f"{prefix}({min_str}-{max_str}){unit}"
        else:
            return f"({min_str}-{max_str}){unit}"
    
    def merge_numeric_values(self, values: List[str], parameter_name: str = '') -> Tuple[str, str]:
        """
        合并数字值（创建范围或统一单位）
        
        【增强】误差结构处理：
        - 检测是否为误差结构（含"±"或"误差"）
        - 若是，采用该行供应商给出的最大数值作为融合数值
        
        Args:
            values: 数值列表
            parameter_name: 参数名称
            
        Returns:
            (融合结果, 融合类型)
        """
        import re
        import pandas as pd
        from collections import Counter
        
        # 【新增】第一步：检测是否为误差结构
        # 误差结构特征：含有"±"或"误差"关键词
        has_error_struct = False
        for val in values:
            val_str = str(val) if pd.notna(val) else ''
            if '±' in val_str or '误差' in val_str:
                has_error_struct = True
                break
        
        # 若为误差结构，提取最大数值
        if has_error_struct:
            max_numeric = None
            max_unit = ''
            
            for val in values:
                if pd.notna(val):
                    val_str = str(val).strip()
                    # 提取该值的数字信息
                    numeric_list = self.extract_numeric_info(val_str)
                    if numeric_list:
                        # 找到最大的数字
                        for num_info in numeric_list:
                            if max_numeric is None or num_info['value'] > max_numeric:
                                max_numeric = num_info['value']
                                max_unit = num_info['unit']
            
            if max_numeric is not None:
                # 格式化结果
                if max_unit:
                    result = f"{max_numeric:g}{max_unit}"
                else:
                    result = f"{max_numeric:g}"
                return result, '误差结构融合'
        
        # 【继续原有逻辑】提取所有数字信息
        all_numeric = []
        text_prefixes = []  # 保存文字前缀
        range_like_data = []  # 识别范围类数据
        
        for val in values:
            nums = self.extract_numeric_info(str(val))
            if nums:
                all_numeric.extend(nums)
                # 提取数字前的文字部分作为前缀
                # 使用正则表达式找到第一个数字出现的位置
                match = re.search(r'\d', str(val))  # 找到第一个数字
                if match:
                    text_before_num = str(val)[:match.start()].strip()
                    # 标准化比较符号
                    text_before_num = self.normalize_comparison_operators(text_before_num)
                    # 只保留数字前的文字部分，不保留比较符号和冒号等符号
                    text_before_num = re.sub(r'^[\s：:、第°No\-–—≥≤><=]+', '', text_before_num).strip()
                    # 去掉末尾的比较符号和冒号
                    text_before_num = re.sub(r'[≥≤><=\-：:]+$', '', text_before_num).strip()  # 去掉末尾的比较符号、减号和冒号
                    if text_before_num and not re.match(r'^[≥≤><=\-：:]+$', text_before_num):
                        # 标准化前缀文本
                        normalized_prefix = self.normalize_text_prefix(text_before_num)
                        text_prefixes.append(normalized_prefix)
                # 检查是否看起来像范围数据（包含范围关键词或-符号）
                if self.is_range_value(str(val)):
                    range_like_data.append(val)
        
        if not all_numeric:
            return None, None
        
        # 如果有明确的范围标识，只处理有范围关键词的数据
        numeric_data_to_process = all_numeric
        if range_like_data and len(range_like_data) > 1:
            # 如果大多数数据看起来像范围，只从这些数据中提取数字
            if len(range_like_data) >= len(values) / 2:
                range_numeric = []
                for val in range_like_data:
                    nums = self.extract_numeric_info(str(val))
                    if nums:
                        range_numeric.extend(nums)
                if range_numeric:
                    numeric_data_to_process = range_numeric
        
                # ... existing code ...
        # 步骤1：识别有效的数字（基于上下文和单位）
        # 例如：供应商2中"5步可视可调"的5是噪声数字，应该被过滤
        # 原理：寻找多个供应商都提到的（通常相似的）数字范围，忽略只出现一次的异常值
        
        # 统计所有提取的数字值
        all_values = [n['value'] for n in numeric_data_to_process]
        unique_values = sorted(set([round(v, 1) for v in all_values]))
        
        # 如果数字太多（>3个不同值），可能有噪声数字
        if len(unique_values) > 3:
            # 检查最小值是否显著小于其他值（可能是噪声）
            if len(unique_values) > 1:
                # 计算数值的中位数
                sorted_vals = sorted(all_values)
                median_val = sorted_vals[len(sorted_vals) // 2]
                
                # 如果最小值远小于中位数（<中位数的50%），可能是噪声
                min_val = min(all_values)
                if min_val < median_val * 0.5:
                    # 过滤掉这个最小值
                    numeric_data_to_process = [n for n in numeric_data_to_process if n['value'] >= median_val * 0.5]
        
        # 如果没有明确范围标识，过滤掉明显是单个分段/阈值的数字
        # 例如："分段≥8" 中的 8 应该被过滤
        if not range_like_data or len(range_like_data) < len(values) / 2:
            # 只保留相对值区间大的数据（很可能是范围）
            if len(numeric_data_to_process) > 1:
                values_only = [n['value'] for n in numeric_data_to_process]
                value_range = max(values_only) - min(values_only)
                # 如果数值跨度很大（>50% of max），认为是真实范围
                max_val = max(values_only)
                if value_range > max_val * 0.1:  # 跨度大于最大值的10%
                    # 保留这个范围
                    pass
                elif len(values_only) > 1 and len(set([round(v, 1) for v in values_only])) == len(values_only):
                    # 如果有多个不同的数字，保留
                    pass
                else:
                    # 否则，只取最大的数字（可能是真实阈值）
                    max_num_idx = values_only.index(max_val)
                    numeric_data_to_process = [numeric_data_to_process[max_num_idx]]
        
        # 确定前缀（使用最常见的，或使用参数名称）
                # ... existing code ...
        prefix = ''
        # 优先优先使用后上出现最频繁的前缀（更恰当）
        if text_prefixes:
            most_common_prefix = Counter(text_prefixes).most_common(1)[0][0]
            prefix = most_common_prefix
        # 其次使用参数名称
        elif parameter_name:
            prefix = parameter_name
        
        # 检查单位是否一致
        units = [n['unit'] for n in numeric_data_to_process if n['unit']]
        
        if not units:
            # 纯数字,无单位
            nums = [n['value'] for n in numeric_data_to_process]
            if len(set(nums)) == 1:
                result = f"{prefix}{nums[0]:g}" if prefix else str(nums[0])
                return result, '精确匹配'
            else:
                min_val = min(nums)
                max_val = max(nums)
                result = f"{prefix}{min_val:g}-{max_val:g}" if prefix else f"{min_val:g}-{max_val:g}"
                return result, '数字范围融合'
        
        # 尝试单位统一
        first_unit = units[0]
        # 【修复】单位统一时不区分大小写（并且使用供应商中会较常出现的单位形式）
        first_unit_lower = first_unit.lower()
        normalized_values = []
        used_unit = first_unit  # 预设使用的单位
        
                # ... existing code ...
        # 规则：
        # 1. 如果单位都为空，可以融合
        # 2. 如果单位都相同（忽略大小写），可以融合
        # 3. 如果单位可以相互转换（如w和kW），可以融合
        # 4. 如果存在不同的非空单位且无法转换，拒绝融合（不能混淆Hz和s、%和s等）
        all_units_compatible = True
        non_empty_units = [n['unit'] for n in numeric_data_to_process if n['unit']]
        
        if non_empty_units:
            # 存在非空单位，检查是否都相同或可转换
            first_non_empty_unit = non_empty_units[0]
            for unit in non_empty_units[1:]:
                # 先检查大小写是否相同
                if unit.lower() != first_non_empty_unit.lower():
                    # 大小写不同，尝试单位转换来判断兼容性
                    # 例如：w 转 kW
                    converted = self.convert_unit(1.0, unit, first_non_empty_unit)
                    if converted is None:
                        # 无法转换，说明是不同的物理量，拒绝融合
                        all_units_compatible = False
                        break
        
        # 如果单位不兼容，拒绝融合
        if not all_units_compatible:
            return None, None
        
        for num_info in numeric_data_to_process:
            if num_info['unit']:
                # 尝试转换为第一个单位
                converted = self.convert_unit(num_info['value'], num_info['unit'], first_unit)
                if converted is not None:
                    # 转换成功
                    normalized_values.append(converted)
                    used_unit = first_unit
                else:
                    # 如果转换失败，检查是否是大小写差异
                    # 例如 'db' vs 'DB' 或 'w' vs 'W'
                    if num_info['unit'].lower() == first_unit.lower():
                        # 实际是同一个单位，使用原值
                        normalized_values.append(num_info['value'])
                        used_unit = first_unit
                    else:
                        # 实际是不同的单位且无法转换
                        # 这不应该发生（因为前面已经检查了兼容性）
                        # 但为了安全起见，使用原值
                        normalized_values.append(num_info['value'])
            else:
                normalized_values.append(num_info['value'])  
        
        # 使用记录的单位形式（来自供应商数据）
        final_unit = used_unit
        
                # ... existing code ...
        # 比较时使用较大的整数位来防止浮点数值误差
        # 例如：3000W 转换为 3KW 后的 3.0 与 3 应该被认为相同
        rounded_values = [round(v, 6) for v in normalized_values]  # 大精度囎入
        if len(set(rounded_values)) == 1:
            result = f"{prefix}{normalized_values[0]:g}{final_unit}" if prefix else f"{normalized_values[0]:g}{final_unit}"
            return result, '单位转换融合'
        
        # 创建范围
        min_val = min(normalized_values)
        max_val = max(normalized_values)
        
        # 格式化范围，保留前缀
        if prefix:
            result = f"{prefix}{min_val:g}-{max_val:g}{final_unit}"
        else:
            result = self.format_range(min_val, max_val, final_unit, parameter_name)
        
        return result, '数字范围融合'
    
    def is_relevant_data(self, text: str, parameter_name: str) -> bool:
        """
        判断数据是否与参数名称相关
        过滤掉完全不相关的数据
        
        例如：
        - 参数: "电池容量"
        - 数据: "工作时间≥0.5小时" -> False (不相关)
        - 数据: "容量≥13000mA" -> True (相关)
        
        Args:
            text: 供应商数据
            parameter_name: 参数名称
            
        Returns:
            是否相关
        """
        if not text or not parameter_name:
            return True
        
        text_lower = str(text).lower()
        param_lower = str(parameter_name).lower()
        
        # 【增强】严格相关性检查：使用字符串相似度来判断参数是否完全不同
        # 例如："增益调节"和"TGC分段"不应该融合
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, param_lower, text_lower).ratio()
        
        # 如果两个参数名称的相似度低于30%，认为是完全不同的参数
        if similarity < 0.3:
            return False
        
        # 提取参数的关键词
        # 例如: "电池容量" -> ["电池", "容量"]
        param_keywords = []
        for word in param_lower.split():
            if len(word) > 1:  # 过滤单个字符
                param_keywords.append(word)
        
        # 检查数据中是否包含参数关键词
        has_param_keyword = any(kw in text_lower for kw in param_keywords)
        
        # 检查是否包含明显不相关的关键词
        irrelevant_keywords = [
            '工作时间',  # 时间参数
            '断电',      # 特殊条件
            '操作',      # 动作词
            '响应',      # 响应相关
            '刷新',      # 刷新相关
            '频率',      # 频率相关（如果参数不是频率）
        ]
        
        has_irrelevant = any(kw in text_lower for kw in irrelevant_keywords)
        
        # 修改逻辑：必须包含参数关键词且不包含不相关词
        return has_param_keyword and not has_irrelevant
    
    def is_dimension_specification(self, text: str) -> bool:
        """
        【新增】检测文本是否是尺寸规格类参数
        
        尺寸规格示例：
        - 280mm×240mm
        - 285mm*200mm
        - 23.8英寸
        - 1920*1080像素
        
        这类数据不应该甩整合（在非相同上下文中是完全不同的规格）
        
        Args:
            text: 文本
            
        Returns:
            是否是尺寸规格
        """
        if not text:
            return False
        
        text_str = str(text)
        
        # 检测是否包含尺寸相关的分隔符号（*, x, ×的是乔洛时）
        # 1. 咨及׸×分隔的数字+单位
        if re.search(r'\d+\s*(?:mm|cm|in|"|\x27|英寸|\.)\s*[\u00d7x*\/]\s*\d+', text_str, re.IGNORECASE):
            return True
        
        # 2. 像素或单位分隔
        if re.search(r'\d+\s*\*\s*\d+\s*(?:像素|pixel)', text_str, re.IGNORECASE):
            return True
        
        # 3. 只是数字×数字（例夗1920×1080）
        if re.search(r'\d+\s*[\u00d7x*]\s*\d+', text_str):
            # 但要排除数字-数字的情况（如范围）
            if not re.search(r'\d+-\d+', text_str):
                return True
        
        return False
    
    def has_model_keywords(self, text: str) -> bool:
        """
        【新增】检测文本是否包含型号关键词
        
        型号关键词示例：i3、i5、i7、i8、Intel、AMD、RTX、GTX等
        如果包含型号关键词，表明这是一个型号参数，不应该进行数字范围融合
        
        Args:
            text: 文本
            
        Returns:
            是否包含型号关键词
        """
        if not text:
            return False
        
        text_lower = str(text).lower()
        
        # CPU型号关键词
        cpu_models = [
            'i3', 'i5', 'i7', 'i9',  # Intel Core i系列
            'intel', 'amd', 'ryzen',  # CPU品牌
            'xeon', 'pentium',        # 其他CPU型号
        ]
        
        # GPU型号关键词
        gpu_models = [
            'rtx', 'gtx', 'tesla',    # NVIDIA
            'radeon', 'rx',           # AMD
            'arc',                    # Intel Arc
        ]
        
        # 其他型号关键词
        other_models = [
            '代', '第',               # CPU代数（如"第12代"）
        ]
        
        # 检查是否包含这些关键词
        all_models = cpu_models + gpu_models + other_models
        for model_keyword in all_models:
            if model_keyword in text_lower:
                return True
        
        return False
    
    def is_error_tolerance(self, text: str) -> bool:
        """
        【新增】检测文本是否是误差范围/容差
        
        误差范围示例：
        - ±5%
        - ±10 dB
        - ±40%
        - ±20%
        
        这类数据是精度/接受上限，不应该与其他单位数捪进行数字范围融合
        
        Args:
            text: 文本
            
        Returns:
            是否是误差范围
        """
        if not text:
            return False
        
        text_str = str(text)
        
        # 模式：±[整数|x.xx][了空格][%|dB|℃]
        # 例夗1：±5%, ±10dB, ±40%
        error_pattern = r'[±+-]\s*\d+(?:\.\d+)?\s*(?:%|dB|db|℃|°C)'
        if re.search(error_pattern, text_str, re.IGNORECASE):
            return True
        
        # 模式2：整整数+-整整数的误差表述
        # 例夗0±40%、±20%
        if re.search(r'\d+\s*[%±+-]', text_str):
            if re.search(r'[%℃dB]', text_str, re.IGNORECASE):
                return True
        
        return False

    def is_numeric(self, text: str) -> bool:
        """判断文本是否包含数字"""
        return bool(re.search(r'\d', str(text)))
    
    def parse_scientific_notation(self, text: str) -> Optional[float]:
        """
        【新增】解析科学记数法
        
        Args:
            text: 文本
            
        Returns:
            数值或None
        
        Examples:
            "3e6" -> 3000000.0
            "1.5E-3" -> 0.0015
        """
        match = self.scientific_pattern.search(text)
        if match:
            base = float(match.group(1))
            exp = int(match.group(2))
            return base * (10 ** exp)
        return None
    
    def parse_multi_value(self, text: str, separator: str = '×') -> Dict[str, int]:
        """
        【新增】解析多值参数
        
        Args:
            text: 文本
            separator: 分隔符
            
        Returns:
            键值字典
        
        Examples:
            "USB×3 HDMI×2" -> {"USB": 3, "HDMI": 2}
            "A/B/M" -> {"A": 1, "B": 1, "M": 1}
        """
        result = {}
        
        # 处理斜杠分隔的情况 (A/B/M)
        if separator == '/' or '/' in text:
            parts = text.split('/')
            for part in parts:
                part = part.strip()
                # 移除数字部分
                clean_part = re.sub(r'[\d×]+', '', part).strip()
                if clean_part:
                    result[clean_part.upper()] = 1
            return result
        
        # 使用正则匹配 (×分隔)
        matches = self.multi_value_pattern.findall(text)
        for key, value in matches:
            result[key.upper()] = int(value)
        
        return result

    def parse_range_value(self, text: str) -> Optional[Tuple[float, float, str, str]]:
        """
        【新增】解析范围值，支持多种格式
        
        支持格式：
        - 3~5kW
        - 3-5kW
        - ≥3kW ≤5kW
        - 3kW 或 5kW
        
        Args:
            text: 文本
            
        Returns:
            (min_val, max_val, unit, comparison) 或 None
        """
        # 模式1：3~5kW 或 3-5kW
        pattern1 = r'(\d+\.?\d*)\s*[~\-至]\s*(\d+\.?\d*)\s*([a-zA-Z]+)'
        match = re.search(pattern1, text)
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            unit = match.group(3)
            return (min_val, max_val, unit, '')
        
        # 模式2：≥3kW ≤5kW
        pattern2 = r'([\u2265\u2264><=]+)\s*(\d+\.?\d*)\s*([a-zA-Z]+)'
        matches = re.findall(pattern2, text)
        if len(matches) == 2:
            comp1, val1, unit1 = matches[0]
            comp2, val2, unit2 = matches[1]
            if unit1 == unit2:
                vals = [float(val1), float(val2)]
                return (min(vals), max(vals), unit1, '')
        
        # 模式3：3kW 或 5kW
        pattern3 = r'(\d+\.?\d*)\s*([a-zA-Z]+)\s*[或or]\s*(\d+\.?\d*)\s*([a-zA-Z]+)'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            val1 = float(match.group(1))
            unit1 = match.group(2)
            val2 = float(match.group(3))
            unit2 = match.group(4)
            if unit1 == unit2 or unit1.lower() == unit2.lower():
                return (min(val1, val2), max(val1, val2), unit1, '')
        
        return None
    
    def normalize_text_prefix(self, prefix: str) -> str:
        """
        【新增】标准化文本前缀，将语义等价的文本统一
        
        例如：
        - "不小于" -> "≥"
        - "不少于" -> "≥"
        - "至少" -> "≥"
        - "不大于" -> "≤"
        - "不超过" -> "≤"
        - "最多" -> "≤"
        
        Args:
            prefix: 原始文本前缀
            
        Returns:
            标准化后的符号
        """
        if not prefix:
            return ''
        
        prefix_lower = prefix.lower().strip()
        
        # 大于等于的语义等价
        if any(kw in prefix_lower for kw in ['不小于', '不少于', '至少', '不低于', '大于等于', '≥0']):
            return '≥'
        
        # 小于等于的语义等价
        if any(kw in prefix_lower for kw in ['不大于', '不超过', '最多', '不高于', '小于等于', '≤0']):
            return '≤'
        
        # 大于
        if any(kw in prefix_lower for kw in ['大于', '超过', '高于', '>']):
            return '≥'  # 统一转为≥
        
        # 小于
        if any(kw in prefix_lower for kw in ['小于', '低于', '<']):
            return '≤'  # 统一转为≤
        
        return prefix
    
    def should_skip_numeric_fusion(self, text: str) -> bool:
        """
        【新增】判断是否应该跳过数字融合
        
        应该跳过的情况:
        - 不是数字信息
        - 是描诼性文本
        
        Args:
            text: 文本
            
        Returns:
            是否应该跳过
        """
        if not text:
            return True
        
        text_lower = str(text).lower()
        
        # 应该跳过的情况
        skip_keywords = ['描诼', 'description', '什么是', 'what', '可能']
        
        return any(kw in text_lower for kw in skip_keywords)
    
    def normalize_comparison_operators(self, text: str) -> str:
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
        
        # 替换比较符号: > → ≥，< → ≤
        # 下面是全角符号
        result = result.replace('＞=', '≥')  # ＞= → ≥
        result = result.replace('＜=', '≤')  # ＜= → ≤
        result = result.replace('＞', '≥')   # ＞ → ≥
        result = result.replace('＜', '≤')   # ＜ → ≤
        
        # 下面是半角符号
        result = result.replace('>=', '≥')  # >= → ≥
        result = result.replace('<=', '≤')  # <= → ≤
        result = result.replace('>', '≥')   # > → ≥
        result = result.replace('<', '≤')   # < → ≤
        
        return result
