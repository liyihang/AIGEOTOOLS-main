# Tab8：GEO 资源库（从 geo_tool.py 迁移，通过 render_tab_resources() 供主入口调用。）

import streamlit as st

from modules.resource_recommender import ResourceRecommender
from modules.ui.components import render_tab_top_with_clear


def render_tab_resources(storage, brand: str) -> None:
    """渲染 Tab8：GEO 资源库。由主入口在 with tab8 内调用。"""
    render_tab_top_with_clear(
        title="📚 GEO 资源库",
        caption="发现 GEO 相关工具、代理、论文和社区资源，增强工具生态",
        clear_key="resources_clear",
        on_clear=lambda: None,  # 资源库无需清空
    )

    resource_recommender = ResourceRecommender()

    # 资源统计概览
    summary = resource_recommender.get_resource_summary()
    stat_cols = st.columns(5)
    stats = [
        ("总资源数", summary['total']),
        ("AI 搜索", summary['agents']),
        ("工具推荐", summary['tools']),
        ("论文指南", summary['papers']),
        ("社区资源", summary['communities']),
    ]
    for col, (label, value) in zip(stat_cols, stats):
        with col:
            st.metric(label, value)

    # 搜索功能
    search_col1, search_col2 = st.columns([4, 1])
    with search_col1:
        search_query = st.text_input(
            "搜索资源", 
            key="resource_search", 
            placeholder="🔍 输入关键词搜索资源名称、描述、功能特性...",
            label_visibility="collapsed"
        )
    def _clear_resource_search() -> None:
        st.session_state.resource_search = ""

    with search_col2:
        if st.button(
            "清除",
            use_container_width=True,
            key="clear_resource_search",
            on_click=_clear_resource_search,
        ):
            st.rerun()

    # 资源分类标签
    resource_tab1, resource_tab2, resource_tab3, resource_tab4 = st.tabs([
        "🤖 AI 搜索", "🛠️ 工具推荐", "📄 论文指南", "👥 社区资源"
    ])

    # AI 搜索/代理
    with resource_tab1:
        st.caption("AI 搜索引擎和内容生成服务，用于验证和优化 GEO 效果")

        if search_query:
            agents = resource_recommender.search_resources(search_query, "agents")
        else:
            agents = resource_recommender.get_agents()

        if agents:
            for agent in agents:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{agent['name']}** {agent.get('rating', '')}")
                    with col2:
                        if agent.get('url'):
                            st.link_button("访问", agent['url'], use_container_width=True)

                    st.caption(agent['description'])

                    if agent.get('features'):
                        features_text = " · ".join([f"✓ {f}" for f in agent['features']])
                        st.markdown(f"<small>{features_text}</small>", unsafe_allow_html=True)
        else:
            st.info("💡 暂无匹配的资源，尝试其他关键词搜索。")

    # 工具推荐
    with resource_tab2:
        st.caption("GEO 相关的工具和服务，帮助优化内容效果")

        if search_query:
            tools = resource_recommender.search_resources(search_query, "tools")
        else:
            tools = resource_recommender.get_tools()

        if tools:
            # 按分类分组显示
            categories = {}
            for tool in tools:
                cat = tool.get('category', '其他')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(tool)

            for category, category_tools in categories.items():
                st.markdown(f"**{category}**")
                for tool in category_tools:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{tool['name']}** {tool.get('rating', '')}")
                        with col2:
                            if tool.get('url'):
                                st.link_button("访问", tool['url'], use_container_width=True)

                        st.caption(tool['description'])

                        if tool.get('features'):
                            features_text = " · ".join([f"✓ {f}" for f in tool['features']])
                            st.markdown(f"<small>{features_text}</small>", unsafe_allow_html=True)
        else:
            st.info("💡 暂无匹配的工具，尝试其他关键词搜索。")

    # 论文/指南
    with resource_tab3:
        st.caption("GEO 相关的论文、指南、文档，深入学习 GEO 策略")

        if search_query:
            papers = resource_recommender.search_resources(search_query, "papers")
        else:
            papers = resource_recommender.get_papers()

        if papers:
            # 按重要性分组显示
            importance_order = {"高": 3, "中": 2, "低": 1}
            papers_sorted = sorted(papers, key=lambda x: importance_order.get(x.get('importance', '低'), 1), reverse=True)

            importance_groups = {
                "🔥 必读": [p for p in papers_sorted if p.get('importance') == '高'],
                "⭐ 推荐": [p for p in papers_sorted if p.get('importance') == '中'],
            }

            for group_name, group_papers in importance_groups.items():
                if group_papers:
                    st.markdown(f"**{group_name}**")
                    for paper in group_papers:
                        with st.container(border=True):
                            st.markdown(f"**{paper['title']}**")
                            st.caption(paper['description'])
                            meta = f"分类：{paper.get('category', 'N/A')} · 日期：{paper.get('date', 'N/A')}"
                            st.markdown(f"<small>{meta}</small>", unsafe_allow_html=True)
                            if paper.get('url'):
                                st.link_button("查看", paper['url'], use_container_width=True)
        else:
            st.info("💡 暂无匹配的论文/指南，尝试其他关键词搜索。")

    # 社区资源
    with resource_tab4:
        st.caption("GEO 相关的社区和论坛，与其他用户交流经验")

        if search_query:
            communities = resource_recommender.search_resources(search_query, "communities")
        else:
            communities = resource_recommender.get_communities()

        if communities:
            for community in communities:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{community['name']}** {community.get('rating', '')}")
                    with col2:
                        if community.get('url'):
                            st.link_button("访问", community['url'], use_container_width=True)

                    st.caption(community['description'])
                    st.markdown(f"<small>分类：{community.get('category', 'N/A')}</small>", unsafe_allow_html=True)
        else:
            st.info("💡 暂无匹配的社区资源，尝试其他关键词搜索。")
