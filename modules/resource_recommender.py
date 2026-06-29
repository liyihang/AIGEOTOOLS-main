"""
GEO 资源推荐模块
提供 GEO 代理、工具、论文等资源推荐，增强工具生态
"""
from typing import List, Dict, Optional
from datetime import datetime


class ResourceRecommender:
    """GEO 资源推荐器"""
    
    def __init__(self):
        # GEO 代理/服务列表
        self.agents = [
            {
                "name": "Perplexity AI",
                "description": "AI 搜索引擎，可用于验证 GEO 效果",
                "url": "https://www.perplexity.ai",
                "category": "AI 搜索",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["实时搜索", "引用来源", "多模型支持"]
            },
            {
                "name": "ChatGPT Search",
                "description": "OpenAI 的搜索功能，验证品牌在 AI 搜索中的表现",
                "url": "https://chat.openai.com",
                "category": "AI 搜索",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["GPT-4", "实时联网", "引用分析"]
            },
            {
                "name": "Google SGE",
                "description": "Google 搜索生成体验，了解 AI 搜索趋势",
                "url": "https://search.google",
                "category": "AI 搜索",
                "rating": "⭐⭐⭐⭐",
                "features": ["AI 摘要", "来源引用", "搜索结果"]
            },
            {
                "name": "Jasper AI",
                "description": "AI 内容创作平台，支持 SEO 优化内容生成",
                "url": "https://www.jasper.ai",
                "category": "内容生成",
                "rating": "⭐⭐⭐⭐",
                "features": ["模板丰富", "品牌声音", "SEO 优化"]
            },
            {
                "name": "Surfer SEO",
                "description": "SEO 内容优化工具，支持 SERP 分析",
                "url": "https://surferseo.com",
                "category": "SEO 工具",
                "rating": "⭐⭐⭐⭐",
                "features": ["内容评分", "关键词分析", "SERP 分析"]
            }
        ]
        
        # 工具推荐
        self.tools = [
            {
                "name": "Google Search Console",
                "description": "监控网站在 Google 搜索中的表现",
                "url": "https://search.google.com/search-console",
                "category": "搜索引擎工具",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["搜索分析", "索引监控", "性能报告"]
            },
            {
                "name": "Bing Webmaster Tools",
                "description": "Bing 搜索引擎的网站管理工具",
                "url": "https://www.bing.com/webmasters",
                "category": "搜索引擎工具",
                "rating": "⭐⭐⭐⭐",
                "features": ["索引提交", "搜索分析", "URL 检查"]
            },
            {
                "name": "Schema.org Validator",
                "description": "验证 JSON-LD Schema 标记是否正确",
                "url": "https://validator.schema.org",
                "category": "结构化数据",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["Schema 验证", "结构化数据测试", "错误检测"]
            },
            {
                "name": "Google Rich Results Test",
                "description": "测试网页是否支持 Google 富媒体搜索结果",
                "url": "https://search.google.com/test/rich-results",
                "category": "结构化数据",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["富媒体测试", "预览效果", "错误诊断"]
            },
            {
                "name": "PageSpeed Insights",
                "description": "分析网页性能，Core Web Vitals 指标",
                "url": "https://pagespeed.web.dev",
                "category": "性能工具",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["性能分析", "优化建议", "移动端测试"]
            },
            {
                "name": "Ahrefs",
                "description": "SEO 工具套件，关键词研究和竞品分析",
                "url": "https://ahrefs.com",
                "category": "SEO 工具",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["关键词研究", "反向链接分析", "竞品分析"]
            },
            {
                "name": "SEMrush",
                "description": "数字营销工具，SEO 和内容营销分析",
                "url": "https://www.semrush.com",
                "category": "SEO 工具",
                "rating": "⭐⭐⭐⭐⭐",
                "features": ["关键词研究", "站点审计", "内容优化"]
            },
            {
                "name": "Clearscope",
                "description": "AI 内容优化工具，提升内容相关性",
                "url": "https://www.clearscope.io",
                "category": "内容优化",
                "rating": "⭐⭐⭐⭐",
                "features": ["内容评分", "关键词建议", "竞品分析"]
            }
        ]
        
        # 论文/指南链接
        self.papers = [
            {
                "title": "GEO: Generative Engine Optimization (arXiv)",
                "description": "GEO 原始研究论文，定义了生成式引擎优化的概念和方法",
                "url": "https://arxiv.org/abs/2311.09735",
                "category": "学术论文",
                "date": "2023",
                "importance": "高"
            },
            {
                "title": "Google E-E-A-T Guidelines",
                "description": "Google 官方 E-E-A-T 指南，GEO 核心原则",
                "url": "https://developers.google.com/search/docs/fundamentals/creating-helpful-content",
                "category": "官方指南",
                "date": "2024",
                "importance": "高"
            },
            {
                "title": "Google Search Quality Rater Guidelines",
                "description": "Google 搜索质量评估指南，详细的 E-E-A-T 标准",
                "url": "static.googleusercontent.com/media/guidelines.raterhub.com/en//searchqualityevaluatorguidelines.pdf",
                "category": "官方指南",
                "date": "2024",
                "importance": "高"
            },
            {
                "title": "Schema.org Documentation",
                "description": "Schema.org 结构化数据完整文档",
                "url": "https://schema.org",
                "category": "技术文档",
                "date": "持续更新",
                "importance": "高"
            },
            {
                "title": "Google Structured Data Guidelines",
                "description": "Google 结构化数据指南和最佳实践",
                "url": "https://developers.google.com/search/docs/appearance/structured-data",
                "category": "技术文档",
                "date": "2024",
                "importance": "高"
            },
            {
                "title": "AI Search Optimization Guide",
                "description": "AI 搜索引擎优化最佳实践指南",
                "url": "https://www.searchenginejournal.com/ai-search-optimization",
                "category": "最佳实践",
                "date": "2024",
                "importance": "中"
            },
            {
                "title": "LLM Prompt Engineering Guide",
                "description": "大语言模型提示工程完整指南",
                "url": "https://www.promptingguide.ai",
                "category": "技术指南",
                "date": "持续更新",
                "importance": "中"
            },
            {
                "title": "Content Quality Guidelines",
                "description": "高质量内容创作指南",
                "url": "https://developers.google.com/search/docs/fundamentals/creating-helpful-content",
                "category": "内容指南",
                "date": "2024",
                "importance": "中"
            }
        ]
        
        # 社区资源
        self.communities = [
            {
                "name": "r/SEO (Reddit)",
                "description": "Reddit SEO 社区，讨论 SEO 和 GEO 策略",
                "url": "https://www.reddit.com/r/SEO",
                "category": "论坛社区",
                "rating": "⭐⭐⭐⭐⭐"
            },
            {
                "name": "r/ChatGPT (Reddit)",
                "description": "ChatGPT 社区，讨论 AI 搜索和 GEO 应用",
                "url": "https://www.reddit.com/r/ChatGPT",
                "category": "论坛社区",
                "rating": "⭐⭐⭐⭐"
            },
            {
                "name": "SEO Twitter/X Community",
                "description": "SEO 和 GEO 从业者 Twitter 社区",
                "url": "https://twitter.com/search?q=SEO%20GEO",
                "category": "社交媒体",
                "rating": "⭐⭐⭐⭐"
            },
            {
                "name": "Google Search Central Community",
                "description": "Google 官方搜索社区",
                "url": "https://support.google.com/webmasters/community",
                "category": "官方社区",
                "rating": "⭐⭐⭐⭐⭐"
            },
            {
                "name": "Moz Community",
                "description": "Moz SEO 社区，丰富的 SEO 资源",
                "url": "https://moz.com/community",
                "category": "论坛社区",
                "rating": "⭐⭐⭐⭐"
            }
        ]
    
    def get_agents(self, category: Optional[str] = None) -> List[Dict]:
        """获取 GEO 代理列表"""
        if category:
            return [agent for agent in self.agents if agent.get("category") == category]
        return self.agents
    
    def get_tools(self, category: Optional[str] = None) -> List[Dict]:
        """获取工具推荐列表"""
        if category:
            return [tool for tool in self.tools if tool.get("category") == category]
        return self.tools
    
    def get_papers(self, category: Optional[str] = None, importance: Optional[str] = None) -> List[Dict]:
        """获取论文/指南列表"""
        result = self.papers
        if category:
            result = [p for p in result if p.get("category") == category]
        if importance:
            result = [p for p in result if p.get("importance") == importance]
        return result
    
    def get_communities(self) -> List[Dict]:
        """获取社区资源列表"""
        return self.communities
    
    def get_resource_summary(self) -> Dict:
        """获取资源统计摘要"""
        return {
            "total": len(self.agents) + len(self.tools) + len(self.papers) + len(self.communities),
            "agents": len(self.agents),
            "tools": len(self.tools),
            "papers": len(self.papers),
            "communities": len(self.communities)
        }
    
    def search_resources(self, query: str, resource_type: Optional[str] = None) -> List[Dict]:
        """搜索资源"""
        query_lower = query.lower()
        results = []
        
        # 搜索所有资源
        all_resources = []
        
        if resource_type is None or resource_type == "agents":
            for agent in self.agents:
                agent["type"] = "agent"
                all_resources.append(agent)
        
        if resource_type is None or resource_type == "tools":
            for tool in self.tools:
                tool["type"] = "tool"
                all_resources.append(tool)
        
        if resource_type is None or resource_type == "papers":
            for paper in self.papers:
                paper["type"] = "paper"
                all_resources.append(paper)
        
        if resource_type is None or resource_type == "communities":
            for community in self.communities:
                community["type"] = "community"
                all_resources.append(community)
        
        # 搜索匹配
        for resource in all_resources:
            name = resource.get("name", resource.get("title", "")).lower()
            description = resource.get("description", "").lower()
            category = resource.get("category", "").lower()
            features = " ".join(resource.get("features", [])).lower()
            
            if (query_lower in name or 
                query_lower in description or 
                query_lower in category or 
                query_lower in features):
                results.append(resource)
        
        return results
