# 📚 项目文档索引

本文档提供项目所有文档的快速导航。

## 🚀 快速开始

- [快速开始指南](docs/guides/QUICK_START_GUIDE.md) - 新用户入门指南
- [平台设置指南](docs/guides/PLATFORM_SETUP.md) - API Key 配置说明

## 📖 功能文档

所有功能模块的详细说明：

### 核心功能

- [配置优化器](docs/features/CONFIG_OPTIMIZER_FEATURE.md)
- [内容质量指标](docs/features/CONTENT_METRICS_FEATURE.md)
- [内容质量评分](docs/features/CONTENT_SCORER_FEATURE.md)
- [E-E-A-T 评估与强化](docs/features/EEAT_FEATURE.md)
- [事实密度增强](docs/features/FACT_DENSITY_FEATURE.md)
- [JSON-LD Schema 生成](docs/features/JSON_LD_SCHEMA_FEATURE.md)
- [关键词挖掘](docs/features/KEYWORD_MINING_FEATURE.md)
- [多模态提示生成](docs/features/MULTIMODAL_FEATURE.md)
- [负面监控](docs/features/NEGATIVE_MONITOR_FEATURE.md)
- [优化技巧](docs/features/OPTIMIZATION_TECHNIQUES_FEATURE.md)
- [资源推荐](docs/features/RESOURCE_RECOMMENDER_FEATURE.md)
- [ROI 分析](docs/features/ROI_ANALYSIS_FEATURE.md)
- [语义扩展](docs/features/SEMANTIC_EXPANSION_FEATURE.md)
- [技术配置生成](docs/features/TECHNICAL_CONFIG_FEATURE.md)
- [话题集群](docs/features/TOPIC_CLUSTER_FEATURE.md)
- [工作流自动化](docs/features/WORKFLOW_AUTOMATION_FEATURE.md)

### GEO 增强功能（新增）

- [品牌知识库（RAG）](docs/features/KNOWLEDGE_BASE_FEATURE.md) - 基于 RAG 的知识库管理
- [AI 搜索验证](docs/features/AI_SEARCH_VERIFIER_FEATURE.md) - 使用真实搜索引擎验证品牌提及
- [内容独特性检测](docs/features/CONTENT_UNIQUENESS_FEATURE.md) - 批量内容相似度检测
- [关键词数据增强](docs/features/KEYWORD_DATA_ENHANCER_FEATURE.md) - 基于历史数据优化关键词策略
- [LLM 工厂模块](docs/features/LLM_FACTORY_FEATURE.md) - 统一的 LLM 客户端构建接口

## 📊 分析报告

- [Tab 与模块映射](docs/analysis/TABS_TO_MODULES_ANALYSIS.md) - 主导航 Tab 与 `modules/ui/tab_*.py` 对应关系
- [Tab 拆分模式](docs/analysis/TAB_SPLIT_PATTERN.md) - Tab 拆分模式说明
- [分析准确性报告](docs/analysis/ANALYSIS_ACCURACY_REPORT.md)
- [文档反向验证](docs/analysis/DOCUMENTATION_REVERSE_VERIFICATION.md)
- [功能验证报告](docs/analysis/FUNCTION_VERIFICATION_REPORT.md)

## 📘 指南文档

- [决策指南](docs/guides/DECISION_GUIDE.md)
- [布局升级指南](docs/guides/LAYOUT_UPGRADE_GUIDE.md)
- [平台设置指南](docs/guides/PLATFORM_SETUP.md)
- [快速开始指南](docs/guides/QUICK_START_GUIDE.md)
- [数据存储指南](docs/guides/STORAGE_GUIDE.md)
- [根目录文件管理规则](docs/guides/ROOT_DIRECTORY_RULES.md)

## 🔧 实现文档

- [高级功能](docs/implementation/ADVANCED_FEATURES.md)
- [完整功能列表](docs/implementation/FEATURES_COMPLETE_LIST.md)
- [实现总结](docs/implementation/IMPLEMENTATION_SUMMARY.md)
- [集成说明](docs/implementation/INTEGRATION_NOTES.md)
- [平台同步分析](docs/implementation/PLATFORM_SYNC_ANALYSIS.md)
- [平台同步实现](docs/implementation/PLATFORM_SYNC_IMPLEMENTATION.md)
- [平台同步测试](docs/implementation/PLATFORM_SYNC_TEST.md)

## 🖥️ 前端结构与开发流程（拆分后）

- **入口**：`geo_tool.py` 为 Streamlit 单入口，负责侧边栏配置、全局状态、主导航 Tabs 与对各 Tab 模块的调用。
- **Tab 模块**：`modules/ui/tab_*.py`，每个文件提供 `render_tab_*(...)`，由主入口在对应 `with tabN:` 内调用。
- **公共 UI**：`modules/ui/components.py` 提供 `sanitize_filename`、`render_section_header`、`render_download_button`、`render_tab_top_with_clear` 等，供各 Tab 复用。
- **状态与主题**：`modules/ui/state.py` 统一初始化 `st.session_state`；`modules/ui/theme.py` 注入全局 CSS。
- **服务层**：`modules/services/` 封装对业务模块的常用工作流（如 `schema_service`、`tech_config_service`），Tab 可按需调用。

**新增一个 Tab 的流程**：

1. 在 `modules/ui/` 下新建 `tab_新功能.py`，实现 `def render_tab_新功能(...)`，接收主入口传入的 `storage`、`ss_init`、`brand` 等依赖。
2. 在 `geo_tool.py` 的 `st.tabs([...])` 中增加新 Tab 标签，并增加 `with tabN:` 块内调用 `tab_新功能.render_tab_新功能(...)`。
3. 在 `modules/ui/__init__.py` 的 `from . import (...)` 中增加 `tab_新功能`。

详见：[Tab 与模块映射](docs/analysis/TABS_TO_MODULES_ANALYSIS.md)、[Tab 拆分模式](docs/analysis/TAB_SPLIT_PATTERN.md)。

## 📁 项目结构

项目采用模块化架构，详见 [README.md](README.md) 中的项目结构说明。

## 🔍 查找文档

### 按类型查找

- **功能说明** → `docs/features/`
- **分析报告** → `docs/analysis/`
- **使用指南** → `docs/guides/`
- **实现细节** → `docs/implementation/`

### 按主题查找

- **快速入门** → [快速开始指南](docs/guides/QUICK_START_GUIDE.md)
- **功能配置** → [平台设置指南](docs/guides/PLATFORM_SETUP.md)
- **数据存储** → [数据存储指南](docs/guides/STORAGE_GUIDE.md)
- **平台同步** → [平台同步实现](docs/implementation/PLATFORM_SYNC_IMPLEMENTATION.md)
- **知识库** → [品牌知识库功能](docs/features/KNOWLEDGE_BASE_FEATURE.md)
- **AI 搜索验证** → [AI 搜索验证功能](docs/features/AI_SEARCH_VERIFIER_FEATURE.md)

---

💡 **提示**：如果找不到需要的文档，请查看 [README.md](README.md) 或使用搜索功能。