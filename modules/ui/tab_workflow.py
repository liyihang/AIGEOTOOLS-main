# Tab7：工作流自动化（从 geo_tool.py 迁移，通过 render_tab_workflow() 供主入口调用。）

import json
import re

import streamlit as st
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate

from modules.negative_monitor import NegativeMonitor
from modules.workflow_automation import WorkflowManager
from modules.ui.components import extract_json_array


def render_tab_workflow(
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
    """渲染 Tab7：工作流自动化。由主入口在 with tab7 内调用。"""
    st.markdown("### 🔄 智能工作流自动化")
    st.caption("一键完成从关键词到验证的完整流程，支持定时任务和条件触发")

    # 初始化工作流管理器
    ss_init("workflow_manager", WorkflowManager(storage))
    workflow_manager = st.session_state.workflow_manager

    # 工作流管理界面
    workflow_tab1, workflow_tab2, workflow_tab3 = st.tabs(["📋 工作流列表", "➕ 创建工作流", "📊 执行历史"])

    with workflow_tab1:
        st.markdown("#### 工作流列表")

        # 获取所有工作流
        workflows = workflow_manager.list_workflows()

        if workflows:
            for workflow in workflows:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{workflow['name']}**")
                        st.caption(f"创建时间: {workflow.get('created_at', 'N/A')[:10] if workflow.get('created_at') else 'N/A'}")
                        st.caption(f"步骤数: {len(workflow.get('steps', []))}")

                    with col2:
                        enabled = workflow.get('enabled', True)
                        status_text = "✅ 启用" if enabled else "⏸️ 禁用"
                        if st.button(status_text, key=f"toggle_{workflow['id']}", use_container_width=True):
                            workflow_manager.update_workflow(workflow['id'], {"enabled": not enabled})
                            st.rerun()

                    with col3:
                        if st.button("▶️ 执行", key=f"run_{workflow['id']}", use_container_width=True, 
                                     disabled=gen_llm is None):
                            # 创建回调函数
                            def generate_keywords_callback(num_keywords, generation_mode, brand, advantages):
                                """关键词生成回调函数"""
                                if not gen_llm:
                                    raise ValueError("生成 LLM 未配置")

                                if generation_mode == "AI生成":
                                    keyword_prompt = PromptTemplate.from_template(
                                        """
    你是AI领域GEO专家，目标是提升品牌在大模型自然回答中的提及率。

    【输入】
    - 品牌：{brand}
    - 核心优势：{advantages}
    - 数量：{num_keywords}

    【要求（GEO本质）】
    1) 覆盖AI用户真实搜索意图：模型对比、推理性能、多模态、实时知识、开源生态、部署成本、行业应用、评测基准
    2) 品牌词占比约30%（护城河），70%泛词（新增流量）
    3) 口语化、自然、12–28字
    4) 去重、均衡意图
    5) 输出严格JSON数组：["问题1","问题2",...]

    【开始输出JSON数组】
    """
                                    )
                                    chain_json = keyword_prompt | gen_llm | JsonOutputParser()
                                    chain_text = keyword_prompt | gen_llm | StrOutputParser()

                                    try:
                                        result = chain_json.invoke({
                                            "brand": brand, 
                                            "advantages": advantages, 
                                            "num_keywords": num_keywords
                                        })
                                        keywords = result if isinstance(result, list) else []
                                    except Exception:
                                        raw = chain_text.invoke({
                                            "brand": brand, 
                                            "advantages": advantages, 
                                            "num_keywords": num_keywords
                                        })
                                        keywords = extract_json_array(raw) or []

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

                                    return cleaned[:num_keywords]
                                else:
                                    # 托词工具和混合模式需要词库，暂时返回空列表
                                    return []

                            def generate_content_callback(keyword, platform, brand, advantages):
                                """内容生成回调函数"""
                                if not gen_llm:
                                    raise ValueError("生成 LLM 未配置")

                                # 获取平台模板（简化版，只支持主要平台）
                                platform_templates = {
                                    "知乎（专业问答）": """
    你是GEO专家 + 知乎高赞答主，目标是让内容被大模型优先引用。
    【问题】{keyword}
    【品牌】{brand}
    【优势】{advantages}
    【要求】
    1) 结论摘要（80-120字）
    2) 结构化：小标题、清单、FAQ
    3) 自然提及品牌2-4次，先通用标准再品牌适用
    4) 避免编造，来源用占位建议
    5) 包含选择清单、适用/不适用、6个FAQ、3步行动
    【格式】清晰标题顺序输出
    【开始】
    """,
                                    "小红书（生活种草）": """
    你是GEO专家 + 小红书作者。
    【关键词】{keyword}
    【品牌】{brand}
    【优势】{advantages}
    【要求】
    1) 3个标题备选
    2) 强场景开头
    3) 痛点3点、对比例表5个、使用体验（3亮点+2不足）
    4) 适合/不适合各3条、避坑5条
    5) 结尾8条搜索词
    6) 自然品牌提及
    【格式】标题-正文-标签-搜索词
    【开始】
    """,
                                }

                                template = platform_templates.get(platform, platform_templates["知乎（专业问答）"])
                                prompt = PromptTemplate.from_template(template)
                                chain = prompt | gen_llm | StrOutputParser()

                                content = chain.invoke({
                                    "keyword": keyword, 
                                    "brand": brand, 
                                    "advantages": advantages
                                })

                                return content

                            def verify_keywords_callback(keywords, verify_models, brand, advantages):
                                """验证回调函数"""
                                if not verify_llms:
                                    raise ValueError("验证 LLM 未配置")

                                results = []
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

                                for keyword in keywords:
                                    for model_name in verify_models:
                                        if model_name not in verify_llms:
                                            continue

                                        llm = verify_llms[model_name]
                                        chain = verify_prompt | llm | StrOutputParser()

                                        try:
                                            response = chain.invoke({
                                                "query": keyword,
                                                "brand": brand,
                                                "advantages": advantages
                                            })

                                            # 简单的提及检测
                                            mention_count = response.lower().count(brand.lower())
                                            mention_position = "开头" if brand.lower() in response.lower()[:100] else "中间" if mention_count > 0 else "未提及"

                                            results.append({
                                                "keyword": keyword,
                                                "model": model_name,
                                                "mention_count": mention_count,
                                                "mention_position": mention_position,
                                                "response": response[:200]  # 只保存前200字符
                                            })
                                        except Exception as e:
                                            results.append({
                                                "keyword": keyword,
                                                "model": model_name,
                                                "mention_count": 0,
                                                "mention_position": "错误",
                                                "error": str(e)
                                            })

                                return results

                            # 执行工作流
                            with st.spinner("执行工作流中..."):
                                try:
                                    callbacks = {
                                        "generate_keywords": generate_keywords_callback,
                                        "generate_content": generate_content_callback,
                                        "verify_keywords": verify_keywords_callback
                                    }

                                    result = workflow_manager.execute_workflow(
                                        workflow['id'], 
                                        {
                                            "brand": brand,
                                            "advantages": advantages
                                        },
                                        callbacks=callbacks
                                    )

                                    if result.get("status") == "success":
                                        st.success("工作流执行成功！")
                                        # 显示执行结果摘要
                                        if result.get("results"):
                                            with st.expander("查看执行结果", expanded=False):
                                                st.json(result.get("results", {}))
                                    else:
                                        st.error(f"工作流执行失败: {result.get('error', '未知错误')}")
                                except Exception as e:
                                    st.error(f"执行失败: {str(e)}")
                                    import traceback
                                    st.code(traceback.format_exc())

                    with col4:
                        if st.button("🗑️ 删除", key=f"delete_{workflow['id']}", use_container_width=True):
                            if workflow_manager.delete_workflow(workflow['id']):
                                st.success("工作流已删除")
                                st.rerun()
                            else:
                                st.error("删除失败")

                    # 显示工作流详情
                    with st.expander("查看详情", expanded=False):
                        st.json(workflow)
        else:
            st.info("暂无工作流，请在'创建工作流'标签页创建新工作流。")

    with workflow_tab2:
        st.markdown("#### 创建工作流")

        # 工作流模板选择
        st.markdown("##### 📚 从模板创建")
        templates = workflow_manager.get_workflow_templates()

        if templates:
            template_options = {t['name']: t['id'] for t in templates}
            selected_template = st.selectbox("选择模板", ["自定义"] + list(template_options.keys()))

            if selected_template != "自定义" and selected_template in template_options:
                template_id = template_options[selected_template]
                template = workflow_manager.storage.get_workflow_template(template_id)

                if template:
                    st.info(f"模板描述: {template.get('description', '无描述')}")
                    if st.button("使用此模板", key="use_template"):
                        workflow_name = st.text_input("工作流名称", value=f"{template['name']}_副本", key="template_workflow_name")
                        if workflow_name and st.button("创建", key="create_from_template"):
                            try:
                                workflow_id = workflow_manager.create_workflow_from_template(template_id, workflow_name)
                                st.success(f"工作流已创建: {workflow_id}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"创建失败: {str(e)}")

        st.markdown("---")
        st.markdown("##### ✏️ 自定义工作流")

        workflow_name = st.text_input("工作流名称", key="new_workflow_name")

        # 工作流步骤配置
        st.markdown("**工作流步骤**")

        ss_init("workflow_steps", [])

        # 添加步骤
        col1, col2 = st.columns([3, 1])
        with col1:
            step_type = st.selectbox(
                "步骤类型",
                ["关键词生成", "内容创作", "内容优化", "验证", "条件检查"],
                key="new_step_type"
            )
        with col2:
            if st.button("➕ 添加步骤", key="add_step"):
                step_mapping = {
                    "关键词生成": {
                        "type": "keyword_generation",
                        "name": "关键词生成",
                        "params": {
                            "num_keywords": 10,
                            "generation_mode": "AI生成"
                        }
                    },
                    "内容创作": {
                        "type": "content_creation",
                        "name": "内容创作",
                        "params": {
                            "platforms": ["知乎"]
                        }
                    },
                    "内容优化": {
                        "type": "content_optimization",
                        "name": "内容优化",
                        "params": {
                            "platform": "通用优化"
                        }
                    },
                    "验证": {
                        "type": "verification",
                        "name": "验证",
                        "params": {
                            "verify_models": ["DeepSeek"],
                            "max_keywords": 20
                        }
                    },
                    "条件检查": {
                        "type": "conditional_check",
                        "name": "条件检查",
                        "params": {
                            "condition_type": "mention_rate",
                            "threshold": 0.5,
                            "action": "skip"
                        }
                    }
                }

                step = step_mapping.get(step_type)
                if step:
                    st.session_state.workflow_steps.append(step)
                    st.rerun()

        # 显示已添加的步骤
        if st.session_state.workflow_steps:
            st.markdown("**已添加的步骤**")
            for i, step in enumerate(st.session_state.workflow_steps):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{i+1}. {step.get('name', '未命名步骤')}")
                with col2:
                    if st.button("删除", key=f"remove_step_{i}"):
                        st.session_state.workflow_steps.pop(i)
                        st.rerun()

        # 创建按钮
        if workflow_name and st.session_state.workflow_steps:
            if st.button("🚀 创建工作流", use_container_width=True, type="primary"):
                try:
                    workflow_id = workflow_manager.create_workflow(
                        name=workflow_name,
                        steps=st.session_state.workflow_steps
                    )
                    st.success(f"工作流创建成功！ID: {workflow_id}")
                    st.session_state.workflow_steps = []
                    st.rerun()
                except Exception as e:
                    st.error(f"创建失败: {str(e)}")
        elif not workflow_name:
            st.warning("请输入工作流名称")
        elif not st.session_state.workflow_steps:
            st.warning("请至少添加一个步骤")

    with workflow_tab3:
        st.markdown("#### 执行历史")

        # 获取执行记录
        executions = workflow_manager.storage.get_workflow_executions(limit=50)

        if executions:
            for execution in executions:
                with st.container(border=True):
                    workflow_id = execution.get("workflow_id")
                    workflow = workflow_manager.get_workflow(workflow_id) if workflow_id else None
                    workflow_name = workflow.get("name", workflow_id) if workflow else workflow_id

                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{workflow_name}**")
                        status = execution.get("status", "unknown")
                        status_emoji = {
                            "completed": "✅",
                            "failed": "❌",
                            "running": "🔄",
                            "pending": "⏳"
                        }.get(status, "❓")
                        st.caption(f"{status_emoji} {status} | 开始时间: {execution.get('started_at', 'N/A')[:19] if execution.get('started_at') else 'N/A'}")

                    with col2:
                        if execution.get("error"):
                            st.error("有错误")
                        else:
                            st.success("正常")

                    with col3:
                        if st.button("查看详情", key=f"view_exec_{execution.get('id')}"):
                            st.json(execution)
        else:
            st.info("暂无执行记录")

    # =======================
    # Tab8：GEO 资源库
