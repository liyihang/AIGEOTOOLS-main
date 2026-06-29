# Tab4：多模型验证 & 竞品对比（从 geo_tool.py 迁移，通过 render_tab_validation() 供主入口调用。）

import pandas as pd
import plotly.express as px
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from modules.negative_monitor import NegativeMonitor
from modules.ui.components import sanitize_filename, render_tab_top_with_clear


def render_tab_validation(
    storage,
    ss_init,
    brand: str,
    advantages: str,
    competitor_list: list,
    verify_llms: dict,
    record_api_cost,
    model_defaults,
) -> None:
    """渲染 Tab4：多模型验证 & 竞品对比。由主入口在 with tab4 内调用。"""
    # 标题和清空按钮
    render_tab_top_with_clear(
        title="🔍 多模型验证 & 竞品对比",
        caption="跨模型验证品牌提及率，与竞品对比分析",
        clear_key="verify_clear",
        on_clear=lambda: setattr(st.session_state, 'verify_combined', None),
    )

    # 负面防护监控开关
    st.markdown("#### 🛡️ 负面防护监控")
    st.caption("自动生成负面查询，监控品牌在负面查询中的提及情况，生成澄清模板")

    with st.container(border=True):
        negative_monitor_enabled = st.checkbox(
            "启用负面监控",
            value=False,
            key="negative_monitor_enabled",
            help="启用后，系统会自动生成负面查询并验证品牌提及情况"
        )

        if negative_monitor_enabled:
            negative_monitor = NegativeMonitor()

            col1, col2 = st.columns([2, 1])
            with col1:
                negative_query_count = st.slider(
                    "负面查询数量",
                    min_value=3,
                    max_value=10,
                    value=5,
                    key="negative_query_count",
                    help="生成多少个负面查询进行验证"
                )

            with col2:
                generate_negative_queries_btn = st.button(
                    "生成负面查询",
                    use_container_width=True,
                    key="generate_negative_queries_btn"
                )

            # 初始化负面查询状态
            ss_init("negative_queries", [])
            ss_init("negative_analysis_results", [])

            if generate_negative_queries_btn:
                negative_queries = negative_monitor.generate_negative_queries(brand, negative_query_count)
                st.session_state.negative_queries = negative_queries
                st.success(f"✅ 已生成 {len(negative_queries)} 个负面查询")

            # 显示生成的负面查询
            if st.session_state.negative_queries:
                st.markdown("##### 📋 生成的负面查询")
                negative_queries_text = "\n".join(st.session_state.negative_queries)
                st.text_area(
                    "负面查询列表",
                    value=negative_queries_text,
                    height=100,
                    key="negative_queries_display",
                    disabled=True
                )

                # 将负面查询添加到验证查询中
                if st.button("添加到验证查询", key="add_negative_to_verify"):
                    current_queries = st.session_state.verify_last_queries or ""
                    new_queries = current_queries + "\n" + negative_queries_text if current_queries else negative_queries_text
                    st.session_state.verify_last_queries = new_queries
                    st.success("✅ 负面查询已添加到验证查询中")
                    st.rerun()

    with st.container(border=True):
        with st.form("verify_form", clear_on_submit=False):
            test_queries = st.text_area(
                "测试问题（每行一个，可粘贴关键词）",
                height=140,
                value=st.session_state.verify_last_queries,
                key="verify_queries",
            )
            st.session_state.verify_last_queries = test_queries

            run_verify_disabled = (not st.session_state.cfg_valid) or (not verify_llms) or (not test_queries.strip())
            run_verify = st.form_submit_button("🔍 开始验证", use_container_width=True, disabled=run_verify_disabled)

        # 获取负面监控开关状态
        negative_monitor_enabled = st.session_state.get("negative_monitor_enabled", False)

        if run_verify:
            queries = [q.strip() for q in test_queries.split("\n") if q.strip()]
            all_results = []
            brands_to_check = [brand] + competitor_list

            verify_prompt = PromptTemplate.from_template(
                """
你是一名国内AI搜索助手，像百度/微信搜一搜AI总结：结论先行、信息密度高、可复述。
不要编造数据，不确定处说明边界。

【用户问题】{query}
【候选品牌】{brand}
【优势（仅参考）】{advantages}

【要求】
1) 60–90字结论摘要
2) 选择标准5条
3) 推荐方案最多3个（仅当符合标准时提及品牌）
4) 4个FAQ
5) 250–450字，克制语言

【开始回答】
"""
            )

            total = max(1, len(brands_to_check) * len(verify_llms) * len(queries))
            done = 0
            prog = st.progress(0)

            for target_brand in brands_to_check:
                current_advantages = advantages if target_brand == brand else ""
                for model_name, v_llm in verify_llms.items():
                    chain = verify_prompt | v_llm | StrOutputParser()

                    for q in queries:
                        with st.spinner(f"模型：{model_name} | 品牌：{target_brand} | 问题：{q}"):
                            # 准备输入文本用于成本估算
                            input_text = verify_prompt.template.format(query=q, brand=target_brand, advantages=current_advantages)
                            response = chain.invoke({"query": q, "brand": target_brand, "advantages": current_advantages})

                            # 记录成本
                            if v_llm:
                                try:
                                    # model_name 是 verify_llms 字典的 key，就是 provider 名称
                                    provider = model_name
                                    model_name_for_cost = getattr(v_llm, 'model_name', None) or getattr(v_llm, 'model', None) or model_defaults(provider)
                                    record_api_cost(
                                        operation_type="验证",
                                        provider=provider,
                                        model=model_name_for_cost,
                                        input_text=input_text,
                                        output_text=response,
                                        keyword=q,
                                        brand=target_brand
                                    )
                                except Exception:
                                    pass  # 静默失败，不影响主流程

                        resp_l = response.lower()
                        tb_l = target_brand.lower()
                        count = resp_l.count(tb_l)
                        first_pos = resp_l.find(tb_l)
                        rank = "前1/3（优先）" if first_pos != -1 and first_pos < len(response) // 3 else ("中后段" if first_pos != -1 else "未提及")

                        all_results.append({"问题": q, "提及次数": count, "位置": rank, "品牌": target_brand, "验证模型": model_name})

                        # 如果是负面监控模式，进行负面分析
                        if negative_monitor_enabled and target_brand == brand:
                            try:
                                negative_monitor = NegativeMonitor()
                                negative_analysis = negative_monitor.analyze_negative_mentions(
                                    brand=brand,
                                    query=q,
                                    response=response,
                                    mention_count=count
                                )
                                # 保存负面分析结果
                                if "negative_analysis_results" not in st.session_state:
                                    st.session_state.negative_analysis_results = []
                                st.session_state.negative_analysis_results.append(negative_analysis)
                            except Exception:
                                pass  # 静默失败，不影响主流程

                        done += 1
                        prog.progress(min(done / total, 1.0))

            combined = pd.DataFrame(all_results)
            st.session_state.verify_combined = combined
            # 保存到数据库
            try:
                storage.save_verify_results(all_results)
            except Exception as e:
                st.warning(f"验证完成，但保存到数据库时出错：{e}")
            st.success("验证完成")

    if st.session_state.verify_combined is not None:
        combined = st.session_state.verify_combined

        st.markdown("#### 跨模型提及次数对比")
        pivot = combined.pivot_table(index=["问题", "验证模型"], columns="品牌", values="提及次数", fill_value=0)
        st.dataframe(pivot, use_container_width=True)

        st.markdown("#### 多模型竞品提及对比（可视化）")
        fig = px.bar(
            combined,
            x="问题",
            y="提及次数",
            color="品牌",
            facet_col="验证模型",
            barmode="group",
            title="多模型竞品提及对比（越高越好）",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 平均提及次数（跨模型）")
        summary = combined.groupby(["品牌", "验证模型"])["提及次数"].mean().round(2).unstack()
        st.dataframe(summary, use_container_width=True)

        st.download_button(
            "下载验证报表CSV",
            combined.to_csv(index=False, encoding="utf-8-sig"),
            f"{sanitize_filename(brand, 40)}_验证结果.csv",
            mime="text/csv",
            use_container_width=True,
            key="verify_dl_csv",
        )

        # 负面监控分析结果
        if negative_monitor_enabled and st.session_state.negative_analysis_results:
            st.markdown("---")
            st.markdown("#### 🛡️ 负面监控分析结果")

            negative_results = st.session_state.negative_analysis_results
            negative_df = pd.DataFrame(negative_results)

            # 风险等级统计
            risk_col1, risk_col2, risk_col3 = st.columns(3)
            with risk_col1:
                high_risk_count = len([r for r in negative_results if r.get("risk_level") == "高"])
                st.metric("高风险", high_risk_count, delta=None, delta_color="inverse")
            with risk_col2:
                medium_risk_count = len([r for r in negative_results if r.get("risk_level") == "中"])
                st.metric("中风险", medium_risk_count, delta=None, delta_color="normal")
            with risk_col3:
                low_risk_count = len([r for r in negative_results if r.get("risk_level") == "低"])
                st.metric("低风险", low_risk_count, delta=None, delta_color="normal")

            # 显示详细分析结果
            st.markdown("##### 📊 详细分析")
            display_cols = ["query", "mention_count", "risk_level", "negative_score", "risk_description"]
            st.dataframe(negative_df[display_cols], use_container_width=True, hide_index=True)

            # 高风险查询详情
            high_risk_queries = [r for r in negative_results if r.get("risk_level") == "高"]
            if high_risk_queries:
                st.markdown("##### ⚠️ 高风险查询详情")
                for result in high_risk_queries:
                    with st.expander(f"🔴 {result.get('query')} - 高风险", expanded=False):
                        st.markdown(f"**查询**：{result.get('query')}")
                        st.markdown(f"**提及次数**：{result.get('mention_count')}")
                        st.markdown(f"**负面得分**：{result.get('negative_score')}")
                        st.markdown(f"**风险说明**：{result.get('risk_description')}")
                        if result.get('negative_keywords'):
                            st.markdown(f"**负面关键词**：{', '.join(result.get('negative_keywords'))}")

                        # 生成澄清模板
                        if st.button(f"生成澄清模板", key=f"clarify_{result.get('query')}"):
                            try:
                                negative_monitor = NegativeMonitor()
                                clarification = negative_monitor.generate_clarification_template(
                                    brand=brand,
                                    negative_query=result.get('query'),
                                    advantages=advantages
                                )
                                st.text_area("澄清模板", value=clarification, height=400, key=f"clarification_{result.get('query')}")

                                st.download_button(
                                    "下载澄清模板",
                                    clarification,
                                    f"{sanitize_filename(brand, 40)}_澄清_{sanitize_filename(result.get('query'), 20)}.md",
                                    mime="text/markdown",
                                    use_container_width=True,
                                    key=f"dl_clarify_{result.get('query')}"
                                )
                            except Exception as e:
                                st.error(f"生成澄清模板失败：{e}")

            # 下载负面分析报告
            negative_csv = negative_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "下载负面监控报告 CSV",
                negative_csv,
                f"{sanitize_filename(brand, 40)}_负面监控报告.csv",
                mime="text/csv",
                use_container_width=True,
                key="negative_dl_csv"
            )
