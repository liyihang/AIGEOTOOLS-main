"""
内容独特性检测模块
检测批量生成内容的相似度，避免多篇文章说同一件事
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import Counter
import math


class ContentUniquenessChecker:
    """内容独特性检查器"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Args:
            similarity_threshold: 相似度阈值，超过此值认为内容过于相似
        """
        self.similarity_threshold = similarity_threshold
    
    def check_batch_uniqueness(self, contents: List[str]) -> Dict:
        """
        批量检查内容独特性
        
        Args:
            contents: 内容列表
            
        Returns:
            检查结果
        """
        if len(contents) < 2:
            return {
                "is_unique": True,
                "message": "内容数量不足，无需检查"
            }
        
        # 计算两两相似度
        similarity_matrix = []
        high_similarity_pairs = []
        
        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                similarity = self.calculate_similarity(contents[i], contents[j])
                similarity_matrix.append({
                    "pair": (i, j),
                    "similarity": similarity
                })
                
                if similarity > self.similarity_threshold:
                    high_similarity_pairs.append({
                        "content_index_1": i,
                        "content_index_2": j,
                        "similarity": similarity,
                        "preview_1": contents[i][:100] + "...",
                        "preview_2": contents[j][:100] + "..."
                    })
        
        # 计算整体独特性分数
        if similarity_matrix:
            avg_similarity = sum(s["similarity"] for s in similarity_matrix) / len(similarity_matrix)
            max_similarity = max(s["similarity"] for s in similarity_matrix)
        else:
            avg_similarity = 0
            max_similarity = 0
        
        # 计算独特性分数 (0-100)
        uniqueness_score = max(0, (1 - avg_similarity) * 100)
        
        return {
            "is_unique": len(high_similarity_pairs) == 0,
            "total_contents": len(contents),
            "high_similarity_pairs": high_similarity_pairs,
            "avg_similarity": avg_similarity,
            "max_similarity": max_similarity,
            "uniqueness_score": uniqueness_score,
            "suggestions": self._generate_suggestions(high_similarity_pairs, avg_similarity)
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 (0-1)
        """
        # 使用多种方法综合计算
        
        # 1. 词汇重叠度 (Jaccard 相似度)
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))
        
        if not words1 or not words2:
            return 0
        
        intersection = words1 & words2
        union = words1 | words2
        jaccard_similarity = len(intersection) / len(union)
        
        # 2. 结构相似度 (基于句子结构)
        structure_similarity = self._calculate_structure_similarity(text1, text2)
        
        # 3. 关键信息重叠度
        key_info_similarity = self._calculate_key_info_similarity(text1, text2)
        
        # 综合相似度
        total_similarity = (
            jaccard_similarity * 0.4 +
            structure_similarity * 0.3 +
            key_info_similarity * 0.3
        )
        
        return total_similarity
    
    def _tokenize(self, text: str) -> List[str]:
        """分词（简单实现）"""
        # 移除标点符号，按空格分词
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.lower().split()
        
        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', 
                      '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
                      'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'shall'}
        
        return [w for w in words if w not in stop_words and len(w) > 1]
    
    def _calculate_structure_similarity(self, text1: str, text2: str) -> float:
        """计算结构相似度"""
        # 提取结构特征
        features1 = self._extract_structure_features(text1)
        features2 = self._extract_structure_features(text2)
        
        # 比较特征
        similarity = 0
        total_features = 0
        
        for key in set(features1.keys()) | set(features2.keys()):
            if key in features1 and key in features2:
                # 数值型特征
                if isinstance(features1[key], (int, float)):
                    max_val = max(abs(features1[key]), abs(features2[key]))
                    if max_val > 0:
                        similarity += 1 - abs(features1[key] - features2[key]) / max_val
                # 列表型特征
                elif isinstance(features1[key], list):
                    set1 = set(features1[key])
                    set2 = set(features2[key])
                    if set1 or set2:
                        similarity += len(set1 & set2) / len(set1 | set2)
            total_features += 1
        
        return similarity / total_features if total_features > 0 else 0
    
    def _extract_structure_features(self, text: str) -> Dict:
        """提取文本结构特征"""
        lines = text.split('\n')
        
        return {
            "total_chars": len(text),
            "total_lines": len(lines),
            "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
            "has_headers": any(line.startswith('#') for line in lines),
            "has_list": any(re.match(r'^\s*[-*•]\s', line) for line in lines),
            "has_numbered_list": any(re.match(r'^\s*\d+[.、]\s', line) for line in lines),
            "header_count": sum(1 for line in lines if line.startswith('#')),
            "paragraph_count": sum(1 for line in lines if line.strip() == '') + 1
        }
    
    def _calculate_key_info_similarity(self, text1: str, text2: str) -> float:
        """计算关键信息重叠度"""
        # 提取数字
        numbers1 = set(re.findall(r'\d+', text1))
        numbers2 = set(re.findall(r'\d+', text2))
        
        # 提取引号内容
        quotes1 = set(re.findall(r'[""「」『』](.+?)[""「」『』]', text1))
        quotes2 = set(re.findall(r'[""「」『』](.+?)[""「」『』]', text2))
        
        # 提取英文单词（可能是专业术语）
        english1 = set(re.findall(r'[A-Za-z]+', text1))
        english2 = set(re.findall(r'[A-Za-z]+', text2))
        
        # 计算重叠度
        number_overlap = len(numbers1 & numbers2) / max(len(numbers1 | numbers2), 1)
        quote_overlap = len(quotes1 & quotes2) / max(len(quotes1 | quotes2), 1)
        english_overlap = len(english1 & english2) / max(len(english1 | english2), 1)
        
        return (number_overlap + quote_overlap + english_overlap) / 3
    
    def _generate_suggestions(self, high_similarity_pairs: List[Dict], 
                              avg_similarity: float) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if high_similarity_pairs:
            suggestions.append(f"发现 {len(high_similarity_pairs)} 对高度相似的内容，建议修改其中一篇")
            
            # 给出具体建议
            for pair in high_similarity_pairs[:3]:
                suggestions.append(
                    f"内容 {pair['content_index_1']+1} 和 {pair['content_index_2']+1} "
                    f"相似度为 {pair['similarity']:.0%}，建议调整角度或添加独特案例"
                )
        
        if avg_similarity > 0.5:
            suggestions.append("整体相似度较高，建议：")
            suggestions.append("1. 为每篇内容选择不同的切入角度")
            suggestions.append("2. 添加独特的案例或数据")
            suggestions.append("3. 使用不同的表达方式和结构")
        
        if not suggestions:
            suggestions.append("内容独特性良好，无需修改")
        
        return suggestions
    
    def find_duplicate_sentences(self, contents: List[str], 
                                 min_length: int = 20) -> List[Dict]:
        """
        查找重复句子
        
        Args:
            contents: 内容列表
            min_length: 最小句子长度
            
        Returns:
            重复句子列表
        """
        # 提取所有句子
        sentence_sources = {}  # sentence -> [content_index]
        
        for i, content in enumerate(contents):
            sentences = re.split(r'[。！？.!?]', content)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) >= min_length:
                    if sentence not in sentence_sources:
                        sentence_sources[sentence] = []
                    sentence_sources[sentence].append(i)
        
        # 找出重复句子
        duplicates = []
        for sentence, sources in sentence_sources.items():
            if len(set(sources)) > 1:  # 出现在多篇内容中
                duplicates.append({
                    "sentence": sentence,
                    "appears_in": list(set(sources)),
                    "count": len(set(sources))
                })
        
        # 按出现次数排序
        duplicates.sort(key=lambda x: x["count"], reverse=True)
        
        return duplicates
    
    def generate_uniqueness_report(self, contents: List[str]) -> Dict:
        """
        生成独特性报告
        
        Args:
            contents: 内容列表
            
        Returns:
            报告数据
        """
        # 批量检查
        batch_result = self.check_batch_uniqueness(contents)
        
        # 查找重复句子
        duplicate_sentences = self.find_duplicate_sentences(contents)
        
        # 计算内容指纹
        fingerprints = [self._calculate_fingerprint(content) for content in contents]
        unique_fingerprints = len(set(fingerprints))
        
        return {
            **batch_result,
            "duplicate_sentences": duplicate_sentences,
            "unique_fingerprints": unique_fingerprints,
            "fingerprint_uniqueness": unique_fingerprints / len(contents) if contents else 0
        }
    
    def _calculate_fingerprint(self, text: str) -> str:
        """计算文本指纹"""
        # 提取关键特征
        words = self._tokenize(text)
        # 取前100个词的哈希作为指纹
        fingerprint_text = ' '.join(words[:100])
        return hashlib.md5(fingerprint_text.encode()).hexdigest()[:16]


def check_content_similarity(content1: str, content2: str) -> Dict:
    """
    检查两段内容的相似度
    
    Args:
        content1: 内容1
        content2: 内容2
        
    Returns:
        相似度分析结果
    """
    checker = ContentUniquenessChecker()
    
    similarity = checker.calculate_similarity(content1, content2)
    
    # 找出共同句子
    sentences1 = set(re.split(r'[。！？.!?]', content1))
    sentences2 = set(re.split(r'[。！？.!?]', content2))
    
    common_sentences = []
    for s1 in sentences1:
        s1 = s1.strip()
        if len(s1) >= 20:
            for s2 in sentences2:
                s2 = s2.strip()
                if s1 == s2:
                    common_sentences.append(s1)
    
    return {
        "similarity": similarity,
        "is_similar": similarity > 0.7,
        "common_sentences": common_sentences,
        "suggestion": "内容过于相似，建议修改" if similarity > 0.7 else "内容独特性良好"
    }
