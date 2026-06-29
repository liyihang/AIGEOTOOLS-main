import json
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate

from modules.keyword_mining import KeywordMining
from modules.semantic_expander import SemanticExpander
from modules.topic_cluster import TopicCluster
from modules.ui.components import sanitize_filename, extract_json_array


def render_tab_keywords(storage, ss_init, gen_llm, brand: str, advantages: str) -> None:
    """
    渲染 Tab1：关键词蒸馏。

    该实现直接从 `geo_tool.py` 中迁移而来，仅进行了最小必要的结构调整：
    - 包装为函数，便于从主入口调用
    - 通过参数接收 `storage` / `ss_init` / `gen_llm` / `brand` / `advantages`
    """
    # ========== 区域 1：模式选择 ==========
    st.markdown("**🎯 生成模式**")
    generation_mode = st.radio(
        "选择生成模式",
        ["AI生成", "托词工具", "混合模式"],
        index=["AI生成", "托词工具", "混合模式"].index(
            st.session_state.kw_generation_mode
        ),
        horizontal=True,
        key="kw_mode_radio",
        help="AI生成：使用 LLM 直接生成；托词工具：基于词库组合；混合模式：先组合再润色",
    )
    st.session_state.kw_generation_mode = generation_mode
    st.markdown("---")

    # ========== 区域 2：配置区（条件显示） ==========
    if generation_mode in ["托词工具", "混合模式"]:
        # 初始化词库
        if st.session_state.wordbanks is None:
            st.session_state.wordbanks = st.session_state.keyword_tool.load_wordbanks()

        # 初始化组合模式选择
        ss_init("selected_patterns", list(st.session_state.keyword_tool.combination_patterns))

        wordbanks = st.session_state.wordbanks

        # 组合模式选择
        with st.container(border=True):
            st.markdown("**📐 组合模式选择**")
            pattern_descriptions = st.session_state.keyword_tool.get_pattern_descriptions()
            all_patterns = st.session_state.keyword_tool.combination_patterns

            # 显示所有可用模式
            pattern_options = []
            for pattern in all_patterns:
                pattern_str = "+".join(pattern)
                desc = pattern_descriptions.get(pattern_str, pattern_str)
                pattern_options.append((pattern_str, pattern, desc))

            # 多选组合模式
            selected_pattern_strs = st.multiselect(
                "选择要使用的组合模式（可多选）",
                options=[opt[0] for opt in pattern_options],
                default=[
                    opt[0]
                    for opt in pattern_options
                    if opt[1] in st.session_state.selected_patterns
                ],
                key="kw_pattern_select",
                help="选择要使用的组合模式，至少选择一个",
            )

            # 更新选中的模式
            selected_patterns = []
            for pattern_str, pattern, desc in pattern_options:
                if pattern_str in selected_pattern_strs:
                    selected_patterns.append(pattern)
            st.session_state.selected_patterns = (
                selected_patterns if selected_patterns else all_patterns
            )

            # 显示模式说明
            with st.expander("📖 组合模式说明", expanded=False):
                for pattern_str, pattern, desc in pattern_options:
                    st.markdown(f"**{pattern_str}**: {' + '.join(desc)}")

        # 词库管理
        with st.container(border=True):
            st.markdown("**📚 词库管理**")
            wordbank_tab1, wordbank_tab2 = st.tabs(["编辑词库", "导入/导出"])

            with wordbank_tab1:
                st.markdown("**词库编辑**")
                bank_types = list(wordbanks.keys())

                # 横向展示所有词库类型（6列）
                st.caption(
                    "💡 提示：所有词库类型横向展示，可直接编辑，点击各列的「更新」按钮或使用下方的「更新所有词库」按钮保存修改"
                )
                cols = st.columns(6)
                edited_wordbanks = {}

                for idx, bank_type in enumerate(bank_types):
                    with cols[idx]:
                        # 显示词库类型名称
                        st.markdown(f"**{bank_type}**")

                        # 显示当前词库内容
                        current_words = wordbanks.get(bank_type, [])
                        edited_words = st.text_area(
                            f"{bank_type} 词汇（每行一个）",
                            "\n".join(current_words),
                            height=200,
                            key=f"kw_bank_edit_{bank_type}",
                            label_visibility="collapsed",
                        )

                        # 保存编辑内容
                        edited_wordbanks[bank_type] = edited_words

                        # 每个词库单独的更新按钮
                        if st.button(
                            "更新",
                            key=f"kw_update_{bank_type}",
                            use_container_width=True,
                        ):
                            new_words = [
                                w.strip() for w in edited_words.split("\n") if w.strip()
                            ]
                            wordbanks[bank_type] = new_words
                            st.session_state.wordbanks = wordbanks
                            st.success(f"✅ {bank_type} 已更新（{len(new_words)} 个词汇）")
                            st.info(
                                "💡 提示：词库已更新，建议重新生成关键词以应用新词库"
                            )
                            st.rerun()

                # 统一更新所有词库按钮
                if st.button(
                    "💾 更新所有词库",
                    use_container_width=True,
                    type="primary",
                    key="kw_update_all",
                ):
                    updated_count = 0
                    for bank_type, edited_text in edited_wordbanks.items():
                        new_words = [
                            w.strip() for w in edited_text.split("\n") if w.strip()
                        ]
                        if new_words != wordbanks.get(bank_type, []):
                            wordbanks[bank_type] = new_words
                            updated_count += 1

                    if updated_count > 0:
                        st.session_state.wordbanks = wordbanks
                        st.success(f"✅ 已更新 {updated_count} 个词库")
                        st.info(
                            "💡 提示：词库已更新，建议重新生成关键词以应用新词库"
                        )
                        st.rerun()
                    else:
                        st.info("没有词库需要更新")

            with wordbank_tab2:
                st.markdown("**词库导入/导出**")
                # 导出
                wordbanks_json = json.dumps(wordbanks, ensure_ascii=False, indent=2)
                st.download_button(
                    "导出词库（JSON）",
                    wordbanks_json,
                    "wordbanks.json",
                    "application/json",
                    use_container_width=True,
                    key="kw_export_json",
                )

                # 导入
                uploaded_wordbanks = st.file_uploader(
                    "导入词库（JSON）",
                    type=["json"],
                    key="kw_import_json",
                )
                if uploaded_wordbanks:
                    try:
                        imported = json.loads(
                            uploaded_wordbanks.read().decode("utf-8")
                        )
                        if isinstance(imported, dict):
                            st.session_state.wordbanks = imported
                            st.success("词库导入成功！")
                            st.rerun()
                    except Exception as e:
                        st.error(f"导入失败：{e}")

                # 重置为默认词库
                if st.button(
                    "重置为默认词库",
                    use_container_width=True,
                    key="kw_reset_banks",
                ):
                    st.session_state.wordbanks = (
                        st.session_state.keyword_tool.load_wordbanks()
                    )
                    st.success("已重置为默认词库")
                    st.rerun()

    # ========== 区域 3：生成控制 ==========
    with st.container(border=True):
        st.markdown("**⚙️ 生成控制**")
        ss_init("kw_last_num", 20)  # 确保默认值初始化

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.session_state.kw_last_num = st.slider(
                "生成数量",
                5,
                200,
                st.session_state.kw_last_num,
                key="kw_num",
                help="建议范围：10-50 个关键词",
            )
        with c2:
            # 根据模式调整禁用条件
            if generation_mode == "托词工具":
                run_kw_disabled = (
                    not st.session_state.get("selected_patterns")
                    or len(st.session_state.get("selected_patterns", [])) == 0
                )
            else:
                run_kw_disabled = (not st.session_state.cfg_valid) or (gen_llm is None)

            # 防止并发点击
            if st.session_state.get("kw_generating", False):
                run_kw_disabled = True

            run_kw = st.button(
                "🚀 生成关键词",
                type="primary",
                use_container_width=True,
                disabled=run_kw_disabled,
                key="kw_run",
            )
        with c3:
            if st.button(
                "🗑️ 清空结果", use_container_width=True, key="kw_clear"
            ):
                # 清空所有相关状态
                st.session_state.keywords = []
                st.session_state.expanded_keywords = []
                st.session_state.topic_clusters = []
                st.session_state.cluster_relationships = []
                st.session_state.cluster_stats = None
                st.session_state.content_planning = None
                st.session_state.mined_keywords = []
                st.session_state.competition_analysis = {}
                st.session_state.trend_analysis = {}
                st.session_state.value_matrix = {}
                st.session_state.keyword_recommendations = []
                st.toast("已清空所有关键词和相关数据")
                st.rerun()

        if run_kw:
            # ========== 参数验证 ==========
            if generation_mode == "AI生成":
                if not brand or not advantages:
                    st.error("❌ **请先在侧边栏配置品牌名称和核心优势**")
                    st.stop()

            # ========== 防止并发点击 ==========
            if st.session_state.get("kw_generating", False):
                st.warning("⏳ 正在生成中，请勿重复点击")
                st.stop()

            st.session_state.kw_generating = True
            keywords = []

            if generation_mode == "AI生成":
                # 原有 AI 生成逻辑
                keyword_prompt = PromptTemplate.from_template(
                    """
你是GEO（Generative Engine Optimization）专家，目标是提升品牌在大模型自然回答中的提及率。

【输入】
- 品牌：{brand}
- 核心优势：{advantages}
- 数量：{num_keywords}

【GEO核心要求】
1) 覆盖用户真实搜索意图：
   - 根据品牌和优势，识别用户可能的搜索场景（对比、评测、使用、购买、问题、教程等）
   - 关键词应反映用户真实需求，而非营销术语
   - 考虑不同用户角色和搜索阶段的需求
   
2) 品牌词占比策略：
   - 约30%包含品牌词（建立护城河，提升品牌提及率）
   - 约70%为泛词（扩大覆盖面，获取新流量）
   - 品牌词应自然融入，避免生硬拼接
   
3) 表达要求：
   - 口语化、自然、符合用户搜索习惯
   - 长度控制在 12-28 字
   - 避免过于正式或营销化
   
4) 多样性要求：
   - 去重：避免生成相同或过于相似的关键词
   - 均衡意图：覆盖不同搜索意图（对比、评测、使用、购买、问题等）
   - 多样化表达：使用不同的表达方式

【输出格式】
请严格按照以下 JSON 数组格式输出，不要添加任何其他内容：
["关键词1", "关键词2", "关键词3", ...]

如果无法生成 JSON 格式，请每行输出一个关键词（纯文本格式）。

【开始生成】
"""
                )

                chain_json = keyword_prompt | gen_llm | JsonOutputParser()
                chain_text = keyword_prompt | gen_llm | StrOutputParser()

                # 改进加载状态
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("🔄 正在生成关键词...")
                progress_bar.progress(10)

                status_text.text("🤖 调用 AI 模型生成关键词...")
                progress_bar.progress(30)

                try:
                    result = chain_json.invoke(
                        {
                            "brand": brand,
                            "advantages": advantages,
                            "num_keywords": st.session_state.kw_last_num,
                        }
                    )
                    keywords = result if isinstance(result, list) else []
                    progress_bar.progress(80)
                except Exception:
                    raw = chain_text.invoke(
                        {
                            "brand": brand,
                            "advantages": advantages,
                            "num_keywords": st.session_state.kw_last_num,
                        }
                    )
                    keywords = extract_json_array(raw) or []
                    progress_bar.progress(80)

                status_text.text("✨ 处理生成结果...")
                progress_bar.progress(100)

                progress_bar.empty()
                status_text.empty()

            elif generation_mode == "托词工具":
                # 托词工具生成
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("🔧 加载词库和组合模式...")
                progress_bar.progress(20)

                wordbanks = (
                    st.session_state.wordbanks
                    or st.session_state.keyword_tool.load_wordbanks()
                )
                selected_patterns = st.session_state.get(
                    "selected_patterns", st.session_state.keyword_tool.combination_patterns
                )

                # 检查词库是否为空（在生成前检查）
                empty_banks = [k for k, v in wordbanks.items() if not v]
                if empty_banks:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(
                        f"❌ 以下词库为空，请先添加词汇：{', '.join(empty_banks)}"
                    )
                    st.session_state.kw_generating = False
                    st.stop()

                status_text.text("🔄 生成关键词组合...")
                progress_bar.progress(60)

                keywords = st.session_state.keyword_tool.generate_combinations(
                    wordbanks=wordbanks,
                    patterns=selected_patterns,
                    max_results=st.session_state.kw_last_num,
                    similarity_threshold=0.8,
                )

                status_text.text("✨ 去重和筛选...")
                progress_bar.progress(100)

                progress_bar.empty()
                status_text.empty()

            elif generation_mode == "混合模式":
                # 混合模式：先托词生成，再 LLM 润色
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("🔧 加载词库和组合模式...")
                progress_bar.progress(10)

                wordbanks = (
                    st.session_state.wordbanks
                    or st.session_state.keyword_tool.load_wordbanks()
                )
                selected_patterns = st.session_state.get(
                    "selected_patterns", st.session_state.keyword_tool.combination_patterns
                )

                # 检查词库是否为空（在生成前检查）
                empty_banks = [k for k, v in wordbanks.items() if not v]
                if empty_banks:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(
                        f"❌ 以下词库为空，请先添加词汇：{', '.join(empty_banks)}"
                    )
                    st.session_state.kw_generating = False
                    st.stop()

                status_text.text("🔄 托词生成中...")
                progress_bar.progress(30)

                raw_keywords = st.session_state.keyword_tool.generate_combinations(
                    wordbanks=wordbanks,
                    patterns=selected_patterns,
                    max_results=st.session_state.kw_last_num * 2,  # 生成更多，因为会去重
                    similarity_threshold=0.8,
                )

                if raw_keywords and gen_llm:
                    status_text.text("🤖 LLM 润色中...")
                    progress_bar.progress(60)

                    # 使用 LLM 润色
                    polish_template = PromptTemplate.from_template("{input}")
                    polish_chain = polish_template | gen_llm | StrOutputParser()
                    keywords = st.session_state.keyword_tool.polish_with_llm(
                        keywords=raw_keywords,
                        llm_chain=polish_chain,
                        brand=brand,
                        max_polish=min(
                            len(raw_keywords), st.session_state.kw_last_num
                        ),
                    )
                    progress_bar.progress(90)
                else:
                    keywords = raw_keywords
                    progress_bar.progress(90)

                status_text.text("✨ 处理生成结果...")
                progress_bar.progress(100)

                progress_bar.empty()
                status_text.empty()

            # 清理和去重
            cleaned, seen = [], set()
            for k in keywords:
                if not isinstance(k, str):
                    continue
                kk = k.strip()
                if not kk:
                    continue
                kl = kk.lower()
                if kl in seen:
                    continue
                seen.add(kl)
                cleaned.append(kk)

            # 限制数量
            cleaned = cleaned[: st.session_state.kw_last_num]

            # 清理生成状态
            st.session_state.kw_generating = False

            if cleaned:
                # 清空扩展和集群相关状态（避免数据混乱）
                st.session_state.expanded_keywords = []
                st.session_state.topic_clusters = []
                st.session_state.cluster_relationships = []
                st.session_state.cluster_stats = None
                st.session_state.content_planning = None

                st.session_state.keywords = cleaned
                # 保存到数据库
                try:
                    storage.save_keywords(cleaned, brand)
                except Exception as e:
                    st.warning(f"关键词已生成，但保存到数据库时出错：{e}")
                st.success(f"✅ 生成完成！共生成 {len(cleaned)} 个关键词")
            else:
                # 分场景错误提示
                if generation_mode == "AI生成":
                    st.error(
                        """
❌ **AI 生成失败**

**可能原因：**
- API Key 配置错误或余额不足
- 网络连接问题
- 品牌名称或核心优势为空

**解决建议：**
1. 检查侧边栏的 API Key 配置
2. 确认品牌名称和核心优势已填写
3. 稍后重试或联系技术支持
"""
                    )
                elif generation_mode == "托词工具":
                    wordbanks = (
                        st.session_state.wordbanks
                        or st.session_state.keyword_tool.load_wordbanks()
                    )
                    empty_banks = [k for k, v in wordbanks.items() if not v]
                    if empty_banks:
                        st.error(
                            f"""
❌ **词库为空**

以下词库为空，请先添加词汇：
- {', '.join(empty_banks)}

**操作步骤：**
1. 点击"词库管理"
2. 选择空的词库类型
3. 添加至少 3-5 个词汇
4. 点击"更新词库"
5. 重新生成关键词
"""
                        )
                    elif not st.session_state.get("selected_patterns") or len(
                        st.session_state.get("selected_patterns", [])
                    ) == 0:
                        st.error(
                            """
❌ **未选择组合模式**

请至少选择一个组合模式：
1. 在"组合模式选择"区域
2. 勾选至少一个模式
3. 重新生成关键词
"""
                        )
                    else:
                        st.error(
                            """
❌ **生成失败**

请检查词库配置或选择更多组合模式后重试。
"""
                        )
                elif generation_mode == "混合模式":
                    wordbanks = (
                        st.session_state.wordbanks
                        or st.session_state.keyword_tool.load_wordbanks()
                    )
                    empty_banks = [k for k, v in wordbanks.items() if not v]
                    if empty_banks:
                        st.error(
                            f"""
❌ **词库为空**

以下词库为空，请先添加词汇：
- {', '.join(empty_banks)}

**操作步骤：**
1. 点击"词库管理"
2. 选择空的词库类型
3. 添加至少 3-5 个词汇
4. 点击"更新词库"
5. 重新生成关键词
"""
                        )
                    elif not st.session_state.get("selected_patterns") or len(
                        st.session_state.get("selected_patterns", [])
                    ) == 0:
                        st.error(
                            """
❌ **未选择组合模式**

请至少选择一个组合模式后重试。
"""
                        )
                    elif not gen_llm:
                        st.error(
                            """
❌ **LLM 配置缺失**

混合模式需要 LLM 进行润色，请检查侧边栏的 API Key 配置。
"""
                        )
                    else:
                        st.error(
                            """
❌ **生成失败**

请检查配置后重试。
"""
                        )

    if st.session_state.keywords:
        # 语义足迹扩展功能
        st.markdown("---")
        st.markdown("**🌐 语义足迹扩展**")
        st.caption(
            "基于现有关键词，通过语义相似度扩展出更多相关关键词，提升关键词覆盖面"
        )

        # 使用容器包装，使布局更清晰
        with st.container(border=True):
            # 第一行：扩展数量滑块（单独一行，更清晰）
            current_keyword_count = len(st.session_state.keywords)
            max_expansion = max(
                11, min(100, current_keyword_count * 3)
            )  # 最多扩展到当前数量的3倍，但确保至少为11（因为最小值是10）
            default_expansion = min(
                30, max(10, current_keyword_count)
            )  # 默认值不超过当前数量

            expansion_count = st.slider(
                "扩展数量",
                10,
                max_expansion,
                default_expansion,
                key="semantic_expansion_count",
                help=f"期望扩展的关键词数量（当前有 {current_keyword_count} 个关键词，建议扩展 10-{max_expansion} 个）",
            )

            # 第二行：按钮和合并策略并排
            expand_col1, expand_col2 = st.columns([2, 1])

            with expand_col1:
                expand_keywords_btn = st.button(
                    "🚀 开始语义扩展",
                    use_container_width=True,
                    disabled=(
                        (not st.session_state.cfg_valid)
                        or (gen_llm is None)
                        or (len(st.session_state.keywords) == 0)
                    ),
                    key="semantic_expand_btn",
                )

            with expand_col2:
                merge_strategy = st.selectbox(
                    "合并策略",
                    ["追加", "替换", "交替"],
                    index=0,
                    key="merge_strategy",
                    help="追加：在现有关键词后添加扩展词；替换：用扩展词替换现有关键词；交替：交替插入",
                )

        # 初始化语义扩展相关状态
        ss_init("expanded_keywords", [])
        ss_init("expansion_stats", None)
        ss_init("expansion_details", [])
        ss_init("original_keywords_before_expansion", [])  # 保存扩展前的原始关键词

        # 执行语义扩展
        if expand_keywords_btn and gen_llm and st.session_state.keywords:
            # 保存扩展前的原始关键词列表（用于撤销功能）
            if not st.session_state.original_keywords_before_expansion:
                st.session_state.original_keywords_before_expansion = (
                    st.session_state.keywords.copy()
                )

            semantic_expander = SemanticExpander()
            with st.spinner(f"正在扩展关键词（目标：{expansion_count} 个）..."):
                try:
                    expand_chain = (
                        PromptTemplate.from_template("{input}")
                        | gen_llm
                        | StrOutputParser()
                    )
                    expansion_result = semantic_expander.expand_keywords(
                        st.session_state.keywords,
                        brand,
                        advantages,
                        expansion_count,
                        expand_chain,
                    )

                    expanded_keywords = expansion_result.get("expanded_keywords", [])
                    st.session_state.expanded_keywords = expanded_keywords
                    st.session_state.expansion_stats = expansion_result.get(
                        "expansion_stats", {}
                    )
                    st.session_state.expansion_details = expansion_result.get(
                        "expansion_details", []
                    )

                    if expanded_keywords:
                        # 合并关键词
                        strategy_map = {"追加": "append", "替换": "replace", "交替": "interleave"}
                        merged = semantic_expander.merge_keywords(
                            st.session_state.keywords,
                            expanded_keywords,
                            strategy_map.get(merge_strategy, "append"),
                        )
                        st.session_state.keywords = merged

                        # 保存到数据库
                        try:
                            storage.save_keywords(merged, brand)
                        except Exception as e:
                            st.warning(f"关键词已扩展，但保存到数据库时出错：{e}")

                        st.success(
                            f"✅ 语义扩展完成！新增 {len(expanded_keywords)} 个关键词，总计 {len(merged)} 个"
                        )

                        # 添加撤销功能提示
                        if st.session_state.original_keywords_before_expansion:
                            if st.button(
                                "↩️ 撤销扩展",
                                key="undo_expansion",
                                use_container_width=False,
                            ):
                                st.session_state.keywords = (
                                    st.session_state.original_keywords_before_expansion.copy()
                                )
                                st.session_state.expanded_keywords = []
                                st.session_state.original_keywords_before_expansion = []
                                st.success("✅ 已撤销扩展，恢复为原始关键词列表")
                                st.rerun()
                    else:
                        st.warning("⚠️ 未生成扩展关键词，请检查输入或重试")
                except Exception as e:
                    # 区分不同类型的错误
                    error_msg = str(e)
                    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                        st.error(
                            f"""
❌ **网络连接错误**

语义扩展失败：{error_msg}

**解决建议：**
1. 检查网络连接
2. 检查 API Key 配置
3. 稍后重试
"""
                        )
                    elif (
                        "api" in error_msg.lower()
                        or "key" in error_msg.lower()
                        or "auth" in error_msg.lower()
                    ):
                        st.error(
                            f"""
❌ **API 配置错误**

语义扩展失败：{error_msg}

**解决建议：**
1. 检查侧边栏的 API Key 配置
2. 确认 API Key 有效且有足够余额
3. 检查 API 服务是否正常
"""
                        )
                    elif "json" in error_msg.lower() or "parse" in error_msg.lower():
                        st.error(
                            f"""
❌ **数据解析错误**

语义扩展失败：{error_msg}

**解决建议：**
1. 重试扩展操作
2. 如果问题持续，请联系技术支持
"""
                        )
                    else:
                        st.error(
                            f"""
❌ **语义扩展失败**

错误信息：{error_msg}

**解决建议：**
1. 检查输入的关键词是否有效
2. 重试扩展操作
3. 如果问题持续，请联系技术支持
"""
                        )

        # 显示扩展统计信息
        if st.session_state.expansion_stats:
            stats = st.session_state.expansion_stats
            st.markdown("##### 📊 扩展统计")
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.metric("扩展总数", stats.get("total_expanded", 0))
            with col2:
                st.metric("同义扩展", stats.get("synonym_count", 0))
            with col3:
                st.metric("场景扩展", stats.get("scenario_count", 0))
            with col4:
                st.metric("问题扩展", stats.get("question_count", 0))
            with col5:
                st.metric("功能扩展", stats.get("feature_count", 0))
            with col6:
                st.metric("长尾扩展", stats.get("longtail_count", 0))

            # 显示扩展详情
            if st.session_state.expansion_details:
                with st.expander("📝 扩展详情", expanded=False):
                    for detail in st.session_state.expansion_details[:10]:  # 只显示前10个
                        st.markdown(f"**原关键词**：{detail.get('original', 'N/A')}")
                        st.markdown(f"**扩展类型**：{detail.get('type', 'N/A')}")
                        expanded_list = detail.get("expanded", [])
                        if expanded_list:
                            st.markdown(
                                f"**扩展词**：{', '.join(expanded_list[:5])}"
                            )  # 只显示前5个
                        st.markdown("---")

        # 显示覆盖面分析
        if st.session_state.expanded_keywords and st.session_state.keywords:
            semantic_expander = SemanticExpander()
            # 计算原始关键词数量（扩展前的）
            original_count = len(st.session_state.keywords) - len(
                st.session_state.expanded_keywords
            )
            original_keywords = (
                st.session_state.keywords[:original_count] if original_count > 0 else []
            )

            coverage = semantic_expander.analyze_expansion_coverage(
                original_keywords,
                st.session_state.expanded_keywords,
            )

            if coverage.get("coverage_ratio", 0) > 0:
                with st.expander("📈 覆盖面分析", expanded=False):
                    st.metric(
                        "扩展比例",
                        f"{coverage.get('expansion_ratio', 0):.2f}x",
                    )
                    st.metric("唯一关键词", coverage.get("unique_keywords", 0))

                    categories = coverage.get("categories", {})
                    if categories:
                        st.markdown("**关键词类别分布：**")
                        for cat, count in categories.items():
                            if count > 0:
                                cat_name = {
                                    "question": "问题类",
                                    "scenario": "场景类",
                                    "comparison": "对比类",
                                    "feature": "功能类",
                                    "other": "其他",
                                }.get(cat, cat)
                                st.markdown(f"- {cat_name}：{count} 个")

        # 话题集群生成功能
        st.markdown("---")
        st.markdown("**🎯 话题集群生成**")
        st.caption("将关键词聚类为话题集群，系统化规划内容策略，发现内容盲区")

        # 初始化话题集群相关状态
        ss_init("topic_clusters", [])
        ss_init("cluster_relationships", [])
        ss_init("cluster_stats", None)
        ss_init("content_planning", None)

        with st.container(border=True):
            cluster_col1, cluster_col2 = st.columns([2, 1])

            with cluster_col1:
                current_keyword_count = len(st.session_state.keywords)
                # 集群数量不能超过关键词数量，也不能少于3个
                # 每个集群至少3个关键词，但确保 max_clusters >= 4（因为最小值是3）
                max_clusters = max(
                    4, min(10, max(4, current_keyword_count // 3))
                )  # 确保至少为4
                default_clusters = min(5, max_clusters)

                cluster_count = st.slider(
                    "话题集群数量",
                    3,
                    max_clusters,
                    default_clusters,
                    key="cluster_count",
                    help=f"建议范围：3-{max_clusters}个话题集群（当前有 {current_keyword_count} 个关键词）",
                )

            with cluster_col2:
                generate_clusters_btn = st.button(
                    "🚀 生成话题集群",
                    use_container_width=True,
                    disabled=(
                        (not st.session_state.cfg_valid)
                        or (gen_llm is None)
                        or (len(st.session_state.keywords) == 0)
                    ),
                    key="generate_clusters_btn",
                )

        # 执行话题聚类
        if generate_clusters_btn and gen_llm and st.session_state.keywords:
            topic_cluster = TopicCluster()
            with st.spinner(f"正在生成话题集群（目标：{cluster_count} 个）..."):
                try:
                    cluster_chain = (
                        PromptTemplate.from_template("{input}")
                        | gen_llm
                        | StrOutputParser()
                    )
                    cluster_result = topic_cluster.cluster_keywords(
                        st.session_state.keywords,
                        brand,
                        advantages,
                        cluster_count,
                        cluster_chain,
                    )

                    clusters = cluster_result.get("clusters", [])
                    relationships = cluster_result.get("relationships", [])
                    cluster_stats = cluster_result.get("cluster_stats", {})

                    st.session_state.topic_clusters = clusters
                    st.session_state.cluster_relationships = relationships
                    st.session_state.cluster_stats = cluster_stats

                    if clusters:
                        st.success(
                            f"✅ 话题集群生成完成！共生成 {len(clusters)} 个话题集群"
                        )

                        # 自动生成内容规划建议
                        with st.spinner("正在生成内容规划建议..."):
                            try:
                                planning_result = topic_cluster.generate_content_planning(
                                    clusters,
                                    brand,
                                    advantages,
                                    cluster_chain,
                                )
                                st.session_state.content_planning = planning_result
                            except Exception as e:
                                st.warning(f"内容规划生成失败：{e}")
                    else:
                        st.warning("⚠️ 未生成话题集群，请检查输入或重试")
                except Exception as e:
                    # 区分不同类型的错误
                    error_msg = str(e)
                    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                        st.error(
                            f"""
❌ **网络连接错误**

话题集群生成失败：{error_msg}

**解决建议：**
1. 检查网络连接
2. 检查 API Key 配置
3. 稍后重试
"""
                        )
                    elif (
                        "api" in error_msg.lower()
                        or "key" in error_msg.lower()
                        or "auth" in error_msg.lower()
                    ):
                        st.error(
                            f"""
❌ **API 配置错误**

话题集群生成失败：{error_msg}

**解决建议：**
1. 检查侧边栏的 API Key 配置
2. 确认 API Key 有效且有足够余额
3. 检查 API 服务是否正常
"""
                        )
                    elif "json" in error_msg.lower() or "parse" in error_msg.lower():
                        st.error(
                            f"""
❌ **数据解析错误**

话题集群生成失败：{error_msg}

**解决建议：**
1. 重试生成操作
2. 如果问题持续，请联系技术支持
"""
                        )
                    else:
                        st.error(
                            f"""
❌ **话题集群生成失败**

错误信息：{error_msg}

**解决建议：**
1. 检查输入的关键词是否有效
2. 尝试调整话题集群数量
3. 重试生成操作
4. 如果问题持续，请联系技术支持
"""
                        )

        # 显示话题集群结果
        if st.session_state.topic_clusters:
            clusters = st.session_state.topic_clusters
            relationships = st.session_state.cluster_relationships
            cluster_stats = st.session_state.cluster_stats

            # 显示统计信息
            if cluster_stats:
                st.markdown("##### 📊 话题集群统计")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("话题总数", cluster_stats.get("total_clusters", 0))
                with col2:
                    st.metric("关键词总数", cluster_stats.get("total_keywords", 0))
                with col3:
                    st.metric(
                        "平均关键词/话题",
                        f"{cluster_stats.get('avg_keywords_per_cluster', 0):.1f}",
                    )
                with col4:
                    st.metric(
                        "最大话题关键词数", cluster_stats.get("max_keywords", 0)
                    )

            # 显示话题集群列表
            st.markdown("##### 📋 话题集群列表")
            for cluster in clusters:
                with st.expander(
                    f"**{cluster.get('name', 'N/A')}** - {cluster.get('keyword_count', 0)} 个关键词 | 优先级：{cluster.get('priority', '中')}",
                    expanded=False,
                ):
                    st.markdown(f"**描述**：{cluster.get('description', '无描述')}")
                    keywords_list = cluster.get("keywords", [])
                    if keywords_list:
                        st.markdown(
                            f"**关键词**：{', '.join(keywords_list[:10])}{' ...' if len(keywords_list) > 10 else ''}"
                        )
                        st.caption(f"共 {len(keywords_list)} 个关键词")

            # 显示话题关联关系
            if relationships:
                st.markdown("##### 🔗 话题关联关系")
                rel_df = pd.DataFrame(relationships)
                st.dataframe(rel_df, use_container_width=True, hide_index=True)

            # 显示可视化（网络图）
            if len(clusters) > 1:
                st.markdown("##### 📈 话题网络图")
                try:
                    viz_data = topic_cluster.get_visualization_data(
                        clusters, relationships
                    )

                    # 准备节点数据
                    nodes = viz_data.get("nodes", [])
                    edges = viz_data.get("edges", [])

                    if nodes:
                        # 创建节点位置（简单的圆形布局）
                        n = len(nodes)
                        node_x = []
                        node_y = []
                        node_text = []
                        node_sizes = []

                        for i, node in enumerate(nodes):
                            angle = 2 * math.pi * i / n
                            radius = 1.0
                            node_x.append(radius * math.cos(angle))
                            node_y.append(radius * math.sin(angle))
                            node_text.append(
                                f"{node['name']}<br>({node['size']}个关键词)"
                            )
                            node_sizes.append(node["size"] * 3 + 10)

                        # 创建边
                        edge_x = []
                        edge_y = []
                        for edge in edges:
                            source_idx = next(
                                (
                                    i
                                    for i, nd in enumerate(nodes)
                                    if nd["id"] == edge["source"]
                                ),
                                None,
                            )
                            target_idx = next(
                                (
                                    i
                                    for i, nd in enumerate(nodes)
                                    if nd["id"] == edge["target"]
                                ),
                                None,
                            )
                            if source_idx is not None and target_idx is not None:
                                edge_x.extend(
                                    [node_x[source_idx], node_x[target_idx], None]
                                )
                                edge_y.extend(
                                    [node_y[source_idx], node_y[target_idx], None]
                                )

                        # 创建图形
                        fig = go.Figure()

                        # 添加边
                        fig.add_trace(
                            go.Scatter(
                                x=edge_x,
                                y=edge_y,
                                line=dict(width=1, color="#888"),
                                hoverinfo="none",
                                mode="lines",
                            )
                        )

                        # 添加节点
                        fig.add_trace(
                            go.Scatter(
                                x=node_x,
                                y=node_y,
                                mode="markers+text",
                                marker=dict(
                                    size=node_sizes,
                                    color="#2563EB",
                                    line=dict(width=2, color="white"),
                                ),
                                text=[node["name"] for node in nodes],
                                textposition="middle center",
                                textfont=dict(size=10, color="white"),
                                hovertext=node_text,
                                hoverinfo="text",
                                name="话题集群",
                            )
                        )

                        fig.update_layout(
                            title="话题集群网络图",
                            showlegend=False,
                            hovermode="closest",
                            margin=dict(b=20, l=5, r=5, t=40),
                            annotations=[
                                dict(
                                    text="节点大小表示关键词数量，连线表示话题关联",
                                    showarrow=False,
                                    xref="paper",
                                    yref="paper",
                                    x=0.005,
                                    y=-0.002,
                                    xanchor="left",
                                    yanchor="bottom",
                                    font=dict(size=10, color="#888"),
                                )
                            ],
                            xaxis=dict(
                                showgrid=False,
                                zeroline=False,
                                showticklabels=False,
                            ),
                            yaxis=dict(
                                showgrid=False,
                                zeroline=False,
                                showticklabels=False,
                            ),
                            height=500,
                        )

                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"可视化生成失败：{e}")

            # 显示内容规划建议
            if st.session_state.content_planning:
                planning = st.session_state.content_planning
                st.markdown("##### 💡 内容规划建议")

                # 内容盲区分析
                content_gaps = planning.get("content_gaps", [])
                if content_gaps:
                    st.markdown("**📌 内容盲区分析**")
                    for gap in content_gaps[:5]:  # 只显示前5个
                        st.markdown(
                            f"- **{gap.get('cluster_name', 'N/A')}**：{gap.get('description', 'N/A')}（优先级：{gap.get('priority', '中')}）"
                        )

                # 内容优先级
                content_priorities = planning.get("content_priorities", [])
                if content_priorities:
                    st.markdown("**🎯 内容优先级**")
                    priority_df = pd.DataFrame(content_priorities)
                    priority_df = priority_df.sort_values(
                        "priority",
                        key=lambda x: x.map({"高": 3, "中": 2, "低": 1}),
                    )
                    st.dataframe(priority_df, use_container_width=True, hide_index=True)

                # 内容建议
                content_suggestions = planning.get("content_suggestions", [])
                if content_suggestions:
                    with st.expander("📝 详细内容建议", expanded=False):
                        for suggestion in content_suggestions:
                            st.markdown(
                                f"**{suggestion.get('cluster_name', 'N/A')}**"
                            )
                            st.markdown(
                                f"- **内容类型**：{', '.join(suggestion.get('content_types', []))}"
                            )
                            st.markdown(
                                f"- **发布平台**：{', '.join(suggestion.get('platforms', []))}"
                            )
                            st.markdown(
                                f"- **关键词策略**：{suggestion.get('keyword_strategy', 'N/A')}"
                            )
                            ideas = suggestion.get("content_ideas", [])
                            if ideas:
                                st.markdown(
                                    f"- **内容创意**：{', '.join(ideas[:3])}"
                                )
                            st.markdown("---")

        # ========== 区域 5：关键词列表（条件显示） ==========
        st.markdown("---")
        st.markdown("**📋 关键词列表**")

        # 添加搜索和筛选
        search_col, filter_col = st.columns([3, 1])
        with search_col:
            search_term = st.text_input(
                "搜索关键词", key="kw_search", placeholder="🔍 输入关键词搜索...", label_visibility="collapsed"
            )
        with filter_col:
            show_original = st.checkbox(
                "仅显示原始关键词", key="kw_filter_original", value=False
            )

        # 过滤关键词
        display_keywords = st.session_state.keywords
        if search_term and search_term.strip():  # 检查非空字符串
            search_term_lower = search_term.strip().lower()
            display_keywords = [
                kw for kw in display_keywords if search_term_lower in kw.lower()
            ]
        if show_original and st.session_state.expanded_keywords:
            original_count = len(st.session_state.keywords) - len(
                st.session_state.expanded_keywords
            )
            display_keywords = (
                display_keywords[:original_count] if original_count > 0 else []
            )

        # 显示列表（分页）
        if display_keywords:
            page_size = 20
            total_pages = max(1, (len(display_keywords) - 1) // page_size + 1)
            page = st.session_state.get("kw_page", 1)

            if total_pages > 1:
                page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
                with page_col2:
                    page = st.selectbox(
                        "页码",
                        range(1, total_pages + 1),
                        index=min(page - 1, total_pages - 1),
                        key="kw_page_select",
                    )
                    st.session_state.kw_page = page
            else:
                page = 1

            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_keywords = display_keywords[start_idx:end_idx]

            df = pd.DataFrame(page_keywords, columns=["长尾关键词/问题"])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.caption(
                f"显示第 {start_idx + 1}-{min(end_idx, len(display_keywords))} 条，共 {len(display_keywords)} 条关键词"
            )

            # 区分原始和扩展关键词
            if st.session_state.expanded_keywords:
                original_count = len(st.session_state.keywords) - len(
                    st.session_state.expanded_keywords
                )
                st.info(
                    f"📌 原始关键词：{original_count} 个 | 🆕 扩展关键词：{len(st.session_state.expanded_keywords)} 个"
                )
        else:
            if search_term or show_original:
                st.info("未找到匹配的关键词")
            else:
                st.info("暂无关键词")

        # 下载按钮
        st.download_button(
            "📥 下载关键词 CSV",
            pd.DataFrame(
                st.session_state.keywords, columns=["长尾关键词/问题"]
            ).to_csv(index=False, encoding="utf-8-sig"),
            f"{sanitize_filename(brand,40)}_keywords.csv",
            mime="text/csv",
            use_container_width=True,
            key="kw_dl_csv",
        )

        # ========== 区域 6：智能挖掘（条件显示，默认折叠） ==========
        st.markdown("---")
        with st.expander("🔍 智能关键词挖掘与趋势分析", expanded=False):
            st.caption(
                "发现高价值关键词，分析竞争度，预测趋势，优化关键词策略"
            )

            # 初始化关键词挖掘器
            keyword_miner = KeywordMining(storage)

            # 创建子标签页
            mining_tab1, mining_tab2, mining_tab3, mining_tab4 = st.tabs(
                [
                    "🌐 行业热点挖掘",
                    "📊 竞争度分析",
                    "📈 趋势预测",
                    "💎 价值矩阵",
                ]
            )

            with mining_tab1:
                st.caption("基于行业趋势自动挖掘高价值关键词")

                with st.container(border=True):
                    # 默认使用 brand，允许覆盖
                    default_industry = brand if brand else ""
                    industry = st.text_input(
                        "行业领域",
                        value=default_industry,
                        key="mining_industry",
                        help="输入您的行业领域，如：AI工具、SaaS产品、电商平台等",
                    )
                num_mine = st.slider("挖掘数量", 10, 50, 20, key="mining_num")

                mine_btn = st.button(
                    "🚀 开始挖掘",
                    use_container_width=True,
                    disabled=(not st.session_state.cfg_valid) or (gen_llm is None),
                )

            ss_init("mined_keywords", [])

            if mine_btn and gen_llm and industry:
                with st.spinner(f"正在挖掘行业关键词（目标：{num_mine} 个）..."):
                    try:
                        mine_chain = (
                            PromptTemplate.from_template("{input}")
                            | gen_llm
                            | StrOutputParser()
                        )
                        mined_keywords = keyword_miner.mine_industry_keywords(
                            brand=brand,
                            industry=industry,
                            advantages=advantages,
                            num_keywords=num_mine,
                            llm_chain=mine_chain,
                        )

                        if mined_keywords:
                            st.session_state.mined_keywords = mined_keywords
                            st.success(
                                f"✅ 挖掘完成！发现 {len(mined_keywords)} 个关键词"
                            )
                        else:
                            st.warning(
                                "⚠️ 未挖掘到关键词，请检查输入或重试"
                            )
                    except Exception as e:
                        st.error(f"挖掘失败：{e}")

            # 显示挖掘结果
            if st.session_state.mined_keywords:
                mined_kw_list = st.session_state.mined_keywords
                st.markdown("##### 📋 挖掘结果")

                for i, kw_data in enumerate(mined_kw_list):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{kw_data.get('keyword', 'N/A')}**")
                            st.caption(
                                f"类别：{kw_data.get('category', 'N/A')} | 意图：{kw_data.get('intent', 'N/A')}"
                            )
                        with col2:
                            st.metric(
                                "预估价值",
                                f"{kw_data.get('estimated_value', 0)}/10",
                            )
                        with col3:
                            if st.button(
                                "添加",
                                key=f"add_mined_{i}",
                                use_container_width=True,
                            ):
                                if kw_data.get("keyword") not in st.session_state.keywords:
                                    st.session_state.keywords.append(
                                        kw_data.get("keyword")
                                    )
                                    storage.save_keywords(
                                        [kw_data.get("keyword")], brand
                                    )
                                    st.success("已添加")
                                    st.rerun()

            with mining_tab2:
                st.caption("分析关键词在 AI 中的提及频率和竞争程度")

                keywords_to_analyze = st.multiselect(
                    "选择要分析的关键词",
                    options=st.session_state.keywords
                    if st.session_state.keywords
                    else [],
                    key="comp_keywords_select",
                    help="选择要分析竞争度的关键词",
                )

                analyze_comp_btn = st.button(
                    "📊 开始分析",
                    use_container_width=True,
                    disabled=len(keywords_to_analyze) == 0,
                )

                ss_init("competition_analysis", {})

                if analyze_comp_btn and keywords_to_analyze:
                    with st.spinner("正在分析竞争度..."):
                        try:
                            competition_data = keyword_miner.analyze_competition(
                                keywords=keywords_to_analyze,
                                brand=brand,
                            )
                            st.session_state.competition_analysis = competition_data
                            st.success("✅ 分析完成！")
                        except Exception as e:
                            st.error(f"分析失败：{e}")

                if st.session_state.competition_analysis:
                    comp_data = st.session_state.competition_analysis
                    st.markdown("##### 📊 竞争度分析结果")

                    comp_df_data = []
                    for keyword, data in comp_data.items():
                        comp_df_data.append(
                            {
                                "关键词": keyword,
                                "提及率": f"{data.get('mention_rate', 0):.2%}",
                                "竞争级别": data.get("competition_level", "未知"),
                                "竞品提及": data.get("competitor_mentions", 0),
                                "总提及": data.get("total_mentions", 0),
                                "数据点": data.get("data_points", 0),
                            }
                        )

                    if comp_df_data:
                        comp_df = pd.DataFrame(comp_df_data)
                        st.dataframe(comp_df, use_container_width=True, hide_index=True)

                        if len(comp_df_data) > 0:
                            fig = px.bar(
                                comp_df,
                                x="关键词",
                                y="提及率",
                                color="竞争级别",
                                title="关键词竞争度分析",
                                labels={"提及率": "提及率 (%)"},
                            )
                            fig.update_xaxes(tickangle=-45)
                            st.plotly_chart(fig, use_container_width=True)

            with mining_tab3:
                st.caption("基于历史数据预测关键词热度变化趋势")

                keywords_to_predict = st.multiselect(
                    "选择要预测的关键词",
                    options=st.session_state.keywords
                    if st.session_state.keywords
                    else [],
                    key="trend_keywords_select",
                    help="选择要预测趋势的关键词",
                )

                predict_days = st.slider(
                    "预测未来天数", 7, 90, 30, key="predict_days"
                )
                predict_btn = st.button(
                    "🔮 开始预测",
                    use_container_width=True,
                    disabled=len(keywords_to_predict) == 0,
                )

                ss_init("trend_analysis", {})

                if predict_btn and keywords_to_predict:
                    with st.spinner("正在预测趋势..."):
                        try:
                            trend_data = keyword_miner.predict_trend(
                                keywords=keywords_to_predict,
                                brand=brand,
                                days=predict_days,
                            )
                            st.session_state.trend_analysis = trend_data
                            st.success("✅ 预测完成！")
                        except Exception as e:
                            st.error(f"预测失败：{e}")

                if st.session_state.trend_analysis:
                    trend_data = st.session_state.trend_analysis
                    st.markdown("##### 📈 趋势预测结果")

                    trend_df_data = []
                    for keyword, data in trend_data.items():
                        trend_df_data.append(
                            {
                                "关键词": keyword,
                                "当前提及率": f"{data.get('current_rate', 0):.2%}",
                                "预测提及率": f"{data.get('predicted_mention_rate', 0):.2%}",
                                "趋势": data.get("trend", "未知"),
                                "趋势强度": f"{data.get('trend_strength', 0):.2%}",
                                "置信度": f"{data.get('confidence', 0):.2%}",
                                "数据点": data.get("data_points", 0),
                            }
                        )

                    if trend_df_data:
                        trend_df = pd.DataFrame(trend_df_data)
                        st.dataframe(trend_df, use_container_width=True, hide_index=True)

            with mining_tab4:
                st.caption("分析关键词的价值和竞争度，找到最优投入策略")

                keywords_for_matrix = st.multiselect(
                    "选择要分析的关键词",
                    options=st.session_state.keywords
                    if st.session_state.keywords
                    else [],
                    key="matrix_keywords_select",
                    help="选择要分析价值矩阵的关键词",
                )

                estimated_values = {}
                if st.session_state.mined_keywords:
                    for kw_data in st.session_state.mined_keywords:
                        if kw_data.get("keyword") in keywords_for_matrix:
                            estimated_values[kw_data.get("keyword")] = kw_data.get(
                                "estimated_value", 5
                            )

                analyze_matrix_btn = st.button(
                    "💎 开始分析",
                    use_container_width=True,
                    disabled=len(keywords_for_matrix) == 0,
                )

                ss_init("value_matrix", {})
                ss_init("keyword_recommendations", [])

                if analyze_matrix_btn and keywords_for_matrix:
                    with st.spinner("正在分析价值矩阵..."):
                        try:
                            if not st.session_state.competition_analysis:
                                competition_data = keyword_miner.analyze_competition(
                                    keywords=keywords_for_matrix,
                                    brand=brand,
                                )
                            else:
                                competition_data = (
                                    st.session_state.competition_analysis
                                )

                            value_matrix = keyword_miner.calculate_value_matrix(
                                keywords=keywords_for_matrix,
                                competition_data=competition_data,
                                estimated_values=estimated_values
                                if estimated_values
                                else None,
                            )
                            st.session_state.value_matrix = value_matrix

                            trend_data = (
                                st.session_state.trend_analysis
                                if st.session_state.trend_analysis
                                else None
                            )

                            recommendations = keyword_miner.recommend_keywords(
                                keywords=keywords_for_matrix,
                                value_matrix=value_matrix,
                                competition_data=competition_data,
                                trend_data=trend_data,
                                top_n=len(keywords_for_matrix),
                            )
                            st.session_state.keyword_recommendations = recommendations

                            st.success("✅ 分析完成！")
                        except Exception as e:
                            st.error(f"分析失败：{e}")

                if st.session_state.value_matrix:
                    matrix_data = st.session_state.value_matrix
                    st.markdown("##### 💎 价值矩阵结果")

                    matrix_df_data = []
                    for keyword, data in matrix_data.items():
                        matrix_df_data.append(
                            {
                                "关键词": keyword,
                                "价值分数": data.get("value_score", 0),
                                "竞争分数": data.get("competition_score", 0),
                                "矩阵位置": data.get("matrix_position", "未知"),
                                "推荐建议": data.get("recommendation", ""),
                            }
                        )

                    if matrix_df_data:
                        matrix_df = pd.DataFrame(matrix_df_data)
                        st.dataframe(matrix_df, use_container_width=True, hide_index=True)

                        if len(matrix_df_data) > 0:
                            fig = px.scatter(
                                matrix_df,
                                x="竞争分数",
                                y="价值分数",
                                color="矩阵位置",
                                size=[10] * len(matrix_df),
                                hover_data=["关键词", "推荐建议"],
                                title="关键词价值矩阵",
                                labels={
                                    "竞争分数": "竞争度（越高越激烈）",
                                    "价值分数": "价值（0-10分）",
                                },
                            )
                            st.plotly_chart(fig, use_container_width=True)

                if st.session_state.keyword_recommendations:
                    recommendations = st.session_state.keyword_recommendations
                    st.markdown("##### ⭐ 智能推荐（按推荐度排序）")

                    for i, rec in enumerate(recommendations[:10], 1):
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            with col1:
                                st.markdown(
                                    f"**{i}. {rec.get('keyword', 'N/A')}**"
                                )
                                st.caption(rec.get("recommendation", ""))
                            with col2:
                                st.metric(
                                    "推荐分",
                                    f"{rec.get('recommendation_score', 0):.1f}",
                                )
                            with col3:
                                st.metric(
                                    "价值", f"{rec.get('value_score', 0):.1f}"
                                )
                            with col4:
                                trend_emoji = {
                                    "上升": "📈",
                                    "下降": "📉",
                                    "稳定": "➡️",
                                }.get(rec.get("trend", "稳定"), "➡️")
                                st.metric(
                                    "趋势",
                                    f"{trend_emoji} {rec.get('trend', '稳定')}",
                                )
    else:
        st.info("在左侧完成配置后，点击“生成关键词”。")

