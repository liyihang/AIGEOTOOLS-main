"""
知识库管理 Tab
支持上传文档、查看文档列表、搜索测试
"""

import streamlit as st
from modules.knowledge_base import KnowledgeBase, SourceVerifier


def render_tab_knowledge(kb: KnowledgeBase):
    """
    渲染知识库管理 Tab
    
    Args:
        kb: 知识库实例
    """
    st.markdown("### 📚 品牌知识库")
    st.caption("上传品牌文档、产品手册、案例库，AI 生成内容时将自动检索引用")
    
    # 统计信息
    stats = kb.get_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 文档数量", stats["total_documents"])
    with col2:
        st.metric("📦 分块数量", stats["total_chunks"])
    with col3:
        doc_types = stats.get("document_types", {})
        st.metric("📋 文档类型", len(doc_types))
    
    # 主要功能区域
    kb_tab1, kb_tab2, kb_tab3, kb_tab4 = st.tabs([
        "📤 上传文档", "📋 文档列表", "🔍 搜索测试", "📊 来源验证"
    ])
    
    with kb_tab1:
        _render_upload_section(kb)
    
    with kb_tab2:
        _render_document_list(kb)
    
    with kb_tab3:
        _render_search_test(kb)
    
    with kb_tab4:
        _render_source_verifier()


def _render_upload_section(kb: KnowledgeBase):
    """渲染上传文档区域"""
    st.markdown("#### 上传新文档")
    
    # 文档类型选择
    doc_type = st.selectbox(
        "文档类型",
        ["text", "faq", "product", "case", "markdown"],
        format_func=lambda x: {
            "text": "📝 通用文本",
            "faq": "❓ FAQ 问答",
            "product": "📦 产品文档",
            "case": "💼 客户案例",
            "markdown": "📑 Markdown 文档"
        }.get(x, x),
        help="选择文档类型有助于更精准的分块和检索"
    )
    
    # 上传方式选择
    upload_method = st.radio(
        "上传方式",
        ["📁 上传文件", "📝 粘贴文本"],
        horizontal=True
    )
    
    if upload_method == "📁 上传文件":
        uploaded_file = st.file_uploader(
            "选择文件",
            type=["txt", "md", "csv"],
            help="支持 TXT、Markdown、CSV 格式"
        )
        
        if uploaded_file:
            # 安全解码文件内容
            b = uploaded_file.read()
            content = None
            for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
                try:
                    content = b.decode(enc)
                    break
                except Exception:
                    pass
            if content is None:
                content = b.decode("utf-8", errors="replace")
            
            st.text_area("文件预览", content[:1000] + "..." if len(content) > 1000 else content, 
                        height=150, disabled=True)
            
            if st.button("📥 导入知识库", use_container_width=True, type="primary"):
                with st.spinner("正在处理文档..."):
                    result = kb.add_document(
                        filename=uploaded_file.name,
                        content=content,
                        doc_type=doc_type
                    )
                    st.success(f"✅ 文档 '{result['filename']}' 已导入，分为 {result['chunk_count']} 个分块")
                    st.rerun()
    else:
        filename = st.text_input("文档名称", placeholder="例如：产品功能说明")
        content = st.text_area("粘贴文档内容", height=300, 
                              placeholder="粘贴品牌介绍、产品说明、FAQ 等内容...")
        
        if st.button("📥 导入知识库", use_container_width=True, type="primary"):
            if not filename:
                st.warning("请输入文档名称")
            elif not content.strip():
                st.warning("请输入文档内容")
            else:
                with st.spinner("正在处理文档..."):
                    result = kb.add_document(
                        filename=filename,
                        content=content,
                        doc_type=doc_type
                    )
                    st.success(f"✅ 文档 '{result['filename']}' 已导入，分为 {result['chunk_count']} 个分块")
                    st.rerun()
    
    # 批量导入示例
    with st.expander("💡 快速导入示例数据"):
        st.markdown("""
        **FAQ 示例格式：**
        ```
        Q：你们的产品有什么优势？
        A：我们的产品具有以下核心优势：1）AI深度赋能...；2）全流程覆盖...；3）数据驱动决策...
        
        Q：如何开始使用？
        A：只需三步：1）注册账号；2）配置基础信息；3）开始使用核心功能。
        ```
        
        **产品文档示例格式：**
        ```
        # 产品概述
        产品简介...
        
        # 核心功能
        功能说明...
        
        # 技术架构
        架构说明...
        ```
        """)


