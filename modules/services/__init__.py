"""
服务层：封装对 modules 业务模块的常用工作流，供 UI 层（tab_*.py）按需调用。

- 不替代现有业务类，仅做薄封装与流程编排。
- Tab 可继续直接使用 modules.*，也可逐步改为调用本层以集中错误处理、参数归一化等。
"""

from . import schema_service
from . import tech_config_service

__all__ = ["schema_service", "tech_config_service"]
