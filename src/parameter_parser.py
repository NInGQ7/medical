# -*- coding: utf-8 -*-
"""
参数解析模块
用于解析整合的规格参数字符串，如：
"≥Windows10操作系统，≥酷睿i5 CPU、≥8G 内存，≥250GB SSD+4T 硬盘，≥24 英寸高分辨率TFT"
"""

import re
from typing import List, Dict, Optional, Tuple


class ParameterParser:
    """参数解析器 - 用于解析整合参数字符串"""
    
    def __init__(self):
        """初始化参数解析器"""
        # 参数分隔符（逗号、顿号、分号等）
        self.separators = r'[，,；;、\n]'
        
        # 比较符号
        self.comparison_symbols = r'[≥≤><=\-~]+'
        
        # 参数类型关键词映射
        self.param_type_keywords = {
            '操作系统': ['操作系统', '系统', '系统版本', 'OS', '操作'],
            'CPU': ['CPU', '处理器', '中央处理器', '酷睿', '英特尔', 'Intel', 'AMD', '锐龙', 'Ryzen'],
            '内存': ['内存', 'RAM', '内存大小', '存储内存'],
            '存储': ['存储', '硬盘', '固态硬盘', 'SSD', 'HDD', '磁盘', 'M.2', 'NVMe'],
            '显示器': ['显示器', '显示屏', '屏幕', '英寸', '分辨率', '液晶屏', 'TFT'],
            '显卡': ['显卡', 'GPU', '独立显卡', '集成显卡'],
            '网络': ['网络', '网口', 'RJ45', '以太网'],
            '接口': ['接口', 'USB', 'HDMI', 'DisplayPort', 'Thunderbolt'],
            '电源': ['电源', '功率', 'W', 'kW'],
            '冷却': ['散热', '冷却', '风冷', '液冷'],
        }
    
    def parse_integrated_params(self, text: str) -> List[Dict]:
        """
        解析整合的规格参数字符串
        
        Args:
            text: 整合参数字符串，如"≥Windows10操作系统，≥酷睿i5 CPU、≥8G 内存，≥250GB SSD+4T 硬盘，≥24 英寸高分辨率TFT"
            
        Returns:
            参数列表 [{'param_type': str, 'original': str, 'comparison': str, 'content': str}, ...]
        """
        if not text or not isinstance(text, str):
            return []
        
        results = []
        
        # 第一步：按分隔符拆分
        segments = re.split(self.separators, text.strip())
        
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            
            # 第二步：提取比较符号
            comparison_match = re.match(r'^(' + self.comparison_symbols + r')\s*(.*?)$', segment)
            
            if comparison_match:
                comparison = comparison_match.group(1).strip()
                content = comparison_match.group(2).strip()
            else:
                comparison = ''
                content = segment
            
            if not content:
                continue
            
            # 第三步：识别参数类型
            param_type = self._identify_param_type(content)
            
            results.append({
                'param_type': param_type,
                'original': segment,
                'comparison': comparison,
                'content': content
            })
        
        return results
    
    def _identify_param_type(self, content: str) -> str:
        """
        识别参数类型
        
        Args:
            content: 参数内容
            
        Returns:
            参数类型
        """
        content_lower = content.lower()
        
        # 逐个检查参数类型关键词
        for param_type, keywords in self.param_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return param_type
        
        return '其他'
    
    def extract_specs_from_param(self, param_dict: Dict) -> Dict:
        """
        从参数字典中提取具体规格
        
        Args:
            param_dict: 参数字典 {'param_type': str, 'original': str, 'comparison': str, 'content': str}
            
        Returns:
            提取的规格信息 {'param_type': str, 'spec': str, 'numbers': list, 'units': list}
        """
        content = param_dict.get('content', '')
        param_type = param_dict.get('param_type', '其他')
        
        # 提取数字和单位
        numeric_pattern = r'(\d+[.,\d]*)\s*([a-zA-Z°℃μ/GB数字GHz中文]+)?'
        numbers = []
        units = []
        
        for match in re.finditer(numeric_pattern, content):
            num_str = match.group(1).replace(',', '')
            unit_str = match.group(2) if match.group(2) else ''
            
            try:
                numbers.append(float(num_str))
                if unit_str:
                    units.append(unit_str.strip())
            except ValueError:
                continue
        
        # 清理规格（移除数字和单位，保留描述）
        spec = re.sub(r'(\d+[.,\d]*)\s*([a-zA-Z°℃μ/GB中文]+)?', '', content).strip()
        # 移除参数类型关键词
        for keyword in self.param_type_keywords.get(param_type, []):
            spec = re.sub(rf'{re.escape(keyword)}', '', spec, flags=re.IGNORECASE)
        spec = spec.strip()
        
        return {
            'param_type': param_type,
            'original_content': content,
            'spec_description': spec,
            'numbers': numbers,
            'units': units
        }
    
    def format_parsed_params(self, parsed_list: List[Dict]) -> str:
        """
        格式化解析结果为可读字符串
        
        Args:
            parsed_list: 解析结果列表
            
        Returns:
            格式化后的字符串
        """
        if not parsed_list:
            return "无法解析参数"
        
        lines = []
        for idx, item in enumerate(parsed_list, 1):
            param_type = item.get('param_type', '其他')
            comparison = item.get('comparison', '')
            content = item.get('content', '')
            
            line = f"{idx}. 【{param_type}】 {comparison} {content}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def group_by_param_type(self, parsed_list: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按参数类型分组解析结果
        
        Args:
            parsed_list: 解析结果列表
            
        Returns:
            分组后的字典 {'参数类型': [参数列表]}
        """
        grouped = {}
        for item in parsed_list:
            param_type = item.get('param_type', '其他')
            if param_type not in grouped:
                grouped[param_type] = []
            grouped[param_type].append(item)
        
        return grouped


# 示例使用函数
def demo_parse_params():
    """演示参数解析功能"""
    # 示例1：医疗设备规格
    sample1 = "≥Windows10操作系统，≥酷睿i5 CPU、≥8G 内存，≥250GB SSD+4T 硬盘，≥24 英寸高分辨率TFT"
    
    # 示例2：复杂规格
    sample2 = "Intel-i5 12代及以上, Windows10/11, 16GB DDR4内存, 512GB NVMe SSD, RTX 3050显卡, 24英寸IPS显示器"
    
    parser = ParameterParser()
    
    print("=" * 60)
    print("示例1：", sample1)
    print("=" * 60)
    parsed = parser.parse_integrated_params(sample1)
    print(parser.format_parsed_params(parsed))
    
    print("\n" + "=" * 60)
    print("示例2：", sample2)
    print("=" * 60)
    parsed2 = parser.parse_integrated_params(sample2)
    print(parser.format_parsed_params(parsed2))
    
    print("\n" + "=" * 60)
    print("按参数类型分组：")
    print("=" * 60)
    grouped = parser.group_by_param_type(parsed2)
    for param_type, items in grouped.items():
        print(f"\n【{param_type}】:")
        for item in items:
            print(f"  - {item['comparison']} {item['content']}")


if __name__ == '__main__':
    demo_parse_params()