def _render_document_list(kb: KnowledgeBase):
    """渲染文档列表区域"""
    st.markdown("#### 已导入文档")
    
    documents = kb.list_documents()
    
    if not documents:
        st.info("📭 知识库为空，请先上传文档")
        return
    
    for doc in documents:
        with st.expander(f"📄 {doc['filename']} ({doc['doc_type']})"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**类型：** {doc['doc_type']}")
            with col2:
                st.write(f"**分块数：** {doc['chunk_count']}")
            with col3:
                st.write(f"**导入时间：** {doc['created_at'][:10]}")
            
            if st.button(f"🗑️ 删除", key=f"delete_{doc['doc_id']}"):
                kb.delete_document(doc['doc_id'])
                st.success(f"已删除文档 '{doc['filename']}'")
                st.rerun()


def _render_search_test(kb: KnowledgeBase):
    """渲染搜索测试区域"""
    st.markdown("#### 搜索测试")
    st.caption("测试知识库检索效果，验证文档是否被正确索引")
    
    query = st.text_input("输入测试查询", placeholder="🔍 例如：产品有什么优势？", label_visibility="collapsed")
    
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("返回结果数", 1, 10, 3)
    with col2:
        doc_type_filter = st.selectbox(
            "过滤文档类型",
            ["全部"] + ["text", "faq", "product", "case", "markdown"],
            index=0
        )
    
    if query:
        doc_type = None if doc_type_filter == "全部" else doc_type_filter
        results = kb.search(query, top_k=top_k, doc_type=doc_type)
        
        if results:
            st.markdown(f"**找到 {len(results)} 条相关结果：**")
            for i, result in enumerate(results, 1):
                with st.expander(f"结果 {i} (相关度: {result['score']:.2f})"):
                    st.markdown(f"**来源：** {result['metadata'].get('filename', '未知')}")
                    st.markdown(f"**类型：** {result['metadata'].get('type', '未知')}")
                    st.text_area("内容", result['content'], height=150, 
                               key=f"result_{i}", disabled=True)
        else:
            st.warning("未找到相关结果，请尝试其他查询或添加更多文档")


def _render_source_verifier():
    """渲染来源验证区域"""
    st.markdown("#### 📊 来源质量验证")
    st.caption("检查内容中的来源声明是否真实可信")
    
    verifier = SourceVerifier()
    
    content = st.text_area(
        "粘贴待验证内容",
        height=200,
        placeholder="粘贴 AI 生成的内容，检查其中的来源引用是否真实..."
    )
    
    if st.button("🔍 开始验证", use_container_width=True, type="primary"):
        if not content.strip():
            st.warning("请输入待验证内容")
        else:
            with st.spinner("正在分析来源质量..."):
                result = verifier.assess_source_quality(content)
            
            # 显示结果
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📝 来源声明数", result["claim_count"])
            with col2:
                if result["has_sources"]:
                    st.metric("✅ 具体来源", result.get("specific_count", 0))
                else:
                    st.metric("✅ 具体来源", 0)
            with col3:
                st.metric("📊 质量评分", f"{result['quality_score']:.0f}/100")
            
            # 详细建议
            if result["suggestions"]:
                st.markdown("**💡 改进建议：**")
                for suggestion in result["suggestions"]:
                    st.markdown(f"- {suggestion}")
            
            # 显示检测到的来源声明
            if result.get("claims"):
                st.markdown("**🔍 检测到的来源声明：**")
                for i, claim in enumerate(result["claims"], 1):
                    st.markdown(f"{i}. {claim['text']}")
