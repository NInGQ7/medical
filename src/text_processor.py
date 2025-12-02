# -*- coding: utf-8 -*-
"""
文本处理工具模块
包含文本标准化、相似度计算、中文分词等功能
"""

import re
import jieba
from typing import List, Optional
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from config.synonyms import MODIFIER_WORDS, NEGATIVE_WORDS


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        """初始化"""
        self.modifier_pattern = '|'.join([re.escape(word) for word in MODIFIER_WORDS])
    
    def normalize_text(self, text: str, remove_modifiers: bool = False) -> str:
        """
        文本标准化处理
        
        Args:
            text: 原始文本
            remove_modifiers: 是否移除修饰词
            
        Returns:
            标准化后的文本
        """
        if not text or text in NEGATIVE_WORDS:
            return ""
        
        # 转字符串并去除首尾空格
        text = str(text).strip()
        
        # 转小写
        text = text.lower()
        
        # 统一空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除修饰词
        if remove_modifiers and self.modifier_pattern:
            text = re.sub(self.modifier_pattern, '', text)
        
        return text.strip()
    
    def remove_punctuation(self, text: str) -> str:
        """
        移除标点符号
        
        Args:
            text: 原始文本
            
        Returns:
            移除标点后的文本
        """
        # 保留中文、英文、数字
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        return text
    
    def extract_chinese_words(self, text: str) -> List[str]:
        """
        提取中文词汇
        
        Args:
            text: 原始文本
            
        Returns:
            中文词汇列表
        """
        words = jieba.lcut(text)
        return [w for w in words if re.search(r'[\u4e00-\u9fff]', w)]
    
    def calculate_similarity(self, text1: str, text2: str, method: str = 'fuzz') -> float:
        """
        计算文本相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            method: 相似度计算方法 ('fuzz', 'ratio', 'token_sort', 'token_set')
            
        Returns:
            相似度分数 (0-100)
        """
        if not text1 or not text2:
            return 0.0
        
        # 标准化文本
        text1 = self.normalize_text(text1)
        text2 = self.normalize_text(text2)
        
        if method == 'fuzz':
            return fuzz.ratio(text1, text2)
        elif method == 'ratio':
            return SequenceMatcher(None, text1, text2).ratio() * 100
        elif method == 'token_sort':
            return fuzz.token_sort_ratio(text1, text2)
        elif method == 'token_set':
            return fuzz.token_set_ratio(text1, text2)
        else:
            return fuzz.ratio(text1, text2)
    
    def is_similar(self, text1: str, text2: str, threshold: float = 80.0) -> bool:
        """
        判断两个文本是否相似
        
        Args:
            text1: 文本1
            text2: 文本2
            threshold: 相似度阈值
            
        Returns:
            是否相似
        """
        similarity = self.calculate_similarity(text1, text2)
        return similarity >= threshold
    
    def find_most_similar(self, target: str, candidates: List[str], 
                          threshold: float = 80.0) -> Optional[str]:
        """
        从候选列表中找到最相似的文本
        
        Args:
            target: 目标文本
            candidates: 候选文本列表
            threshold: 相似度阈值
            
        Returns:
            最相似的文本，如果没有超过阈值则返回None
        """
        if not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.calculate_similarity(target, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        
        return best_match
    
    def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 原始文本
            top_k: 提取关键词数量
            
        Returns:
            关键词列表
        """
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_k)
        return keywords
    
    def has_keyword(self, text: str, keywords: List[str]) -> bool:
        """
        检查文本是否包含关键词
        
        Args:
            text: 文本
            keywords: 关键词列表
            
        Returns:
            是否包含关键词
        """
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False
