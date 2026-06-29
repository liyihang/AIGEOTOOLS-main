"""
Schema 服务：封装 SchemaGenerator 的常用工作流，供 Tab（文章优化、自动创作等）调用。
"""
from typing import Any, Dict, List, Tuple

from modules.schema_generator import SchemaGenerator


def get_combined_schema(
    brand_name: str,
    advantages: str = "",
    schema_types: List[str] = None,
    **kwargs: Any,
) -> Dict:
    """生成组合 JSON-LD Schema。返回可序列化为 JSON 的字典。"""
    gen = SchemaGenerator()
    return gen.generate_combined_schema(
        brand_name=brand_name,
        advantages=advantages,
        schema_types=schema_types,
        **kwargs,
    )


def get_combined_schema_and_html(
    brand_name: str,
    advantages: str = "",
    schema_types: List[str] = None,
    **kwargs: Any,
) -> Tuple[Dict, str]:
    """生成组合 Schema 及其 HTML script 标签片段。返回 (schema_dict, html_script_str)。"""
    gen = SchemaGenerator()
    schema = gen.generate_combined_schema(
        brand_name=brand_name,
        advantages=advantages,
        schema_types=schema_types or ["Organization", "SoftwareApplication"],
        **kwargs,
    )
    html = gen.generate_html_script_tag(schema)
    return schema, html
