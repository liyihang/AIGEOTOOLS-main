"""
关键词数据增强模块
从历史验证数据中提取高价值关键词，反哺关键词生成
"""

import json
import logging
from typing import Dict, List, Optional, Any
from collections import Counter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KeywordDataEnhancer:
    """关键词数据增强器"""
    
    def __init__(self, storage):
        """
        Args:
            storage: DataStorage 实例
        """
        self.storage = storage
    
    def analyze_historical_performance(self, brand: str, 
                                       days: int = 30) -> Dict:
        """
        分析历史验证数据，提取高价值关键词
        
        Args:
            brand: 品牌名
            days: 分析最近 N 天的数据
            
        Returns:
            分析结果
        """
        # 获取历史验证结果
        verify_results = self.storage.get_verify_results(brand=brand)
        
        if not verify_results:
            return {
                "has_data": False,
                "message": "暂无历史验证数据"
            }
        
        # 转换为 DataFrame 便于分析
        import pandas as pd
        df = pd.DataFrame(verify_results)
        
        if df.empty:
            return {"has_data": False, "message": "暂无历史验证数据"}
        
        # 分析关键词表现
        keyword_performance = self._analyze_keyword_performance(df)
        
        # 提取高价值关键词
        high_value_keywords = self._extract_high_value_keywords(keyword_performance)
        
        # 分析搜索意图分布
        intent_distribution = self._analyze_intent_distribution(keyword_performance)
        
        # 生成关键词建议
        suggestions = self._generate_keyword_suggestions(keyword_performance)
        
        return {
            "has_data": True,
            "total_keywords": len(keyword_performance),
            "high_value_keywords": high_value_keywords,
            "intent_distribution": intent_distribution,
            "suggestions": suggestions,
            "keyword_details": keyword_performance
        }
    
    def _analyze_keyword_performance(self, df) -> List[Dict]:
        """分析每个关键词的表现"""
        keyword_stats = []
        
        for keyword in df["问题"].unique():
            keyword_df = df[df["问题"] == keyword]
            
            # 计算提及率
            mentioned = keyword_df[keyword_df["提及次数"] > 0]
            mention_rate = len(mentioned) / len(keyword_df) if len(keyword_df) > 0 else 0
            
            # 计算平均提及次数
            avg_mentions = keyword_df["提及次数"].mean()
            
            # 分析提及位置
            position_counts = Counter()
            for _, row in keyword_df.iterrows():
                pos = row.get("位置", "未提及")
                if pos and pos != "未提及":
                    position_counts[pos] += 1
            
            # 计算综合价值分数
            value_score = self._calculate_value_score(
                mention_rate, avg_mentions, position_counts
            )
            
            keyword_stats.append({
                "keyword": keyword,
                "total_verifications": len(keyword_df),
                "mention_rate": mention_rate,
                "avg_mentions": avg_mentions,
                "position_distribution": dict(position_counts),
                "value_score": value_score,
                "suggested_action": self._suggest_action(mention_rate, value_score)
            })
        
        # 按价值分数排序
        keyword_stats.sort(key=lambda x: x["value_score"], reverse=True)
        
        return keyword_stats
    
    def _calculate_value_score(self, mention_rate: float, 
                               avg_mentions: float,
                               position_counts: Counter) -> float:
        """
        计算关键词价值分数
        
        Args:
            mention_rate: 提及率
            avg_mentions: 平均提及次数
            position_counts: 位置分布
            
        Returns:
            价值分数 (0-100)
        """
        score = 0
        
        # 提及率权重 (40%)
        score += mention_rate * 40
        
        # 平均提及次数权重 (30%)
        mention_score = min(avg_mentions / 3, 1) * 30
        score += mention_score
        
        # 位置权重 (30%)
        total_mentions = sum(position_counts.values())
        if total_mentions > 0:
            front_ratio = position_counts.get("前1/3", 0) / total_mentions
            score += front_ratio * 30
        
        return score
    
    def _suggest_action(self, mention_rate: float, value_score: float) -> str:
        """根据表现建议操作"""
        if value_score >= 70:
            return "✅ 高价值关键词，继续保持"
        elif value_score >= 40:
            if mention_rate < 0.5:
                return "⚡ 提及率较低，建议优化内容"
            else:
                return "📈 有提升空间，建议增加深度"
        else:
            if mention_rate < 0.3:
                return "🔄 效果不佳，考虑替换关键词"
            else:
                return "🔍 价值较低，可减少投入"
    
    def _extract_high_value_keywords(self, keyword_performance: List[Dict], 
                                     top_n: int = 10) -> List[Dict]:
        """提取高价值关键词"""
        return keyword_performance[:top_n]
    
    def _analyze_intent_distribution(self, keyword_performance: List[Dict]) -> Dict:
        """分析搜索意图分布"""
        intent_keywords = {
            "对比": ["对比", "比较", "vs", "versus", "哪个好"],
            "评测": ["评测", "评价", "测评", "怎么样", "好不好"],
            "使用": ["怎么用", "如何使用", "教程", "入门", "指南"],
            "购买": ["价格", "多少钱", "购买", "付费", "免费"],
            "问题": ["问题", "错误", "失败", "怎么办", "解决"],
            "推荐": ["推荐", "最好", "排行", "排名", "前十"]
        }
        
        intent_counts = {intent: 0 for intent in intent_keywords}
        intent_keywords_map = {intent: [] for intent in intent_keywords}
        
        for kw_data in keyword_performance:
            keyword = kw_data["keyword"]
            categorized = False
            
            for intent, patterns in intent_keywords.items():
                if any(pattern in keyword for pattern in patterns):
                    intent_counts[intent] += 1
                    intent_keywords_map[intent].append(keyword)
                    categorized = True
                    break
            
            if not categorized:
                intent_counts["其他"] = intent_counts.get("其他", 0) + 1
        
        return {
            "counts": intent_counts,
            "keywords": intent_keywords_map
        }
    
    def _generate_keyword_suggestions(self, keyword_performance: List[Dict]) -> List[Dict]:
        """生成关键词优化建议"""
        suggestions = []
        
        # 找出低效关键词
        low_performers = [kw for kw in keyword_performance if kw["value_score"] < 30]
        if low_performers:
            suggestions.append({
                "type": "replace",
                "priority": "high",
                "message": f"有 {len(low_performers)} 个关键词效果不佳，建议替换",
                "keywords": [kw["keyword"] for kw in low_performers[:3]]
            })
        
        # 找出高价值关键词
        high_performers = [kw for kw in keyword_performance if kw["value_score"] >= 70]
        if high_performers:
            suggestions.append({
                "type": "expand",
                "priority": "medium",
                "message": f"有 {len(high_performers)} 个高价值关键词，建议扩展相关内容",
                "keywords": [kw["keyword"] for kw in high_performers[:3]]
            })
        
        # 找出提及率低但有潜力的关键词
        potential_keywords = [
            kw for kw in keyword_performance 
            if 0.3 <= kw["mention_rate"] < 0.5 and kw["total_verifications"] >= 3
        ]
        if potential_keywords:
            suggestions.append({
                "type": "optimize",
                "priority": "medium",
                "message": f"有 {len(potential_keywords)} 个关键词有提升空间，建议优化内容",
                "keywords": [kw["keyword"] for kw in potential_keywords[:3]]
            })
        
        return suggestions
    
    def generate_enhanced_keyword_prompt(self, brand: str, advantages: str,
                                         existing_keywords: List[str] = None) -> str:
        """
        生成增强的关键词生成提示词
        
        Args:
            brand: 品牌名
            advantages: 品牌优势
            existing_keywords: 已有关键词列表
            
        Returns:
            增强的提示词
        """
        # 获取历史分析
        analysis = self.analyze_historical_performance(brand)
        
        prompt = f"""你是一个 GEO（生成式引擎优化）关键词策略专家。

品牌信息：
- 品牌名：{brand}
- 品牌优势：{advantages}

"""
        
        if analysis.get("has_data"):
            prompt += """历史验证数据分析：
"""
            # 添加高价值关键词
            high_value = analysis.get("high_value_keywords", [])
            if high_value:
                prompt += "\n高价值关键词（已验证有效）：\n"
                for kw in high_value[:5]:
                    prompt += f"- {kw['keyword']} (提及率: {kw['mention_rate']:.0%}, 价值分: {kw['value_score']:.0f})\n"
            
            # 添加优化建议
            suggestions = analysis.get("suggestions", [])
            if suggestions:
                prompt += "\n优化建议：\n"
                for suggestion in suggestions:
                    prompt += f"- {suggestion['message']}\n"
            
            # 添加意图分布
            intent_dist = analysis.get("intent_distribution", {}).get("counts", {})
            if intent_dist:
                prompt += "\n搜索意图分布：\n"
                for intent, count in sorted(intent_dist.items(), key=lambda x: x[1], reverse=True):
                    if count > 0:
                        prompt += f"- {intent}: {count} 个关键词\n"
        
        if existing_keywords:
            prompt += f"\n已有关键词（避免重复）：\n"
            for kw in existing_keywords[:10]:
                prompt += f"- {kw}\n"
        
        prompt += """
请生成 20 个新的 GEO 优化关键词，要求：
1. 70% 泛词（行业相关）+ 30% 品牌词
2. 覆盖多种搜索意图：对比、评测、使用、购买、问题、推荐
3. 关键词长度 12-28 字，口语化，符合用户真实搜索习惯
4. 每个关键词附带：category（类别）、intent（意图）、estimated_value（预估价值 1-5）

输出 JSON 数组格式：
[
  {
    "keyword": "关键词内容",
    "category": "类别",
    "intent": "意图",
    "estimated_value": 4
  }
]
"""
        
        return prompt
    
    def get_keyword_trends(self, brand: str, keyword: str, 
                           days: int = 30) -> Dict:
        """
        获取关键词趋势数据
        
        Args:
            brand: 品牌名
            keyword: 关键词
            days: 分析天数
            
        Returns:
            趋势数据
        """
        verify_results = self.storage.get_verify_results(brand=brand)
        
        if not verify_results:
            return {"has_data": False}
        
        import pandas as pd
        df = pd.DataFrame(verify_results)
        
        # 过滤指定关键词
        keyword_df = df[df["问题"] == keyword]
        
        if keyword_df.empty:
            return {"has_data": False, "message": f"未找到关键词 '{keyword}' 的验证数据"}
        
        # 按日期分组
        if "验证时间" in keyword_df.columns:
            keyword_df["日期"] = pd.to_datetime(keyword_df["验证时间"]).dt.date
            daily_stats = keyword_df.groupby("日期").agg({
                "提及次数": "mean",
                "问题": "count"
            }).rename(columns={"问题": "验证次数"})
            
            return {
                "has_data": True,
                "keyword": keyword,
                "daily_stats": daily_stats.to_dict("records"),
                "overall_mention_rate": len(keyword_df[keyword_df["提及次数"] > 0]) / len(keyword_df)
            }
        
        return {"has_data": False, "message": "缺少时间戳数据"}
