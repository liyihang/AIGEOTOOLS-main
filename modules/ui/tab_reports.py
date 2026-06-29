# Tab6：AI 数据报表（从 geo_tool.py 迁移，通过 render_tab_reports() 供主入口调用。）

import json
import re

import pandas as pd
import plotly.express as px
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from modules.content_metrics import ContentMetricsAnalyzer
from modules.negative_monitor import NegativeMonitor
from modules.roi_analyzer import ROIAnalyzer
from modules.topic_cluster import TopicCluster
from modules.ui.components import sanitize_filename


def render_tab_reports(
    storage,
    ss_init,
    gen_llm,
    brand: str,
    advantages: str,
    competitor_list: list,
    verify_llms: dict,
    record_api_cost,
    model_defaults,
) -> None:
    """渲染 Tab6：AI 数据报表。由主入口在 with tab6 内调用。"""
    st.markdown("### 📊 AI 数据报表")
    st.caption("自动化监控 GEO 效果，数据驱动优化内容策略")

    # 获取历史关键词用于自动验证
    historical_keywords = storage.get_keywords(brand=brand)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("#### 🚀 自动验证任务")
        st.caption("使用历史关键词自动进行多模型验证，生成数据报表")

    with col2:
        auto_verify_btn = st.button("开始自动验证", use_container_width=True, 
                                     disabled=(not st.session_state.cfg_valid) or (not verify_llms) or (len(historical_keywords) == 0))

    with col3:
        if st.button("刷新报表", use_container_width=True):
            st.rerun()

    if len(historical_keywords) == 0:
        st.info("💡 提示：请先在【1 关键词蒸馏】生成关键词，然后才能进行自动验证。")
    elif not verify_llms:
        st.warning("⚠️ 请先在侧边栏配置至少一个验证用 LLM。")

    # 自动验证逻辑
    if auto_verify_btn and historical_keywords and verify_llms:
        # 选择要验证的关键词（最多20个，避免API费用过高）
        keywords_to_verify = historical_keywords[:20]

        st.info(f"📝 将验证 {len(keywords_to_verify)} 个关键词，共 {len(verify_llms)} 个模型，预计需要 {len(keywords_to_verify) * len(verify_llms) * (1 + len(competitor_list))} 次 API 调用")

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

        total = max(1, len(brands_to_check) * len(verify_llms) * len(keywords_to_verify))
        done = 0
        prog = st.progress(0)
        status_text = st.empty()

        for target_brand in brands_to_check:
            current_advantages = advantages if target_brand == brand else ""
            for model_name, v_llm in verify_llms.items():
                chain = verify_prompt | v_llm | StrOutputParser()

                for q in keywords_to_verify:
                    status_text.text(f"验证中：{target_brand} | {model_name} | {q}")
                    try:
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
                    except Exception as e:
                        st.warning(f"验证失败：{target_brand} | {model_name} | {q} - {str(e)}")

                    done += 1
                    prog.progress(min(done / total, 1.0))

        # 保存验证结果
        if all_results:
            try:
                storage.save_verify_results(all_results)
                st.success(f"✅ 自动验证完成！共验证 {len(all_results)} 条记录")
            except Exception as e:
                st.warning(f"验证完成，但保存到数据库时出错：{e}")

        status_text.empty()
        prog.empty()

    # 获取所有验证数据（带时间戳）
    verify_df = storage.get_verify_results(brand=brand, include_timestamp=True)

    if verify_df.empty:
        st.info("📊 暂无验证数据。请先运行自动验证任务或手动验证。")
    else:
        # 数据概览
        st.markdown("#### 📈 数据概览")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_verifications = len(verify_df)
            st.metric("总验证次数", total_verifications)

        with col2:
            avg_mentions = verify_df[verify_df["品牌"] == brand]["提及次数"].mean() if len(verify_df[verify_df["品牌"] == brand]) > 0 else 0
            st.metric("平均提及次数", f"{avg_mentions:.2f}")

        with col3:
            if "验证时间" in verify_df.columns:
                latest_date = verify_df["验证时间"].max()
                st.metric("最新验证时间", latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "N/A")
            else:
                st.metric("最新验证时间", "N/A")

        with col4:
            unique_queries = verify_df["问题"].nunique()
            st.metric("已验证关键词", unique_queries)

        # 1. 提及率趋势图
        if "验证时间" in verify_df.columns and len(verify_df) > 0:
            st.markdown("#### 📊 提及率趋势图")

            # 按日期聚合数据
            brand_df = verify_df[verify_df["品牌"] == brand].copy()
            if len(brand_df) > 0:
                brand_df["日期"] = brand_df["验证时间"].dt.date
                daily_mentions = brand_df.groupby(["日期", "验证模型"])["提及次数"].mean().reset_index()
                daily_mentions["日期"] = pd.to_datetime(daily_mentions["日期"])

                fig_trend = px.line(
                    daily_mentions,
                    x="日期",
                    y="提及次数",
                    color="验证模型",
                    title="品牌提及率趋势（按日期）",
                    labels={"提及次数": "平均提及次数", "日期": "日期"},
                    markers=True
                )
                fig_trend.update_layout(hovermode='x unified')
                st.plotly_chart(fig_trend, use_container_width=True)

        # 2. 平台贡献度分析（基于文章平台）
        st.markdown("#### 🌐 平台贡献度分析")

        articles = storage.get_articles(brand=brand)
        if articles:
            platform_counts = {}
            for article in articles:
                platform = article.get("platform", "未知")
                platform_counts[platform] = platform_counts.get(platform, 0) + 1

            platform_df = pd.DataFrame(list(platform_counts.items()), columns=["平台", "文章数量"])
            platform_df = platform_df.sort_values("文章数量", ascending=False)

            fig_platform = px.bar(
                platform_df,
                x="平台",
                y="文章数量",
                title="各平台文章数量分布",
                labels={"文章数量": "文章数量", "平台": "发布平台"},
                color="文章数量",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_platform, use_container_width=True)
        else:
            st.info("暂无文章数据。")

        # 话题集群分析模块
        st.markdown("#### 🎯 话题集群分析")
        st.caption("基于历史关键词生成话题集群，分析内容覆盖情况，发现内容盲区")

        # 初始化话题集群分析相关状态
        ss_init("tab6_topic_clusters", [])
        ss_init("tab6_cluster_relationships", [])
        ss_init("tab6_cluster_stats", None)
        ss_init("tab6_content_planning", None)

        with st.container(border=True):
            tab6_cluster_col1, tab6_cluster_col2 = st.columns([2, 1])

            with tab6_cluster_col1:
                tab6_cluster_count = st.slider(
                    "话题集群数量",
                    3,
                    10,
                    5,
                    key="tab6_cluster_count",
                    help="建议范围：3-10个话题集群"
                )

            with tab6_cluster_col2:
                tab6_generate_clusters_btn = st.button(
                    "🚀 生成话题集群分析",
                    use_container_width=True,
                    disabled=(not st.session_state.cfg_valid) or (gen_llm is None) or (len(historical_keywords) == 0),
                    key="tab6_generate_clusters_btn"
                )

        # 执行话题聚类分析
        if tab6_generate_clusters_btn and gen_llm and historical_keywords:
            topic_cluster = TopicCluster()
            with st.spinner(f"正在分析话题集群（目标：{tab6_cluster_count} 个）..."):
                try:
                    cluster_chain = PromptTemplate.from_template("{input}") | gen_llm | StrOutputParser()
                    cluster_result = topic_cluster.cluster_keywords(
                        historical_keywords,
                        brand,
                        advantages,
                        tab6_cluster_count,
                        cluster_chain
                    )

                    clusters = cluster_result.get("clusters", [])
                    relationships = cluster_result.get("relationships", [])
                    cluster_stats = cluster_result.get("cluster_stats", {})

                    st.session_state.tab6_topic_clusters = clusters
                    st.session_state.tab6_cluster_relationships = relationships
                    st.session_state.tab6_cluster_stats = cluster_stats

                    if clusters:
                        st.success(f"✅ 话题集群分析完成！共生成 {len(clusters)} 个话题集群")

                        # 分析覆盖情况
                        coverage = topic_cluster.analyze_cluster_coverage(clusters, historical_keywords)

                        # 生成内容规划建议
                        with st.spinner("正在生成内容规划建议..."):
                            try:
                                planning_result = topic_cluster.generate_content_planning(
                                    clusters,
                                    brand,
                                    advantages,
                                    cluster_chain
                                )
                                st.session_state.tab6_content_planning = planning_result
                            except Exception as e:
                                st.warning(f"内容规划生成失败：{e}")
                    else:
                        st.warning("⚠️ 未生成话题集群，请检查输入或重试")
                except Exception as e:
                    st.error(f"话题集群分析失败：{e}")

        # 显示话题集群分析结果
        if st.session_state.tab6_topic_clusters:
            clusters = st.session_state.tab6_topic_clusters
            relationships = st.session_state.tab6_cluster_relationships
            cluster_stats = st.session_state.tab6_cluster_stats

            # 显示统计信息
            if cluster_stats:
                st.markdown("##### 📊 话题集群统计")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("话题总数", cluster_stats.get("total_clusters", 0))
                with col2:
                    st.metric("关键词总数", cluster_stats.get("total_keywords", 0))
                with col3:
                    st.metric("平均关键词/话题", f"{cluster_stats.get('avg_keywords_per_cluster', 0):.1f}")
                with col4:
                    st.metric("最大话题关键词数", cluster_stats.get("max_keywords", 0))

            # 话题分布可视化
            if clusters:
                st.markdown("##### 📈 话题分布图")
                cluster_names = [c.get("name", "N/A") for c in clusters]
                cluster_counts = [c.get("keyword_count", 0) for c in clusters]

                cluster_dist_df = pd.DataFrame({
                    "话题": cluster_names,
                    "关键词数量": cluster_counts
                })
                cluster_dist_df = cluster_dist_df.sort_values("关键词数量", ascending=False)

                fig_cluster_dist = px.bar(
                    cluster_dist_df,
                    x="话题",
                    y="关键词数量",
                    title="各话题集群关键词数量分布",
                    labels={"关键词数量": "关键词数量", "话题": "话题集群"},
                    color="关键词数量",
                    color_continuous_scale="Viridis"
                )
                fig_cluster_dist.update_xaxes(tickangle=-45)
                st.plotly_chart(fig_cluster_dist, use_container_width=True)

            # 显示话题集群列表
            st.markdown("##### 📋 话题集群详情")
            for cluster in clusters:
                with st.expander(f"**{cluster.get('name', 'N/A')}** - {cluster.get('keyword_count', 0)} 个关键词 | 优先级：{cluster.get('priority', '中')}", expanded=False):
                    st.markdown(f"**描述**：{cluster.get('description', '无描述')}")
                    keywords_list = cluster.get('keywords', [])
                    if keywords_list:
                        st.markdown(f"**关键词**：{', '.join(keywords_list[:15])}{' ...' if len(keywords_list) > 15 else ''}")
                        st.caption(f"共 {len(keywords_list)} 个关键词")

            # 显示话题关联关系
            if relationships:
                st.markdown("##### 🔗 话题关联关系")
                rel_df = pd.DataFrame(relationships)
                st.dataframe(rel_df, use_container_width=True, hide_index=True)

            # 显示内容规划建议
            if st.session_state.tab6_content_planning:
                planning = st.session_state.tab6_content_planning
                st.markdown("##### 💡 内容规划建议")

                # 内容盲区分析
                content_gaps = planning.get("content_gaps", [])
                if content_gaps:
                    st.markdown("**📌 内容盲区分析**")
                    gaps_df = pd.DataFrame(content_gaps)
                    st.dataframe(gaps_df, use_container_width=True, hide_index=True)

                # 内容优先级
                content_priorities = planning.get("content_priorities", [])
                if content_priorities:
                    st.markdown("**🎯 内容优先级**")
                    priority_df = pd.DataFrame(content_priorities)
                    priority_df = priority_df.sort_values("priority", key=lambda x: x.map({"高": 3, "中": 2, "低": 1}), ascending=False)
                    st.dataframe(priority_df, use_container_width=True, hide_index=True)

                # 内容建议
                content_suggestions = planning.get("content_suggestions", [])
                if content_suggestions:
                    with st.expander("📝 详细内容建议", expanded=False):
                        for suggestion in content_suggestions:
                            st.markdown(f"**{suggestion.get('cluster_name', 'N/A')}**")
                            st.markdown(f"- **内容类型**：{', '.join(suggestion.get('content_types', []))}")
                            st.markdown(f"- **发布平台**：{', '.join(suggestion.get('platforms', []))}")
                            st.markdown(f"- **关键词策略**：{suggestion.get('keyword_strategy', 'N/A')}")
                            ideas = suggestion.get('content_ideas', [])
                            if ideas:
                                st.markdown(f"- **内容创意**：{', '.join(ideas[:3])}")

        # ROI 分析与成本优化模块
        st.markdown("#### 💰 ROI 分析与成本优化")
        st.caption("量化 GEO 投入产出比，优化成本结构，数据驱动决策")

        # 初始化 ROI 分析器
        roi_analyzer = ROIAnalyzer()

        # 获取 API 调用记录
        api_calls_df = storage.get_api_calls(brand=brand)

        if api_calls_df.empty:
            st.info("📊 暂无 API 调用记录。开始使用工具后，成本数据将自动记录。")
        else:
            # 成本分析
            cost_analysis = roi_analyzer.analyze_costs(api_calls_df, verify_df)

            # 成本概览
            st.markdown("##### 📊 成本概览")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总成本(CNY)", f"¥{cost_analysis['total_cost_cny']:.2f}")
            with col2:
                st.metric("总成本(USD)", f"${cost_analysis['total_cost_usd']:.2f}")
            with col3:
                st.metric("总Token数", f"{cost_analysis['total_tokens']:,}")
            with col4:
                st.metric("API调用次数", cost_analysis['total_calls'])

            # 成本趋势图
            if cost_analysis.get('daily_costs'):
                st.markdown("##### 📈 成本趋势")
                daily_df = pd.DataFrame(cost_analysis['daily_costs'])
                daily_df['date'] = pd.to_datetime(daily_df['date'])

                fig_cost_trend = px.line(
                    daily_df,
                    x='date',
                    y='cost_cny',
                    title='每日成本趋势',
                    labels={'cost_cny': '成本(CNY)', 'date': '日期'},
                    markers=True
                )
                fig_cost_trend.update_layout(hovermode='x unified')
                st.plotly_chart(fig_cost_trend, use_container_width=True)

            # 成本分布分析
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### 💼 按提供商统计")
                cost_by_provider = cost_analysis.get('cost_by_provider', {})
                if cost_by_provider:
                    provider_df = pd.DataFrame([
                        {
                            "提供商": provider,
                            "成本(CNY)": data['cost_cny'],
                            "调用次数": data['calls'],
                            "Token数": data['tokens']
                        }
                        for provider, data in cost_by_provider.items()
                    ])
                    provider_df = provider_df.sort_values("成本(CNY)", ascending=False)

                    fig_provider = px.pie(
                        provider_df,
                        values="成本(CNY)",
                        names="提供商",
                        title="成本分布（按提供商）"
                    )
                    st.plotly_chart(fig_provider, use_container_width=True)
                else:
                    st.info("暂无提供商数据")

            with col2:
                st.markdown("##### 🔧 按操作类型统计")
                cost_by_operation = cost_analysis.get('cost_by_operation', {})
                if cost_by_operation:
                    operation_df = pd.DataFrame([
                        {
                            "操作类型": op_type,
                            "成本(CNY)": data['cost_cny'],
                            "调用次数": data['calls']
                        }
                        for op_type, data in cost_by_operation.items()
                    ])
                    operation_df = operation_df.sort_values("成本(CNY)", ascending=False)

                    fig_operation = px.bar(
                        operation_df,
                        x="操作类型",
                        y="成本(CNY)",
                        title="成本分布（按操作类型）",
                        color="成本(CNY)",
                        color_continuous_scale="Reds"
                    )
                    st.plotly_chart(fig_operation, use_container_width=True)
                else:
                    st.info("暂无操作类型数据")

            # ROI 分析
            roi_analysis = cost_analysis.get('roi_analysis', {})
            if roi_analysis and roi_analysis.get('total_cost', 0) > 0:
                st.markdown("##### 📈 ROI 分析")
                roi_col1, roi_col2, roi_col3, roi_col4 = st.columns(4)
                with roi_col1:
                    st.metric("总投入成本", f"¥{roi_analysis.get('total_cost', 0):.2f}")
                with roi_col2:
                    st.metric("总提及次数", roi_analysis.get('total_mentions', 0))
                with roi_col3:
                    st.metric("估算价值", f"¥{roi_analysis.get('estimated_value', 0):.2f}")
                with roi_col4:
                    roi_ratio = roi_analysis.get('roi_ratio', 0)
                    st.metric("ROI", f"{roi_ratio:.1f}%", delta=f"¥{roi_analysis.get('roi_value', 0):.2f}")

                # 关键词 ROI 排名
                keyword_roi = roi_analysis.get('keyword_roi', {})
                if keyword_roi:
                    st.markdown("##### 🎯 关键词 ROI 排名")
                    keyword_roi_df = pd.DataFrame([
                        {
                            "关键词": kw,
                            "成本(CNY)": data['cost'],
                            "提及次数": data['mentions'],
                            "估算价值(CNY)": data['value'],
                            "ROI(%)": data['roi']
                        }
                        for kw, data in keyword_roi.items()
                    ])
                    keyword_roi_df = keyword_roi_df.sort_values("ROI(%)", ascending=False)

                    # 显示 Top 10
                    top_roi = keyword_roi_df.head(10)
                    st.dataframe(top_roi, use_container_width=True, hide_index=True)

                    with st.expander("查看完整关键词 ROI 排名", expanded=False):
                        st.dataframe(keyword_roi_df, use_container_width=True, hide_index=True)

            # 成本优化建议
            st.markdown("##### 💡 成本优化建议")
            suggestions = roi_analyzer.get_optimization_suggestions(cost_analysis)

            for suggestion in suggestions:
                priority_color = {
                    "高": "🔴",
                    "中": "🟡",
                    "低": "🟢"
                }.get(suggestion.get('priority', '低'), '⚪')

                with st.container(border=True):
                    st.markdown(f"**{priority_color} {suggestion.get('title', 'N/A')}**")
                    st.markdown(suggestion.get('description', ''))

                    if 'savings_estimate' in suggestion:
                        st.info(f"💵 预计可节省：¥{suggestion['savings_estimate']:.2f}")

                    if 'keywords' in suggestion:
                        st.markdown(f"**相关关键词**：{', '.join(suggestion['keywords'])}")

            # 未来成本预测
            st.markdown("##### 🔮 未来成本预测")
            future_cost = roi_analyzer.estimate_future_cost(api_calls_df, days=30)

            pred_col1, pred_col2, pred_col3 = st.columns(3)
            with pred_col1:
                st.metric("预计日均成本", f"¥{future_cost.get('estimated_daily_cost_cny', 0):.2f}")
            with pred_col2:
                st.metric("预计30天总成本", f"¥{future_cost.get('estimated_total_cost_cny', 0):.2f}")
            with pred_col3:
                confidence = future_cost.get('confidence', '低')
                confidence_icon = {"高": "🟢", "中": "🟡", "低": "🔴"}.get(confidence, "⚪")
                st.metric("预测置信度", f"{confidence_icon} {confidence}")

            if future_cost.get('data_points', 0) < 3:
                st.warning("⚠️ 数据点较少，预测准确性较低。建议积累更多数据后再查看预测。")

            # 导出成本数据
            st.markdown("##### 📥 导出数据")
            export_col1, export_col2 = st.columns(2)
            with export_col1:
                if not api_calls_df.empty:
                    api_calls_csv = api_calls_df.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        "下载 API 调用记录 CSV",
                        api_calls_csv,
                        f"{sanitize_filename(brand,40)}_api_calls.csv",
                        "text/csv",
                        use_container_width=True,
                        key="export_api_calls"
                    )
            with export_col2:
                # 生成成本报告
                cost_report = f"""
    # GEO 成本分析报告

    ## 成本概览
    - 总成本(CNY): ¥{cost_analysis['total_cost_cny']:.2f}
    - 总成本(USD): ${cost_analysis['total_cost_usd']:.2f}
    - 总Token数: {cost_analysis['total_tokens']:,}
    - API调用次数: {cost_analysis['total_calls']}

    ## ROI 分析
    """
                if roi_analysis:
                    cost_report += f"""
    - 总投入成本: ¥{roi_analysis.get('total_cost', 0):.2f}
    - 总提及次数: {roi_analysis.get('total_mentions', 0)}
    - 估算价值: ¥{roi_analysis.get('estimated_value', 0):.2f}
    - ROI: {roi_analysis.get('roi_ratio', 0):.1f}%
    """
                cost_report += f"""
    ## 优化建议
    """
                for suggestion in suggestions:
                    cost_report += f"""
    - [{suggestion.get('priority', '低')}] {suggestion.get('title', 'N/A')}
      {suggestion.get('description', '')}
    """

                st.download_button(
                    "下载成本分析报告",
                    cost_report,
                    f"{sanitize_filename(brand,40)}_cost_report.md",
                    "text/markdown",
                    use_container_width=True,
                    key="export_cost_report"
                )

        # 3. 内容质量指标分析
        st.markdown("#### 📈 内容质量指标分析")
        st.caption("分析内容的信任度、权威性、参与度等关键指标，量化内容质量")

        # 初始化指标分析器
        metrics_analyzer = ContentMetricsAnalyzer()

        # 获取历史文章
        try:
            articles = storage.get_articles(brand=brand)

            if articles and len(articles) > 0:
                # 分析所有文章
                with st.spinner("正在分析内容质量指标..."):
                    metrics_results = metrics_analyzer.analyze_batch(articles, brand)
                    summary = metrics_analyzer.get_metrics_summary(metrics_results)

                # 显示指标概览
                st.markdown("##### 📊 指标概览")
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    st.metric(
                        "平均 Trust Density",
                        f"{summary['avg_trust_density']:.2f}",
                        help="每100字信任信号数（来源占位、数据、案例等）"
                    )

                with metric_col2:
                    st.metric(
                        "平均 Citation Share",
                        f"{summary['avg_citation_share']:.2f}%",
                        help="品牌引用比例（品牌提及次数 / 总提及次数）"
                    )

                with metric_col3:
                    st.metric(
                        "平均 Authority Score",
                        f"{summary['avg_authority_score']:.2f}",
                        help="权威性得分（基于来源占位数量，0-100）"
                    )

                with metric_col4:
                    st.metric(
                        "平均 Engagement Potential",
                        f"{summary['avg_engagement_potential']:.2f}",
                        help="参与度潜力（基于结构化程度，0-100）"
                    )

                # 详细指标分析
                st.markdown("##### 📋 详细指标分析")

                # 创建指标数据框
                metrics_df = pd.DataFrame([
                    {
                        "关键词": r.get('keyword', ''),
                        "平台": r.get('platform', ''),
                        "Trust Density": r.get('trust_density', 0),
                        "Citation Share (%)": r.get('citation_share', 0),
                        "Authority Score": r.get('authority_score', 0),
                        "Engagement Potential": r.get('engagement_potential', 0),
                        "信任信号数": r.get('trust_signals', 0),
                        "来源占位": r.get('citations', 0),
                        "品牌提及": r.get('brand_mentions', 0),
                    }
                    for r in metrics_results
                ])

                if not metrics_df.empty:
                    # 显示指标表格
                    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

                    # 指标可视化
                    viz_col1, viz_col2 = st.columns(2)

                    with viz_col1:
                        # Trust Density 分布
                        fig_trust = px.histogram(
                            metrics_df,
                            x="Trust Density",
                            nbins=20,
                            title="Trust Density 分布",
                            labels={"Trust Density": "Trust Density", "count": "文章数量"},
                            color_discrete_sequence=["#2563EB"]
                        )
                        st.plotly_chart(fig_trust, use_container_width=True)

                    with viz_col2:
                        # Authority Score 分布
                        fig_authority = px.histogram(
                            metrics_df,
                            x="Authority Score",
                            nbins=20,
                            title="Authority Score 分布",
                            labels={"Authority Score": "Authority Score", "count": "文章数量"},
                            color_discrete_sequence=["#10B981"]
                        )
                        st.plotly_chart(fig_authority, use_container_width=True)

                    # 指标热力图（按平台）
                    if len(metrics_df['平台'].unique()) > 1:
                        st.markdown("##### 🔥 平台指标热力图")
                        platform_metrics = metrics_df.groupby('平台').agg({
                            'Trust Density': 'mean',
                            'Citation Share (%)': 'mean',
                            'Authority Score': 'mean',
                            'Engagement Potential': 'mean',
                        }).round(2)

                        fig_heatmap = px.imshow(
                            platform_metrics.T,
                            labels=dict(x="平台", y="指标", color="得分"),
                            title="各平台平均指标热力图",
                            color_continuous_scale="RdYlGn",
                            aspect="auto"
                        )
                        st.plotly_chart(fig_heatmap, use_container_width=True)

                    # 指标相关性分析
                    st.markdown("##### 🔗 指标相关性分析")
                    correlation_cols = ['Trust Density', 'Citation Share (%)', 'Authority Score', 'Engagement Potential']
                    corr_df = metrics_df[correlation_cols].corr()

                    fig_corr = px.imshow(
                        corr_df,
                        labels=dict(x="指标", y="指标", color="相关系数"),
                        title="指标相关性矩阵",
                        color_continuous_scale="RdBu",
                        aspect="auto",
                        text_auto=True
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)

                    # Top 内容排名
                    st.markdown("##### 🏆 Top 内容排名")
                    top_col1, top_col2, top_col3, top_col4 = st.columns(4)

                    with top_col1:
                        top_trust = metrics_df.nlargest(5, 'Trust Density')[['关键词', '平台', 'Trust Density']]
                        st.markdown("**Top 5 Trust Density**")
                        st.dataframe(top_trust, use_container_width=True, hide_index=True)

                    with top_col2:
                        top_citation = metrics_df.nlargest(5, 'Citation Share (%)')[['关键词', '平台', 'Citation Share (%)']]
                        st.markdown("**Top 5 Citation Share**")
                        st.dataframe(top_citation, use_container_width=True, hide_index=True)

                    with top_col3:
                        top_authority = metrics_df.nlargest(5, 'Authority Score')[['关键词', '平台', 'Authority Score']]
                        st.markdown("**Top 5 Authority Score**")
                        st.dataframe(top_authority, use_container_width=True, hide_index=True)

                    with top_col4:
                        top_engagement = metrics_df.nlargest(5, 'Engagement Potential')[['关键词', '平台', 'Engagement Potential']]
                        st.markdown("**Top 5 Engagement Potential**")
                        st.dataframe(top_engagement, use_container_width=True, hide_index=True)

                    # 导出指标数据
                    st.markdown("##### 📥 导出指标数据")
                    metrics_csv = metrics_df.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        "下载指标数据 CSV",
                        metrics_csv,
                        f"{sanitize_filename(brand,40)}_内容质量指标_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="export_metrics_csv"
                    )
                else:
                    st.info("暂无指标数据。")
            else:
                st.info("💡 提示：请先在【2 自动创作】生成内容，然后才能查看内容质量指标。")
        except Exception as e:
            st.error(f"获取内容质量指标失败：{e}")

        # 4. 关键词效果排名
        st.markdown("#### 🎯 关键词效果排名")

        brand_verify = verify_df[verify_df["品牌"] == brand].copy()
        if len(brand_verify) > 0:
            keyword_performance = brand_verify.groupby("问题")["提及次数"].agg(["mean", "count"]).reset_index()
            keyword_performance.columns = ["关键词", "平均提及次数", "验证次数"]
            keyword_performance = keyword_performance.sort_values("平均提及次数", ascending=False)

            # 显示 Top 20
            top_keywords = keyword_performance.head(20)

            fig_keywords = px.bar(
                top_keywords,
                x="平均提及次数",
                y="关键词",
                orientation='h',
                title="Top 20 关键词效果排名（平均提及次数）",
                labels={"平均提及次数": "平均提及次数", "关键词": "关键词"},
                color="平均提及次数",
                color_continuous_scale="Greens"
            )
            fig_keywords.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_keywords, use_container_width=True)

            with st.expander("查看完整关键词排名", expanded=False):
                st.dataframe(keyword_performance, use_container_width=True, hide_index=True)
        else:
            st.info("暂无品牌验证数据。")

        # 4. 竞品对比分析
        st.markdown("#### ⚔️ 竞品对比分析")

        if len(competitor_list) > 0:
            # 计算各品牌的平均提及次数
            brand_comparison = verify_df.groupby("品牌")["提及次数"].agg(["mean", "count"]).reset_index()
            brand_comparison.columns = ["品牌", "平均提及次数", "验证次数"]
            brand_comparison = brand_comparison.sort_values("平均提及次数", ascending=False)

            fig_comparison = px.bar(
                brand_comparison,
                x="品牌",
                y="平均提及次数",
                title="品牌提及率对比（平均提及次数）",
                labels={"平均提及次数": "平均提及次数", "品牌": "品牌"},
                color="平均提及次数",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig_comparison, use_container_width=True)

            # 详细对比表
            with st.expander("查看详细对比数据", expanded=False):
                st.dataframe(brand_comparison, use_container_width=True, hide_index=True)

            # 按验证模型分组的对比
            if "验证模型" in verify_df.columns:
                model_comparison = verify_df.groupby(["品牌", "验证模型"])["提及次数"].mean().reset_index()
                model_comparison = model_comparison.pivot(index="品牌", columns="验证模型", values="提及次数").fillna(0)

                fig_model_comparison = px.bar(
                    model_comparison.reset_index(),
                    x="品牌",
                    y=[col for col in model_comparison.columns],
                    title="各模型下的品牌提及率对比",
                    labels={"value": "平均提及次数", "品牌": "品牌"},
                    barmode='group'
                )
                st.plotly_chart(fig_model_comparison, use_container_width=True)
        else:
            st.info("💡 提示：在侧边栏配置竞品品牌后，可查看竞品对比分析。")

        # 5. 负面防护监控报告
        st.markdown("#### 🛡️ 负面防护监控报告")
        st.caption("分析负面查询中的品牌提及情况，提供风险预警和优化建议")

        # 获取负面分析结果（从 session_state 或数据库）
        try:
            # 尝试从 session_state 获取
            negative_results = st.session_state.get("negative_analysis_results", [])

            # 如果没有，尝试从验证结果中提取负面查询
            if not negative_results and st.session_state.verify_combined is not None:
                verify_df = st.session_state.verify_combined
                # 检查是否有负面查询
                negative_monitor = NegativeMonitor()
                negative_queries_pattern = "|".join([q.replace(brand, "{brand}") for q in negative_monitor.generate_negative_queries(brand, 15)])

                # 筛选可能的负面查询
                brand_verify = verify_df[verify_df["品牌"] == brand].copy()
                if len(brand_verify) > 0:
                    # 检查问题是否包含负面关键词
                    negative_keywords = negative_monitor.negative_keywords
                    negative_verify = brand_verify[
                        brand_verify["问题"].str.contains("|".join(negative_keywords), case=False, na=False)
                    ]

                    if len(negative_verify) > 0:
                        # 重新分析负面查询
                        negative_results = []
                        for _, row in negative_verify.iterrows():
                            # 这里需要重新获取响应内容，但为了简化，我们使用现有数据
                            # 实际应用中，应该从数据库获取完整的响应内容
                            try:
                                analysis = negative_monitor.analyze_negative_mentions(
                                    brand=brand,
                                    query=row["问题"],
                                    response="",  # 如果没有保存响应，使用空字符串
                                    mention_count=row["提及次数"]
                                )
                                negative_results.append(analysis)
                            except Exception:
                                pass

            if negative_results:
                negative_monitor = NegativeMonitor()
                report = negative_monitor.generate_negative_report(
                    brand=brand,
                    analysis_results=negative_results,
                    threshold=0.3
                )

                # 显示报告概览
                st.markdown("##### 📊 报告概览")
                report_col1, report_col2, report_col3, report_col4 = st.columns(4)

                with report_col1:
                    st.metric("总查询数", report.get("total_queries", 0))

                with report_col2:
                    st.metric("高风险", report.get("high_risk_count", 0), delta=None, delta_color="inverse")

                with report_col3:
                    st.metric("平均提及次数", report.get("average_mention_count", 0.0))

                with report_col4:
                    st.metric("平均负面得分", report.get("average_negative_score", 0.0))

                # 预警信息
                alerts = report.get("alerts", [])
                if alerts:
                    st.markdown("##### ⚠️ 预警信息")
                    for alert in alerts:
                        alert_level = alert.get("level", "中")
                        alert_color = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(alert_level, "⚪")
                        st.warning(f"{alert_color} {alert.get('message', '')}")

                # 优化建议
                recommendations = report.get("recommendations", [])
                if recommendations:
                    st.markdown("##### 💡 优化建议")
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"{i}. {rec}")

                # 高风险查询列表
                high_risk_queries = report.get("high_risk_queries", [])
                if high_risk_queries:
                    st.markdown("##### 🔴 高风险查询列表")
                    st.write(", ".join(high_risk_queries))

                # 中风险查询列表
                medium_risk_queries = report.get("medium_risk_queries", [])
                if medium_risk_queries:
                    st.markdown("##### 🟡 中风险查询列表")
                    st.write(", ".join(medium_risk_queries))

                # 下载报告
                import json
                report_json = json.dumps(report, ensure_ascii=False, indent=2)
                st.download_button(
                    "下载负面监控报告 JSON",
                    report_json,
                    f"{sanitize_filename(brand,40)}_负面监控报告_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="negative_report_dl"
                )
            else:
                st.info("💡 提示：暂无负面监控数据。请在【4 多模型验证】中启用负面监控功能，生成负面查询并验证。")
        except Exception as e:
            st.error(f"生成负面监控报告失败：{e}")

        # 6. 数据导出
        st.markdown("#### 💾 数据导出")

        col1, col2 = st.columns(2)
        with col1:
            # 导出验证数据
            csv_data = verify_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "下载验证数据 CSV",
                csv_data,
                f"{sanitize_filename(brand,40)}_AI数据报表_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="report_dl_csv"
            )

        with col2:
            # 导出关键词效果排名
            if len(brand_verify) > 0:
                keyword_csv = keyword_performance.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    "下载关键词排名 CSV",
                    keyword_csv,
                    f"{sanitize_filename(brand,40)}_关键词排名_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="keyword_rank_dl_csv"
                )

    # =======================
    # Tab7：工作流自动化
