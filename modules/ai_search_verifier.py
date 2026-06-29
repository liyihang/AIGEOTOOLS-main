"""
AI 搜索验证模块
支持使用真实的 AI 搜索引擎（Perplexity、ChatGPT Search）验证品牌提及
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    response: str
    sources: List[Dict[str, str]]
    brand_mentioned: bool
    mention_count: int
    mention_positions: List[str]
    sentiment: str  # positive, neutral, negative


class AISearchVerifier:
    """AI 搜索验证器"""
    
    def __init__(self, perplexity_api_key: Optional[str] = None):
        """
        Args:
            perplexity_api_key: Perplexity API Key
        """
        self.perplexity_api_key = perplexity_api_key
    
    def verify_with_perplexity(self, query: str, brand: str) -> Dict:
        """
        使用 Perplexity API 验证品牌提及
        
        Args:
            query: 搜索查询
            brand: 品牌名
            
        Returns:
            验证结果
        """
        if not self.perplexity_api_key:
            return self._mock_verification(query, brand)
        
        try:
            import httpx
            
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer the user's question based on real-time search results. Be factual and cite your sources."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1,
                "return_citations": True,
                "search_recency_filter": "month"
            }
            
            response = httpx.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                citations = result.get("citations", [])
                
                # 分析品牌提及
                mention_analysis = self._analyze_mention(content, brand)
                
                return {
                    "success": True,
                    "query": query,
                    "brand": brand,
                    "response": content,
                    "sources": citations,
                    "mention_count": mention_analysis["count"],
                    "mention_positions": mention_analysis["positions"],
                    "mentioned": mention_analysis["count"] > 0,
                    "sentiment": mention_analysis["sentiment"]
                }
            else:
                logger.error(f"Perplexity API 错误: {response.status_code} {response.text}")
                return {"success": False, "error": f"API 错误: {response.status_code}"}
                
        except ImportError:
            logger.warning("httpx 未安装，无法调用 Perplexity API")
            return self._mock_verification(query, brand)
        except Exception as e:
            logger.error(f"Perplexity 验证失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _mock_verification(self, query: str, brand: str) -> Dict:
        """模拟验证（当 API 不可用时）"""
        return {
            "success": True,
            "query": query,
            "brand": brand,
            "response": f"（模拟结果）关于 '{query}' 的搜索结果需要配置 Perplexity API Key 才能获取真实数据。",
            "sources": [],
            "mention_count": 0,
            "mention_positions": [],
            "mentioned": False,
            "sentiment": "neutral",
            "is_mock": True
        }
    
    def _analyze_mention(self, text: str, brand: str) -> Dict:
        """
        分析文本中的品牌提及
        
        Args:
            text: 文本内容
            brand: 品牌名
            
        Returns:
            提及分析结果
        """
        text_lower = text.lower()
        brand_lower = brand.lower()
        
        # 计算提及次数
        count = text_lower.count(brand_lower)
        
        # 分析提及位置
        positions = []
        if count > 0:
            total_len = len(text)
            for match in re.finditer(re.escape(brand_lower), text_lower):
                pos_ratio = match.start() / total_len
                if pos_ratio < 0.33:
                    positions.append("前1/3")
                elif pos_ratio < 0.67:
                    positions.append("中1/3")
                else:
                    positions.append("后1/3")
        
        # 分析情感（简单规则）
        sentiment = self._analyze_sentiment(text, brand)
        
        return {
            "count": count,
            "positions": positions,
            "sentiment": sentiment
        }
    
    def _analyze_sentiment(self, text: str, brand: str) -> str:
        """
        分析品牌提及的情感
        
        Args:
            text: 文本内容
            brand: 品牌名
            
        Returns:
            情感标签 (positive, neutral, negative)
        """
        text_lower = text.lower()
        brand_lower = brand.lower()
        
        # 正面词汇
        positive_words = [
            "优秀", "出色", "领先", "推荐", "首选", "最佳", "强大", "高效",
            "创新", "专业", "可靠", "稳定", "卓越", "突出", "显著",
            "excellent", "outstanding", "leading", "recommended", "best",
            "powerful", "efficient", "innovative", "professional", "reliable"
        ]
        
        # 负面词汇
        negative_words = [
            "问题", "缺陷", "不足", "失败", "风险", "警告", "谨慎", "避免",
            "差", "慢", "贵", "复杂", "困难", "不稳定",
            "issue", "problem", "defect", "risk", "warning", "avoid",
            "poor", "slow", "expensive", "complex", "difficult", "unstable"
        ]
        
        # 获取品牌附近的上下文（前后50字符）
        contexts = []
        for match in re.finditer(re.escape(brand_lower), text_lower):
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            contexts.append(text_lower[start:end])
        
        if not contexts:
            return "neutral"
        
        # 计算情感分数
        positive_score = 0
        negative_score = 0
        
        for context in contexts:
            for word in positive_words:
                if word in context:
                    positive_score += 1
            for word in negative_words:
                if word in context:
                    negative_score += 1
        
        if positive_score > negative_score * 1.5:
            return "positive"
        elif negative_score > positive_score * 1.5:
            return "negative"
        else:
            return "neutral"
    
    def batch_verify(self, queries: List[str], brand: str, 
                     api_key: Optional[str] = None) -> List[Dict]:
        """
        批量验证多个查询
        
        Args:
            queries: 查询列表
            brand: 品牌名
            api_key: API Key（可选，覆盖初始化时的 key）
            
        Returns:
            验证结果列表
        """
        if api_key:
            self.perplexity_api_key = api_key
        
        results = []
        for query in queries:
            result = self.verify_with_perplexity(query, brand)
            results.append(result)
        
        return results
    
    def generate_verification_report(self, results: List[Dict]) -> Dict:
        """
        生成验证报告
        
        Args:
            results: 验证结果列表
            
        Returns:
            报告数据
        """
        total = len(results)
        mentioned = sum(1 for r in results if r.get("mentioned", False))
        
        mention_rate = mentioned / total if total > 0 else 0
        
        # 统计情感分布
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for r in results:
            sentiment = r.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # 计算平均提及次数
        total_mentions = sum(r.get("mention_count", 0) for r in results)
        avg_mentions = total_mentions / total if total > 0 else 0
        
        return {
            "total_queries": total,
            "mentioned_count": mentioned,
            "mention_rate": mention_rate,
            "avg_mentions_per_query": avg_mentions,
            "sentiment_distribution": sentiment_counts,
            "top_mentioned_queries": [
                r["query"] for r in results 
                if r.get("mentioned", False)
            ][:5],
            "not_mentioned_queries": [
                r["query"] for r in results 
                if not r.get("mentioned", False)
            ][:5]
        }


class SemanticMentionDetector:
    """语义级提及检测器"""
    
    def __init__(self):
        # 品牌别名/同义词映射
        self.brand_aliases: Dict[str, List[str]] = {}
    
    def add_brand_aliases(self, brand: str, aliases: List[str]):
        """
        添加品牌别名
        
        Args:
            brand: 品牌名
            aliases: 别名列表
        """
        self.brand_aliases[brand.lower()] = [a.lower() for a in aliases]
    
    def detect_mention(self, text: str, brand: str) -> Dict:
        """
        语义级提及检测
        
        Args:
            text: 文本内容
            brand: 品牌名
            
        Returns:
            检测结果
        """
        text_lower = text.lower()
        brand_lower = brand.lower()
        
        # 直接提及
        direct_count = text_lower.count(brand_lower)
        
        # 别名提及
        aliases = self.brand_aliases.get(brand_lower, [])
        alias_counts = {}
        for alias in aliases:
            count = text_lower.count(alias)
            if count > 0:
                alias_counts[alias] = count
        
        # 总提及次数
        total_count = direct_count + sum(alias_counts.values())
        
        # 判断提及语境
        contexts = self._extract_contexts(text, brand_lower, aliases)
        
        return {
            "brand": brand,
            "direct_count": direct_count,
            "alias_counts": alias_counts,
            "total_count": total_count,
            "contexts": contexts,
            "is_mentioned": total_count > 0
        }
    
    def _extract_contexts(self, text: str, brand_lower: str, 
                          aliases: List[str]) -> List[Dict]:
        """提取提及上下文"""
        contexts = []
        text_lower = text.lower()
        
        # 查找所有提及位置
        all_patterns = [brand_lower] + aliases
        
        for pattern in all_patterns:
            for match in re.finditer(re.escape(pattern), text_lower):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                contexts.append({
                    "pattern": pattern,
                    "context": context,
                    "position": match.start()
                })
        
        return contexts


def verify_content_quality(content: str, brand: str, 
                          knowledge_base=None) -> Dict:
    """
    综合验证内容质量
    
    Args:
        content: 内容文本
        brand: 品牌名
        knowledge_base: 知识库实例（可选）
        
    Returns:
        质量评估结果
    """
    from modules.knowledge_base import SourceVerifier
    
    verifier = SourceVerifier()
    
    # 来源质量评估
    source_quality = verifier.assess_source_quality(content)
    
    # 品牌提及分析
    detector = SemanticMentionDetector()
    mention_result = detector.detect_mention(content, brand)
    
    # 计算综合分数
    score = 0
    max_score = 100
    
    # 来源质量 (40分)
    score += min(40, source_quality["quality_score"] * 0.4)
    
    # 品牌提及 (30分)
    if mention_result["is_mentioned"]:
        mention_score = min(30, mention_result["total_count"] * 5)
        score += mention_score
    
    # 内容结构 (30分)
    structure_score = 0
    if "##" in content:  # 有标题
        structure_score += 10
    if re.search(r'\d+[.、]', content):  # 有列表
        structure_score += 10
    if "?" in content or "？" in content:  # 有问答
        structure_score += 10
    score += structure_score
    
    return {
        "total_score": score,
        "max_score": max_score,
        "source_quality": source_quality,
        "mention_analysis": mention_result,
        "structure_score": structure_score,
        "suggestions": _generate_suggestions(source_quality, mention_result, structure_score)
    }


def _generate_suggestions(source_quality: Dict, mention_result: Dict, 
                          structure_score: int) -> List[str]:
    """生成改进建议"""
    suggestions = []
    
    if source_quality["quality_score"] < 50:
        suggestions.append("来源质量较低，建议添加真实的行业报告或数据来源")
    
    if not mention_result["is_mentioned"]:
        suggestions.append("内容中未提及品牌，建议在合适位置自然植入品牌信息")
    elif mention_result["total_count"] < 2:
        suggestions.append("品牌提及次数较少，建议增加到 2-3 次")
    
    if structure_score < 20:
        suggestions.append("内容结构不够清晰，建议添加标题、列表或 FAQ")
    
    return suggestions
