# Tab9：平台同步（从 geo_tool.py 迁移，通过 render_tab_platform_sync() 供主入口调用。）

import pandas as pd
import streamlit as st


def render_tab_platform_sync(storage, brand: str) -> None:
    """渲染 Tab9：平台同步。由主入口在 with tab9 内调用。"""
    st.markdown("### 📤 平台文章同步")
    st.caption("将生成的文章自动发布到各平台，支持API发布和一键复制")

    # 品牌信息：优先使用主入口传入的 brand（来自侧边栏 cfg），与其它 Tab 一致
    brand_to_use = (st.session_state.get("brand") or brand or "").strip()
    if not brand_to_use:
        st.info("请先在侧边栏设置品牌信息")
    else:
        # 平台账号配置
        st.markdown("---")
        st.markdown("#### 🔐 平台账号配置")

        platform_config_tabs = st.tabs(["GitHub", "其他平台（开发中）"])

        with platform_config_tabs[0]:
            st.markdown("##### GitHub 配置")
            st.caption("配置GitHub账号信息，用于自动发布文章到GitHub仓库")

            # 检查是否已有配置
            existing_config = storage.get_platform_account("GitHub", brand_to_use)

            github_api_key = st.text_input(
                "GitHub Personal Access Token",
                value=existing_config.get('api_key', '') if existing_config else '',
                type="password",
                help="在 https://github.com/settings/tokens 创建Token，需要 repo 权限",
                key="github_api_key"
            )

            github_repo_owner = st.text_input(
                "仓库所有者（用户名）",
                value=existing_config.get('config', {}).get('repo_owner', '') if existing_config else '',
                help="GitHub用户名或组织名",
                key="github_repo_owner"
            )

            github_repo_name = st.text_input(
                "仓库名称",
                value=existing_config.get('config', {}).get('repo_name', '') if existing_config else '',
                help="要发布到的仓库名称",
                key="github_repo_name"
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 保存配置", type="primary", use_container_width=True):
                    if github_api_key and github_repo_owner and github_repo_name:
                        try:
                            # 验证账号
                            from platform_sync.github_publisher import GitHubPublisher
                            publisher = GitHubPublisher(github_api_key, github_repo_owner, github_repo_name)
                            if publisher.validate_account():
                                storage.save_platform_account(
                                    platform="GitHub",
                                    account_config={
                                        'account_type': 'api',
                                        'api_key': github_api_key,
                                        'config': {
                                            'repo_owner': github_repo_owner,
                                            'repo_name': github_repo_name
                                        }
                                    },
                                    brand=brand_to_use
                                )
                                st.success("✅ GitHub配置已保存并验证成功！")
                            else:
                                st.error("❌ GitHub Token验证失败，请检查Token是否正确")
                        except Exception as e:
                            st.error(f"❌ 配置保存失败: {str(e)}")
                    else:
                        st.error("请填写完整信息")

            with col2:
                if existing_config:
                    st.info("✅ 已配置GitHub账号")

        # 发布功能
        st.markdown("---")
        st.markdown("#### 📝 发布文章")

        # 选择文章
        articles = storage.get_articles(brand=brand_to_use)
        if articles:
            # 文章选择
            article_options = {}
            for article in articles:
                display_name = f"{article.get('keyword', 'N/A')} - {article.get('platform', 'N/A')}"
                article_options[display_name] = article.get('id')

            if article_options:
                selected_article_key = st.selectbox(
                    "选择要发布的文章",
                    list(article_options.keys()),
                    key="publish_article_select"
                )
                selected_article_id = article_options[selected_article_key]

                # 选择平台
                # 定义平台列表
                api_platforms = ["GitHub"]
                copy_platforms = [
                    "头条号（资讯软文）", "小红书（生活种草）", "抖音图文（短内容）", "简书（文艺）",
                    "QQ空间（社交）", "新浪博客（博客）", "新浪新闻（资讯）", "搜狐号（资讯）",
                    "一点号（资讯）", "东方财富（财经）", "邦阅网（外贸）", "原创力文档（文档）"
                ]
                all_publish_platforms = api_platforms + copy_platforms

                publish_platform = st.selectbox(
                    "选择发布平台",
                    all_publish_platforms,
                    key="publish_platform_select"
                )

                if publish_platform == "GitHub":
                    # 检查配置
                    account_config = storage.get_platform_account("GitHub", brand_to_use)
                    if not account_config:
                        st.warning("⚠️ 请先配置GitHub账号")
                    else:
                        # 获取文章
                        article = next((a for a in articles if a.get('id') == selected_article_id), None)
                        if article:
                            # 显示文章预览
                            with st.expander("📄 文章预览", expanded=False):
                                st.markdown(f"**关键词**: {article.get('keyword', 'N/A')}")
                                st.markdown(f"**平台**: {article.get('platform', 'N/A')}")
                                st.markdown(f"**内容长度**: {len(article.get('content', ''))} 字符")
                                st.markdown("---")
                                st.text_area("内容", article.get('content', ''), height=200, disabled=True)

                            # 发布选项
                            file_path = st.text_input(
                                "文件路径（可选）",
                                value=f"content/{article.get('keyword', 'article').replace(' ', '_')[:50]}.md",
                                help="GitHub仓库中的文件路径，留空使用默认路径",
                                key="github_file_path"
                            )

                            if st.button("🚀 发布到GitHub", type="primary", use_container_width=True):
                                try:
                                    from platform_sync.github_publisher import GitHubPublisher
                                    publisher = GitHubPublisher(
                                        api_key=account_config['api_key'],
                                        repo_owner=account_config['config']['repo_owner'],
                                        repo_name=account_config['config']['repo_name']
                                    )

                                    with st.spinner("正在发布到GitHub..."):
                                        result = publisher.publish(
                                            content=article.get('content', ''),
                                            title=article.get('keyword', 'Untitled'),
                                            file_path=file_path if file_path else None
                                        )

                                    # 保存发布记录
                                    storage.save_publish_record(
                                        article_id=selected_article_id,
                                        platform="GitHub",
                                        publish_method="api",
                                        publish_status="success" if result['success'] else "failed",
                                        publish_url=result.get('publish_url', ''),
                                        publish_id=result.get('publish_id', ''),
                                        error_message=result.get('error', '')
                                    )

                                    # 显示结果
                                    if result['success']:
                                        st.success(f"✅ 发布成功！")
                                        st.markdown(f"**发布链接**: [{result['publish_url']}]({result['publish_url']})")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ 发布失败: {result.get('error', '未知错误')}")
                                except Exception as e:
                                    st.error(f"❌ 发布过程出错: {str(e)}")
                                    storage.save_publish_record(
                                        article_id=selected_article_id,
                                        platform="GitHub",
                                        publish_method="api",
                                        publish_status="failed",
                                        error_message=str(e)
                                    )
                else:
                    # 一键复制平台
                    article = next((a for a in articles if a.get('id') == selected_article_id), None)
                    if article:
                        from platform_sync.copy_manager import CopyManager
                        copy_manager = CopyManager()

                        # 格式化内容
                        formatted_content = copy_manager.format_for_platform(
                            platform=publish_platform,
                            content=article.get('content', ''),
                            title=article.get('keyword', 'Untitled'),
                            keyword=article.get('keyword', ''),
                            brand=brand_to_use
                        )

                        # 显示格式化后的内容
                        with st.expander("📄 格式化后的内容（已复制到剪贴板）", expanded=True):
                            st.text_area(
                                "内容",
                                formatted_content,
                                height=300,
                                key="formatted_content_display"
                            )

                        # 发布指南
                        guide = copy_manager.generate_publish_guide(publish_platform)
                        with st.expander("📋 发布指南", expanded=True):
                            st.markdown(guide)

                        # 复制按钮
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("📋 复制到剪贴板", type="primary", use_container_width=True):
                                if copy_manager.copy_to_clipboard(formatted_content):
                                    st.success("✅ 内容已复制到剪贴板！")
                                    st.info("💡 请按照上方发布指南，将内容粘贴到对应平台发布")

                                    # 保存发布记录（标记为已复制）
                                    storage.save_publish_record(
                                        article_id=selected_article_id,
                                        platform=publish_platform,
                                        publish_method="copy",
                                        publish_status="copied",
                                        error_message=""
                                    )
                                else:
                                    st.error("❌ 复制失败，请手动复制内容")

                        with col2:
                            if st.button("📥 下载内容", use_container_width=True):
                                # 生成下载文件
                                safe_title = article.get('keyword', 'article').replace(' ', '_')[:50]
                                filename = f"{publish_platform.replace('（', '_').replace('）', '')}_{safe_title}.txt"
                                st.download_button(
                                    label="⬇️ 下载",
                                    data=formatted_content,
                                    file_name=filename,
                                    mime="text/plain",
                                    key="download_formatted_content"
                                )
        else:
            st.info("📝 请先在【2 自动创作】中生成文章")

        # 发布记录
        st.markdown("---")
        st.markdown("#### 📊 发布记录")

        publish_records = storage.get_publish_records(brand=brand_to_use)
        if publish_records:
            # 统计信息
            total_records = len(publish_records)
            success_records = len([r for r in publish_records if r.get('publish_status') == 'success'])
            copied_records = len([r for r in publish_records if r.get('publish_status') == 'copied'])
            failed_records = len([r for r in publish_records if r.get('publish_status') == 'failed'])

            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            with stat_col1:
                st.metric("总发布数", total_records)
            with stat_col2:
                st.metric("API成功", success_records, delta=f"{success_records/total_records*100:.1f}%" if total_records > 0 else "0%")
            with stat_col3:
                st.metric("已复制", copied_records, delta=f"{copied_records/total_records*100:.1f}%" if total_records > 0 else "0%")
            with stat_col4:
                st.metric("失败", failed_records)

            # 记录列表
            st.markdown("##### 最近发布记录")
            records_df = pd.DataFrame(publish_records[:20])  # 显示最近20条
            if not records_df.empty:
                # 格式化显示
                display_df = records_df[['platform', 'publish_method', 'publish_status', 'publish_url', 'published_at', 'created_at']].copy()
                display_df.columns = ['平台', '发布方式', '状态', '链接', '发布时间', '创建时间']
                display_df['状态'] = display_df['状态'].map({
                    'success': '✅ 成功',
                    'failed': '❌ 失败',
                    'pending': '⏳ 待发布',
                    'copied': '📋 已复制'
                })
                display_df['发布方式'] = display_df['发布方式'].map({
                    'api': 'API',
                    'copy': '一键复制'
                })

                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无发布记录")

    # =======================
