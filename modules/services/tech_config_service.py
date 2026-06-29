"""
技术配置服务：封装 TechnicalConfigGenerator 的常用工作流，供 Tab（文章优化等）调用。
"""
from typing import Any, Dict, List, Optional

from modules.technical_config_generator import TechnicalConfigGenerator


def generate_robots_txt(
    base_url: str = "",
    allow_paths: Optional[List[str]] = None,
    disallow_paths: Optional[List[str]] = None,
    sitemap_url: str = "",
    user_agent: str = "*",
    crawl_delay: Optional[int] = None,
) -> str:
    """生成 robots.txt 内容。"""
    gen = TechnicalConfigGenerator()
    return gen.generate_robots_txt(
        base_url=base_url,
        allow_paths=allow_paths,
        disallow_paths=disallow_paths,
        sitemap_url=sitemap_url,
        user_agent=user_agent,
        crawl_delay=crawl_delay,
    )


def generate_sitemap_xml(
    base_url: str,
    urls: Optional[List[Dict[str, Any]]] = None,
    keywords: Optional[List[str]] = None,
    lastmod: Optional[str] = None,
) -> str:
    """生成 sitemap.xml 内容。"""
    gen = TechnicalConfigGenerator()
    return gen.generate_sitemap_xml(
        base_url=base_url,
        urls=urls,
        keywords=keywords,
        lastmod=lastmod,
    )
