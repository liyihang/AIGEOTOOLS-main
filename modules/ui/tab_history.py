# Tab5：历史记录（从 geo_tool.py 迁移，通过 render_tab_history() 供主入口调用。）

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_history(storage, brand: str) -> None:
    """渲染 Tab5：历史记录。由主入口在 with tab5 内调用。"""
    st.header("历史记录")

    # 统计数据
    try:
        stats = storage.get_stats(brand)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("关键词总数", stats["keywords_count"])
        col2.metric("文章总数", stats["articles_count"])
        col3.metric("优化记录", stats["optimizations_count"])
        col4.metric("验证结果", stats["verify_results_count"])
    except Exception as e:
        st.error(f"获取统计数据失败：{e}")
        stats = {"keywords_count": 0, "articles_count": 0, "optimizations_count": 0, "verify_results_count": 0}

    st.markdown("---")

    # 历史文章列表
    st.markdown("#### 历史文章")
    try:
        articles = storage.get_articles(brand=brand)
        if articles:
            articles_df = pd.DataFrame(articles)
            # 只显示关键列
            display_cols = ["keyword", "platform", "created_at"]
            available_cols = [col for col in display_cols if col in articles_df.columns]
            if available_cols:
                st.dataframe(articles_df[available_cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(articles_df, use_container_width=True, hide_index=True)

            # 文章详情查看
            if len(articles) > 0:
                selected_idx = st.selectbox("选择文章查看详情", range(len(articles)), format_func=lambda x: f"{articles[x].get('keyword', 'N/A')} - {articles[x].get('platform', 'N/A')}")
                if selected_idx is not None:
                    selected_article = articles[selected_idx]
                    with st.expander("文章内容", expanded=True):
                        if selected_article.get("content"):
                            if selected_article.get("platform", "").startswith("GitHub"):
                                st.code(selected_article["content"], language="markdown")
                            else:
                                st.text_area("内容", selected_article["content"], height=400, disabled=True, key=f"article_content_{selected_idx}")
        else:
            st.info("暂无历史文章记录。")
    except Exception as e:
        st.error(f"获取历史文章失败：{e}")

    st.markdown("---")

    # 历史优化记录
    st.markdown("#### 历史优化记录")
    try:
        optimizations = storage.get_optimizations(brand=brand)
        if optimizations:
            opt_df = pd.DataFrame(optimizations)
            display_cols = ["platform", "created_at"]
            available_cols = [col for col in display_cols if col in opt_df.columns]
            if available_cols:
                st.dataframe(opt_df[available_cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(opt_df.head(10), use_container_width=True, hide_index=True)

            if len(optimizations) > 0:
                selected_opt_idx = st.selectbox("选择优化记录查看详情", range(len(optimizations)), format_func=lambda x: f"{optimizations[x].get('platform', 'N/A')} - {optimizations[x].get('created_at', 'N/A')[:10] if optimizations[x].get('created_at') else 'N/A'}")
                if selected_opt_idx is not None:
                    selected_opt = optimizations[selected_opt_idx]
                    with st.expander("优化详情", expanded=True):
                        if selected_opt.get("changes"):
                            st.markdown("**变更说明**")
                            st.markdown(selected_opt["changes"])
                        if selected_opt.get("optimized_content"):
                            st.markdown("**优化后内容**")
                            if "GitHub" in selected_opt.get("platform", ""):
                                st.code(selected_opt["optimized_content"], language="markdown")
                            else:
                                st.text_area("内容", selected_opt["optimized_content"], height=300, disabled=True, key=f"opt_content_{selected_opt_idx}")
        else:
            st.info("暂无优化记录。")
    except Exception as e:
        st.error(f"获取优化记录失败：{e}")

    st.markdown("---")

    # 历史验证结果
    st.markdown("#### 历史验证结果")
    try:
        verify_df = storage.get_verify_results(brand=brand)
        if not verify_df.empty:
            st.dataframe(verify_df, use_container_width=True, hide_index=True)

            # 可视化历史验证结果
            if len(verify_df) > 0:
                st.markdown("#### 历史验证结果可视化")
                fig = px.bar(
                    verify_df,
                    x="问题",
                    y="提及次数",
                    color="品牌",
                    facet_col="验证模型",
                    barmode="group",
                    title="历史验证结果对比",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无验证结果记录。")
    except Exception as e:
        st.error(f"获取验证结果失败：{e}")
