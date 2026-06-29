# Tab3：文章优化（从 geo_tool.py 迁移，通过 render_tab_optimize() 供主入口调用。）

import re

import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from modules.eeat_enhancer import EEATEnhancer
from modules.fact_density_enhancer import FactDensityEnhancer
from modules.optimization_techniques import OptimizationTechniqueManager
from modules.schema_generator import SchemaGenerator
from modules.technical_config_generator import TechnicalConfigGenerator
from modules.ui.components import sanitize_filename, safe_decode_uploaded, render_tab_top_with_clear


def render_tab_optimize(
    storage,
    ss_init,
    gen_llm,
    brand: str,
    advantages: str,
    cfg: dict,
    record_api_cost,
    model_defaults,
) -> None:
    """渲染 Tab3：文章优化。由主入口在 with tab3 内调用。"""
    # 标题和清空按钮
    def _clear_optimize_state():
        st.session_state.optimized_article = ""
        st.session_state.opt_changes = ""

    render_tab_top_with_clear(
        title="🔧 文章优化",
        caption="优化已有文章，生成结构化数据和技术配置，提升 GEO 效果",
        clear_key="opt_clear",
        on_clear=_clear_optimize_state,
    )

    # === 文章优化功能（主流程） ===
    st.markdown("**✏️ 文章内容优化**")

    with st.container(border=True):
        st.markdown("粘贴或上传已写文章，一键提升 GEO 效果（结构化、可引用、自然植入品牌）")

        # 输入方式与文章内容放在表单外，以便粘贴/上传后能触发重跑，从而正确更新「开始优化」按钮的可用状态
        input_mode = st.radio(
            "输入方式",
            ["粘贴文本", "上传文件（TXT/MD）"],
            horizontal=True,
            key="opt_input_mode",
        )
        if input_mode == "粘贴文本":
            original_article = st.text_area(
                "粘贴文章内容", height=360, key="opt_text"
            )
        else:
            uploaded = st.file_uploader(
                "上传 TXT 或 MD 文件",
                type=["txt", "md"],
                key="opt_uploader",
            )
            original_article = ""
            if uploaded:
                try:
                    original_article = safe_decode_uploaded(uploaded) or ""
                except Exception as e:
                    st.error(f"上传文件解析失败：{e}")
                    original_article = ""
                if original_article:
                    st.text_area(
                        "上传内容预览",
                        original_article,
                        height=200,
                        disabled=True,
                        key="opt_upload_preview",
                    )

        with st.form("opt_form", clear_on_submit=False):
            target_platform = st.selectbox(
                "目标平台（影响文风，可选）",
                [
                    "通用优化",
                    "知乎（专业问答）",
                    "CSDN（技术博客）",
                    "GitHub（README/文档）",
                    "B站（视频脚本）",
                    "头条号（资讯软文）",
                    "微信公众号（长文）",
                    "抖音图文（短内容）",
                    "百家号（资讯）",
                    "网易号（资讯）",
                    "企鹅号（资讯）",
                    "简书（文艺）",
                ],
                index=[
                    "通用优化",
                    "知乎（专业问答）",
                    "CSDN（技术博客）",
                    "GitHub（README/文档）",
                    "B站（视频脚本）",
                    "头条号（资讯软文）",
                    "微信公众号（长文）",
                    "抖音图文（短内容）",
                    "百家号（资讯）",
                    "网易号（资讯）",
                    "企鹅号（资讯）",
                    "简书（文艺）",
                ].index(
                    st.session_state.opt_platform
                    if st.session_state.opt_platform
                    in [
                        "通用优化",
                        "知乎（专业问答）",
                        "CSDN（技术博客）",
                        "GitHub（README/文档）",
                        "B站（视频脚本）",
                        "头条号（资讯软文）",
                        "微信公众号（长文）",
                        "抖音图文（短内容）",
                        "百家号（资讯）",
                        "网易号（资讯）",
                        "企鹅号（资讯）",
                        "简书（文艺）",
                    ]
                    else 0
                ),
                key="opt_platform_sel",
            )

            # 高级优化技巧选择器（可选）
            with st.expander("🎨 高级优化技巧（可选）", expanded=False):
                opt_technique_manager = OptimizationTechniqueManager()
                opt_all_techniques = opt_technique_manager.list_techniques()
                opt_technique_options = [
                    f"{tech['icon']} {tech['name']}" for tech in opt_all_techniques
                ]

                opt_selected_technique_names = st.multiselect(
                    "选择要应用的优化技巧（可多选）",
                    options=opt_technique_options,
                    default=[],
                    key="opt_techniques",
                    help="可选，提高 GEO 效果。技巧会动态调整文章优化策略。",
                )

                # 显示选择的技巧描述
                if opt_selected_technique_names:
                    st.caption("已选择：" + "、".join(opt_selected_technique_names))
                    with st.expander("查看技巧说明", expanded=False):
                        for tech_name in opt_selected_technique_names:
                            tech_icon_name = (
                                tech_name.split(" ", 1)[1]
                                if " " in tech_name
                                else tech_name
                            )
                            for tech in opt_all_techniques:
                                if tech["name"] == tech_icon_name:
                                    st.markdown(f"**{tech['icon']} {tech['name']}**")
                                    st.caption(tech["description"])
                                    break

            run_opt_disabled = (
                (not st.session_state.cfg_valid)
                or (gen_llm is None)
                or (not original_article.strip())
            )
            run_opt = st.form_submit_button(
                "开始优化", use_container_width=True, disabled=run_opt_disabled
            )

            if run_opt_disabled:
                if not original_article.strip():
                    st.caption("请先在上方粘贴文章内容，或上传 TXT/MD 文件。")
                elif not st.session_state.cfg_valid or gen_llm is None:
                    st.caption("当前未检测到可用的生成模型，请先在【全局设置】中完成模型/API 配置。")

        if run_opt:
            st.session_state.opt_platform = target_platform
            opt_selected_technique_names = st.session_state.get("opt_techniques", [])

            optimize_prompt_template = """
你是GEO优化专家，目标是提升文章在大模型中的引用率和品牌自然提及。

【原文章】
{original_article}

【品牌】{brand}
【优势】{advantages}
【目标平台】{platform}

【优化要求（严格GEO原则）】
1) 保留原意和核心信息，不改变事实
2) 增强结构化：标题、清单、FAQ、代码块（适用时）
3) 自然植入品牌2-4次（先通用标准，再品牌适用）
4) 提升权威感：评估维度、匿名案例、来源占位建议（不得编造）
5) 结论先行、信息密度高
6) 长度控制在原长度的1.0-1.3倍
7) 输出两部分：【优化后文章】 + 【变更说明】（列出主要改动点）

【输出格式要求】
请严格按照以下结构输出一次，不要在前后添加其他说明或重复输出：
【优化后文章】
（在此输出完整优化后的文章）
【变更说明】
（在此列出主要变更点，使用条目形式）

【E-E-A-T 强化要求】
- 专业性：增强专业术语使用，展示专业知识深度
- 经验性：添加实际使用经验表述（如"实际应用中"、"使用中发现"），至少1处经验性表述
- 权威性：添加来源占位（数据来源、案例来源、标准来源），至少2处来源占位
- 可信度：明确标注不确定信息，避免编造数据，使用占位建议

【开始优化】
"""

            # 根据选择的优化技巧增强 Prompt
            if opt_selected_technique_names:
                opt_technique_manager = OptimizationTechniqueManager()
                opt_technique_ids = opt_technique_manager.get_technique_ids_by_names(
                    [
                        name.split(" ", 1)[1] if " " in name else name
                        for name in opt_selected_technique_names
                    ]
                )
                optimize_prompt_template = opt_technique_manager.enhance_prompt(
                    optimize_prompt_template, opt_technique_ids
                )

            # 对超长文章给出提醒，避免模型上下文溢出
            if len(original_article) > 8000:
                st.warning(
                    "当前文章长度较长（超过 8000 字符），可能导致大模型上下文溢出或响应失败。"
                    " 建议适当拆分文章后分别优化。"
                )

            optimize_prompt = PromptTemplate.from_template(optimize_prompt_template)

            try:
                with st.spinner("优化中..."):
                    chain = optimize_prompt | gen_llm | StrOutputParser()

                    # 准备输入文本用于成本估算
                    input_text = optimize_prompt.template.format(
                        original_article=original_article[
                            :500
                        ],  # 只取前500字符用于估算
                        brand=brand,
                        advantages=advantages,
                        platform=target_platform,
                    )
                    result = chain.invoke(
                        {
                            "original_article": original_article,
                            "brand": brand,
                            "advantages": advantages,
                            "platform": target_platform,
                        }
                    )

                    # 记录成本
                    if gen_llm:
                        try:
                            model_name = (
                                getattr(gen_llm, "model_name", None)
                                or getattr(gen_llm, "model", None)
                                or model_defaults(cfg["gen_provider"])
                            )
                            provider = cfg["gen_provider"]
                            record_api_cost(
                                operation_type="优化",
                                provider=provider,
                                model=model_name,
                                input_text=original_article[
                                    :1000
                                ],  # 使用实际输入文本的前1000字符
                                output_text=result,
                                platform=target_platform,
                                brand=brand,
                            )
                        except Exception:
                            # 记录成本失败不影响主流程
                            pass

                if "【优化后文章】" in result and "【变更说明】" in result:
                    optimized_article = (
                        result.split("【优化后文章】", 1)[1]
                        .split("【变更说明】", 1)[0]
                        .strip()
                    )
                    changes = result.split("【变更说明】", 1)[1].strip()
                else:
                    optimized_article = result.strip()
                    changes = "无详细变更说明（模型未按模板输出）。"

                st.session_state.optimized_article = optimized_article
                st.session_state.opt_changes = changes
                # 保存到数据库
                try:
                    storage.save_optimization(
                        original_article,
                        optimized_article,
                        changes,
                        target_platform,
                        brand,
                    )
                except Exception as e:
                    st.warning(f"优化完成，但保存到数据库时出错：{e}")
            except Exception as e:
                st.error(f"文章优化失败：{e}")

    # === 优化结果 & 质量评估 ===
    if st.session_state.optimized_article:
        st.markdown("---")
        st.markdown("#### 📝 优化结果")

        # 结果 Tabs：优化后文章 / 变更说明
        result_tab1, result_tab2 = st.tabs(["📝 优化后文章", "🧾 变更说明"])
        with result_tab1:
            markdown_platforms = ["GitHub", "微信公众号", "百家号", "网易号", "企鹅号", "简书"]
            if any(p in st.session_state.opt_platform for p in markdown_platforms):
                st.code(st.session_state.optimized_article, language="markdown")
            else:
                st.markdown(st.session_state.optimized_article)

            # 确定文件扩展名
            ext = (
                "md"
                if any(p in st.session_state.opt_platform for p in markdown_platforms)
                else "txt"
            )
            st.download_button(
                "下载优化版",
                st.session_state.optimized_article,
                f"{sanitize_filename(brand,40)}_优化文章.{ext}",
                use_container_width=True,
                key="opt_dl",
            )

        with result_tab2:
            st.markdown("#### 变更说明")
            st.markdown(st.session_state.opt_changes)

        # 提供简单的版本回退能力
        if (
            st.session_state.get("optimized_article_backup")
            and st.session_state.optimized_article_backup
            != st.session_state.optimized_article
        ):
            if st.button("恢复至强化前版本", key="opt_restore_backup"):
                st.session_state.optimized_article = (
                    st.session_state.optimized_article_backup
                )
                st.toast("已恢复至强化前版本。")

        st.markdown(
            "可选步骤：对优化后的文章进行质量评估与再强化（会调用额外模型）。"
        )

        # E-E-A-T 评估和强化区域
        st.markdown("#### 🎯 E-E-A-T 强化 + 来源占位")
        st.caption("评估和强化内容的专业性、经验性、权威性、可信度")

        eeat_col1, eeat_col2 = st.columns(2)

        with eeat_col1:
            assess_eeat_btn = st.button(
                "📊 评估 E-E-A-T",
                use_container_width=True,
                disabled=(not st.session_state.cfg_valid) or (gen_llm is None),
            )

        with eeat_col2:
            enhance_eeat_btn = st.button(
                "✨ 强化 E-E-A-T",
                use_container_width=True,
                disabled=(not st.session_state.cfg_valid) or (gen_llm is None),
            )
            st.caption("强化会覆盖当前优化结果，建议先下载备份。")

        # 初始化 E-E-A-T 相关状态
        ss_init("eeat_assessment", None)
        ss_init("eeat_enhanced_content", "")
        ss_init("eeat_source_placeholders", [])
        ss_init("optimized_article_backup", "")

        # E-E-A-T 评估
        if assess_eeat_btn and gen_llm:
            eeat_enhancer = EEATEnhancer()
            with st.spinner("正在评估 E-E-A-T..."):
                try:
                    score_chain = (
                        PromptTemplate.from_template("{input}")
                        | gen_llm
                        | StrOutputParser()
                    )
                    assessment = eeat_enhancer.assess_eeat(
                        st.session_state.optimized_article,
                        brand,
                        advantages,
                        st.session_state.opt_platform,
                        score_chain,
                    )
                    st.session_state.eeat_assessment = assessment
                except Exception as e:
                    st.error(f"E-E-A-T 评估失败：{e}")

        # E-E-A-T 强化（带备份与安全校验）
        if enhance_eeat_btn and gen_llm:
            eeat_enhancer = EEATEnhancer()
            st.session_state.optimized_article_backup = (
                st.session_state.optimized_article
            )
            with st.spinner("正在强化 E-E-A-T..."):
                try:
                    enhance_chain = (
                        PromptTemplate.from_template("{input}")
                        | gen_llm
                        | StrOutputParser()
                    )
                    enhanced = eeat_enhancer.enhance_eeat(
                        st.session_state.optimized_article,
                        brand,
                        advantages,
                        st.session_state.opt_platform,
                        enhance_chain,
                    )
                    new_content = enhanced.get("enhanced_content", "") or ""
                    if not new_content.strip() or len(new_content.strip()) < 100:
                        st.error(
                            "E-E-A-T 强化失败：模型返回内容异常，已保留强化前版本。"
                        )
                    else:
                        st.session_state.eeat_enhanced_content = new_content
                        st.session_state.eeat_source_placeholders = enhanced.get(
                            "source_placeholders", []
                        )
                        st.session_state.optimized_article = new_content
                        st.success(
                            f"✅ E-E-A-T 强化完成！已添加 {len(st.session_state.eeat_source_placeholders)} 个来源占位"
                        )
                except Exception as e:
                    st.error(f"E-E-A-T 强化失败：{e}")

        # 显示 E-E-A-T 评估结果
        if st.session_state.eeat_assessment:
            assessment = st.session_state.eeat_assessment
            scores = assessment.get("eeat_scores", {})
            total_score = scores.get("total", 0)
            eeat_enhancer = EEATEnhancer()
            level, color = eeat_enhancer.get_eeat_level(total_score)

            st.markdown("##### 📊 E-E-A-T 评估结果")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("总分", f"{total_score}/100", delta=level, delta_color="off")
            with col2:
                st.metric("专业性", f"{scores.get('expertise', 0)}/25")
            with col3:
                st.metric("经验性", f"{scores.get('experience', 0)}/25")
            with col4:
                st.metric("权威性", f"{scores.get('authoritativeness', 0)}/25")
            with col5:
                st.metric("可信度", f"{scores.get('trustworthiness', 0)}/25")

            # 详细评估和改进建议
            with st.container(border=True):
                st.markdown("##### 📝 详细评估与改进建议")
                details = assessment.get("details", {})
                improvements = assessment.get("improvements", [])
                source_suggestions = assessment.get("source_suggestions", [])

                st.markdown("**详细评估：**")
                st.markdown(f"- **专业性**：{details.get('expertise', '无')}")
                st.markdown(f"- **经验性**：{details.get('experience', '无')}")
                st.markdown(f"- **权威性**：{details.get('authoritativeness', '无')}")
                st.markdown(f"- **可信度**：{details.get('trustworthiness', '无')}")

                if improvements:
                    st.markdown("**💡 改进建议：**")
                    for improvement in improvements:
                        st.markdown(f"- {improvement}")

                if source_suggestions:
                    st.markdown("**📚 来源占位建议：**")
                    for suggestion in source_suggestions:
                        st.markdown(f"- {suggestion}")

                # 来源占位检查
                placeholders = assessment.get("source_placeholders", {})
                if placeholders:
                    st.markdown("**✅ 已检测到的来源占位：**")
                    if placeholders.get("data_sources"):
                        st.markdown(
                            f"- 数据来源：{len(placeholders['data_sources'])} 处"
                        )
                    if placeholders.get("case_sources"):
                        st.markdown(
                            f"- 案例来源：{len(placeholders['case_sources'])} 处"
                        )
                    if placeholders.get("standard_sources"):
                        st.markdown(
                            f"- 标准来源：{len(placeholders['standard_sources'])} 处"
                        )
                    if placeholders.get("expert_opinions"):
                        st.markdown(
                            f"- 专家观点：{len(placeholders['expert_opinions'])} 处"
                        )

        # 显示 E-E-A-T 强化后的来源占位清单
        if st.session_state.eeat_source_placeholders:
            with st.container(border=True):
                st.markdown("##### 📚 来源占位清单")
                for placeholder in st.session_state.eeat_source_placeholders:
                    st.markdown(f"- {placeholder}")

        # 事实密度 + 结构化块评估和强化
        st.markdown("---")
        st.markdown("#### 📊 事实密度 + 结构化块")
        st.caption("评估和强化内容的事实信息密度和结构化程度")

        fact_col1, fact_col2 = st.columns(2)

        with fact_col1:
            assess_opt_fact = st.button(
                "📊 评估事实密度",
                use_container_width=True,
                disabled=(not st.session_state.cfg_valid) or (gen_llm is None),
            )

        with fact_col2:
            enhance_opt_fact = st.button(
                "✨ 强化事实密度",
                use_container_width=True,
                disabled=(not st.session_state.cfg_valid) or (gen_llm is None),
            )
            st.caption("强化会覆盖当前优化结果，建议先下载备份。")

        # 初始化事实密度状态
        ss_init("opt_fact_assessment", None)
        ss_init("opt_fact_enhanced", "")
        ss_init("opt_fact_details", [])

        # 事实密度评估
        if assess_opt_fact and gen_llm:
            fact_enhancer = FactDensityEnhancer()
            with st.spinner("正在评估事实密度和结构化块..."):
                try:
                    score_chain = (
                        PromptTemplate.from_template("{input}")
                        | gen_llm
                        | StrOutputParser()
                    )
                    assessment = fact_enhancer.assess_fact_density(
                        st.session_state.optimized_article,
                        brand,
                        advantages,
                        st.session_state.opt_platform,
                        score_chain,
                    )
                    st.session_state.opt_fact_assessment = assessment
                except Exception as e:
                    st.error(f"事实密度评估失败：{e}")

        # 事实密度强化（带备份与安全校验）
        if enhance_opt_fact and gen_llm:
            fact_enhancer = FactDensityEnhancer()
            st.session_state.optimized_article_backup = (
                st.session_state.optimized_article
            )
            with st.spinner("正在强化事实密度和结构化块..."):
                try:
                    enhance_chain = (
                        PromptTemplate.from_template("{input}")
                        | gen_llm
                        | StrOutputParser()
                    )
                    enhanced = fact_enhancer.enhance_fact_density(
                        st.session_state.optimized_article,
                        brand,
                        advantages,
                        st.session_state.opt_platform,
                        enhance_chain,
                    )
                    new_content = enhanced.get("enhanced_content", "") or ""
                    if not new_content.strip() or len(new_content.strip()) < 100:
                        st.error(
                            "事实密度强化失败：模型返回内容异常，已保留强化前版本。"
                        )
                    else:
                        st.session_state.opt_fact_enhanced = new_content
                        st.session_state.opt_fact_details = enhanced.get(
                            "enhancement_details", []
                        )
                        st.session_state.optimized_article = new_content
                        st.success(
                            f"✅ 事实密度强化完成！已添加 {len(st.session_state.opt_fact_details)} 处事实信息和结构化块"
                        )
                except Exception as e:
                    st.error(f"事实密度强化失败：{e}")

        # 显示事实密度评估结果
        if st.session_state.opt_fact_assessment:
            assessment = st.session_state.opt_fact_assessment
            scores = assessment.get("scores", {})
            total_score = scores.get("total", 0)
            fact_enhancer = FactDensityEnhancer()
            level, color = fact_enhancer.get_score_level(total_score)

            st.markdown("##### 📊 事实密度 + 结构化评估结果")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总分", f"{total_score}/100", delta=level, delta_color="off")
            with col2:
                st.metric("事实密度", f"{scores.get('fact_density', 0)}/50")
            with col3:
                st.metric("结构化", f"{scores.get('structure', 0)}/50")

            # 使用 tabs 组织分析结果
            fact_analysis = assessment.get("fact_analysis", {})
            structure_analysis = assessment.get("structure_analysis", {})
            has_details = bool(st.session_state.get("opt_fact_details"))

            # 构建可用的 tabs
            tab_labels = []
            if fact_analysis:
                tab_labels.append("📈 事实密度")
            if structure_analysis:
                tab_labels.append("🏗️ 结构化块")
            if has_details:
                tab_labels.append("📝 强化详情")

            if tab_labels:
                analysis_tabs = st.tabs(tab_labels)
                tab_idx = 0

                # 事实密度分析
                if fact_analysis:
                    with analysis_tabs[tab_idx]:
                        with st.container(border=True):
                            col1, col2, col3, col4, col5, col6 = st.columns(6)
                            with col1:
                                st.metric("数据", fact_analysis.get("data_count", 0))
                            with col2:
                                st.metric("案例", fact_analysis.get("case_count", 0))
                            with col3:
                                st.metric("标准", fact_analysis.get("standard_count", 0))
                            with col4:
                                st.metric(
                                    "对比", fact_analysis.get("comparison_count", 0)
                                )
                            with col5:
                                st.metric("时间", fact_analysis.get("time_count", 0))
                            with col6:
                                st.metric("来源", fact_analysis.get("source_count", 0))

                            missing_facts = fact_analysis.get("missing_facts", [])
                            if missing_facts:
                                st.markdown("**缺失的事实类型：**")
                                for fact in missing_facts:
                                    st.markdown(f"- {fact}")
                    tab_idx += 1

                # 结构化分析
                if structure_analysis:
                    with analysis_tabs[tab_idx]:
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.markdown(
                                    f"**标题层级**：{'✅' if structure_analysis.get('has_title') else '❌'}"
                                )
                                st.markdown(
                                    f"**结论摘要**：{'✅' if structure_analysis.get('has_summary') else '❌'}"
                                )
                            with col2:
                                st.markdown(
                                    f"**清单列表**：{'✅' if structure_analysis.get('has_list') else '❌'}"
                                )
                                st.markdown(
                                    f"**FAQ部分**：{'✅' if structure_analysis.get('has_faq') else '❌'}"
                                )
                            with col3:
                                st.markdown(
                                    f"**代码块**：{'✅' if structure_analysis.get('has_code') else '❌'}"
                                )
                                st.markdown(
                                    f"**对比表格**：{'✅' if structure_analysis.get('has_table') else '❌'}"
                                )
                            with col4:
                                st.markdown(
                                    f"**步骤说明**：{'✅' if structure_analysis.get('has_steps') else '❌'}"
                                )
                                st.markdown(
                                    f"**总结部分**：{'✅' if structure_analysis.get('has_conclusion') else '❌'}"
                                )

                            missing_blocks = structure_analysis.get("missing_blocks", [])
                            if missing_blocks:
                                st.markdown("**缺失的结构化块：**")
                                for block in missing_blocks:
                                    st.markdown(f"- {block}")
                    tab_idx += 1

                # 强化详情
                if has_details:
                    with analysis_tabs[tab_idx]:
                        with st.container(border=True):
                            for detail in st.session_state.opt_fact_details:
                                st.markdown(f"- {detail}")

    # === 高级：结构化 Schema & 技术配置（折叠区） ===
    with st.expander(
        "高级：结构化 Schema & 技术 SEO 配置（可选）", expanded=False
    ):
        # 结构化数据生成
        st.markdown("**📋 结构化数据生成**")
        st.caption(
            "生成符合 Schema.org 规范的 JSON-LD 代码，提升品牌在 AI 模型中的实体识别和权威性"
        )

        with st.container(border=True):
            schema_col1, schema_col2 = st.columns([2, 1])

            with schema_col1:
                schema_type = st.selectbox(
                    "Schema 类型",
                    [
                        "Organization（组织/公司）",
                        "SoftwareApplication（软件应用）",
                        "Product（产品）",
                        "Service（服务）",
                        "组合（Organization + SoftwareApplication）",
                    ],
                    index=1,
                    key="schema_type_sel",
                    help="选择适合您品牌的 Schema 类型",
                )

            with schema_col2:
                generate_schema_btn = st.button(
                    "🚀 生成 JSON-LD",
                    use_container_width=True,
                    key="generate_schema_btn",
                )

            # 初始化 JSON-LD 相关状态
            ss_init("generated_json_ld", None)
            ss_init("generated_html_script", None)

            # 生成 JSON-LD（带基础信息校验）
            if generate_schema_btn:
                if not brand or not advantages or len(brand.strip()) < 2:
                    st.warning(
                        "请先在基础信息中填写品牌名称和优势，再生成 Schema。"
                    )
                else:
                    try:
                        schema_gen = SchemaGenerator()

                        if schema_type == "Organization（组织/公司）":
                            schema_dict = schema_gen.generate_organization_schema(
                                brand_name=brand,
                                description=advantages,
                                url="",  # 用户可以在生成后手动添加
                                logo="",
                                founding_date="",
                            )
                        elif schema_type == "SoftwareApplication（软件应用）":
                            schema_dict = schema_gen.generate_software_application_schema(
                                brand_name=brand,
                                application_name=brand,
                                description=advantages,
                                url="",
                                application_category="BusinessApplication",
                                operating_system="Web",
                            )
                        elif schema_type == "Product（产品）":
                            schema_dict = schema_gen.generate_product_schema(
                                brand_name=brand,
                                product_name=brand,
                                description=advantages,
                                url="",
                            )
                        elif schema_type == "Service（服务）":
                            schema_dict = schema_gen.generate_service_schema(
                                brand_name=brand,
                                service_name=brand,
                                description=advantages,
                                url="",
                            )
                        else:  # 组合
                            schema_dict = schema_gen.generate_combined_schema(
                                brand_name=brand,
                                advantages=advantages,
                                schema_types=[
                                    "Organization",
                                    "SoftwareApplication",
                                ],
                            )

                        # 格式化输出
                        json_ld_code = schema_gen.format_json_ld(schema_dict)
                        html_script = schema_gen.generate_html_script_tag(
                            schema_dict
                        )

                        st.session_state.generated_json_ld = json_ld_code
                        st.session_state.generated_html_script = html_script

                        st.success("✅ JSON-LD Schema 生成成功！")
                    except Exception as e:
                        st.error(f"JSON-LD 生成失败：{e}")

            # 显示生成的 JSON-LD
            if st.session_state.generated_json_ld:
                st.markdown("##### 📄 JSON-LD 代码")
                st.code(st.session_state.generated_json_ld, language="json")

                st.markdown("##### 📄 HTML Script 标签（可直接嵌入网页）")
                st.code(st.session_state.generated_html_script, language="html")

                # 下载按钮
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "下载 JSON-LD",
                        st.session_state.generated_json_ld,
                        f"{sanitize_filename(brand,40)}_schema.json",
                        mime="application/json",
                        use_container_width=True,
                        key="schema_dl_json",
                    )
                with col2:
                    st.download_button(
                        "下载 HTML Script",
                        st.session_state.generated_html_script,
                        f"{sanitize_filename(brand,40)}_schema.html",
                        mime="text/html",
                        use_container_width=True,
                        key="schema_dl_html",
                    )

                st.info(
                    "💡 **使用说明**：将 HTML Script 标签复制到您的官网 `<head>` 部分，或将 JSON-LD 代码添加到 GitHub README 中。"
                )

        # 技术配置生成
        st.markdown("---")
        st.markdown("**⚙️ 技术配置生成**")
        st.caption("生成 robots.txt、sitemap.xml 等技术配置文件，提升内容收录效果（提升 20-30%）")

        with st.container(border=True):
            config_tab1, config_tab2 = st.tabs(["🤖 robots.txt", "🗺️ sitemap.xml"])

            # robots.txt 生成
            with config_tab1:
                st.markdown("##### 🤖 robots.txt 生成")
                st.caption("控制搜索引擎爬虫的访问权限，提升内容收录效果")

                robots_col1, robots_col2 = st.columns([2, 1])

                with robots_col1:
                    robots_base_url = st.text_input(
                        "网站基础 URL",
                        value="",
                        key="robots_base_url",
                        placeholder="https://example.com",
                        help="您的网站基础 URL（如 https://example.com）",
                    )

                with robots_col2:
                    generate_robots_btn = st.button(
                        "🚀 生成 robots.txt",
                        use_container_width=True,
                        key="generate_robots_btn",
                    )

                # 允许/禁止路径配置
                robots_config_col1, robots_config_col2 = st.columns(2)

                with robots_config_col1:
                    allow_paths_input = st.text_area(
                        "允许爬取的路径（每行一个）",
                        value="/\n/blog\n/docs",
                        key="robots_allow_paths",
                        help="每行一个路径，如 /、/blog、/docs",
                        height=100,
                    )

                with robots_config_col2:
                    disallow_paths_input = st.text_area(
                        "禁止爬取的路径（每行一个）",
                        value="/admin\n/private\n/api",
                        key="robots_disallow_paths",
                        help="每行一个路径，如 /admin、/private、/api",
                        height=100,
                    )

                # 初始化状态
                ss_init("generated_robots_txt", None)

                # 生成 robots.txt（带 URL 校验）
                if generate_robots_btn:
                    if not robots_base_url.strip():
                        st.error("请填写网站基础 URL（如 https://example.com）。")
                    else:
                        if not robots_base_url.startswith("http"):
                            st.warning(
                                "建议使用完整 URL（含 http/https），避免 robots.txt 中出现无效链接。"
                            )
                        try:
                            config_gen = TechnicalConfigGenerator()

                            # 解析允许路径
                            allow_paths = (
                                [
                                    p.strip()
                                    for p in allow_paths_input.split("\n")
                                    if p.strip()
                                ]
                                if allow_paths_input
                                else None
                            )

                            # 解析禁止路径
                            disallow_paths = (
                                [
                                    p.strip()
                                    for p in disallow_paths_input.split("\n")
                                    if p.strip()
                                ]
                                if disallow_paths_input
                                else None
                            )

                            robots_txt = config_gen.generate_robots_txt(
                                base_url=robots_base_url,
                                allow_paths=allow_paths,
                                disallow_paths=disallow_paths,
                                sitemap_url="",  # 自动生成
                                user_agent="*",
                                crawl_delay=None,
                            )

                            st.session_state.generated_robots_txt = robots_txt
                            st.success("✅ robots.txt 生成成功！")
                        except Exception as e:
                            st.error(f"robots.txt 生成失败：{e}")

                # 显示生成的 robots.txt
                if st.session_state.generated_robots_txt:
                    st.markdown("##### 📄 robots.txt 内容")
                    st.code(st.session_state.generated_robots_txt, language="text")

                    st.download_button(
                        "下载 robots.txt",
                        st.session_state.generated_robots_txt,
                        "robots.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="robots_dl",
                    )

                    st.info(
                        "💡 **使用说明**：将 robots.txt 文件上传到您网站的根目录（如 https://example.com/robots.txt）"
                    )

            # sitemap.xml 生成
            with config_tab2:
                st.markdown("##### 🗺️ sitemap.xml 生成")
                st.caption("帮助搜索引擎发现和索引您的所有页面，提升内容收录效果")

                sitemap_col1, sitemap_col2 = st.columns([2, 1])

                with sitemap_col1:
                    sitemap_base_url = st.text_input(
                        "网站基础 URL",
                        value="",
                        key="sitemap_base_url",
                        placeholder="https://example.com",
                        help="您的网站基础 URL（如 https://example.com）",
                    )

                with sitemap_col2:
                    generate_sitemap_btn = st.button(
                        "🚀 生成 sitemap.xml",
                        use_container_width=True,
                        key="generate_sitemap_btn",
                    )

                # 选择数据源
                sitemap_source = st.radio(
                    "数据源",
                    ["基于关键词生成", "基于历史文章生成"],
                    key="sitemap_source",
                    horizontal=True,
                )

                # 初始化状态
                ss_init("generated_sitemap_xml", None)

                # 生成 sitemap.xml（带 URL 校验）
                if generate_sitemap_btn:
                    if not sitemap_base_url.strip():
                        st.error("请填写网站基础 URL（如 https://example.com）。")
                    else:
                        if not sitemap_base_url.startswith("http"):
                            st.warning(
                                "建议使用完整 URL（含 http/https），避免 sitemap.xml 中出现无效链接。"
                            )
                        try:
                            config_gen = TechnicalConfigGenerator()

                            if sitemap_source == "基于关键词生成":
                                # 基于关键词生成
                                keywords_for_sitemap = (
                                    st.session_state.keywords
                                    if st.session_state.keywords
                                    else []
                                )

                                if not keywords_for_sitemap:
                                    st.warning(
                                        "⚠️ 请先在【1 关键词蒸馏】生成关键词，或选择【基于历史文章生成】"
                                    )
                                else:
                                    sitemap_xml = (
                                        config_gen.generate_sitemap_xml(
                                            base_url=sitemap_base_url,
                                            keywords=keywords_for_sitemap,
                                            lastmod=None,  # 使用当前日期
                                            changefreq="weekly",
                                            priority=0.8,
                                        )
                                    )
                                    st.session_state.generated_sitemap_xml = (
                                        sitemap_xml
                                    )
                                    st.success(
                                        f"✅ sitemap.xml 生成成功！包含 {len(keywords_for_sitemap)} 个 URL"
                                    )
                            else:
                                # 基于历史文章生成
                                try:
                                    articles = storage.get_articles(brand=brand)

                                    if not articles:
                                        st.warning(
                                            "⚠️ 暂无历史文章，请先生成内容，或选择【基于关键词生成】"
                                        )
                                    else:
                                        sitemap_xml = (
                                            config_gen.generate_sitemap_from_articles(
                                                base_url=sitemap_base_url,
                                                articles=articles,
                                                lastmod=None,
                                                changefreq="weekly",
                                                priority=0.8,
                                            )
                                        )
                                        st.session_state.generated_sitemap_xml = (
                                            sitemap_xml
                                        )
                                        st.success(
                                            f"✅ sitemap.xml 生成成功！包含 {len(articles)} 个 URL"
                                        )
                                except Exception as e:
                                    st.error(f"获取历史文章失败：{e}")

                        except Exception as e:
                            st.error(f"sitemap.xml 生成失败：{e}")

                # 显示生成的 sitemap.xml
                if st.session_state.generated_sitemap_xml:
                    st.markdown("##### 📄 sitemap.xml 内容")
                    st.code(st.session_state.generated_sitemap_xml, language="xml")

                    st.download_button(
                        "下载 sitemap.xml",
                        st.session_state.generated_sitemap_xml,
                        "sitemap.xml",
                        mime="application/xml",
                        use_container_width=True,
                        key="sitemap_dl",
                    )

                    st.info(
                        "💡 **使用说明**：将 sitemap.xml 文件上传到您网站的根目录（如 https://example.com/sitemap.xml），并在 Google Search Console 中提交"
                    )

