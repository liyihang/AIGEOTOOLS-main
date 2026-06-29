# Tab10：配置优化助手（从 geo_tool.py 迁移，通过 render_tab_config_optimizer() 供主入口调用。）

import hashlib

import streamlit as st

from modules.config_optimizer import ConfigOptimizer


def render_tab_config_optimizer(
    storage,
    cfg: dict,
    brand: str,
    advantages: str,
    competitor_list: list,
    build_llm,
    model_defaults,
) -> None:
    """渲染 Tab10：配置优化助手。由主入口在 with tab10 内调用。"""
    # 配置优化助手（与其他Tab保持一致的标题格式）
    st.markdown("### 🎯 配置优化助手")
    st.caption("分析品牌名和优势是否 GEO 友好，提供优化建议。优化后可一键应用到全局配置。")

    # 初始化优化结果存储
    if "config_optimization_result" not in st.session_state:
        st.session_state.config_optimization_result = None

    # 初始化配置hash（用于检测配置变化）
    if "config_hash" not in st.session_state:
        st.session_state.config_hash = None

    # 计算当前配置的hash（使用cfg中的最新值）
    brand_for_hash = cfg.get("brand", "").strip() or brand or ""
    advantages_for_hash = cfg.get("advantages", "").strip() or advantages or ""
    current_config_str = f"{brand_for_hash}|{advantages_for_hash}|{cfg.get('competitors', '')}"
    current_config_hash = hashlib.md5(current_config_str.encode()).hexdigest()

    # 如果配置变化了，清除旧的优化结果
    # 但如果是因为应用版本导致的配置变化，保留优化结果
    if st.session_state.config_hash != current_config_hash:
        # 检查是否是应用版本导致的配置变化
        if not st.session_state.get("_applying_version", False):
            st.session_state.config_optimization_result = None
        st.session_state.config_hash = current_config_hash
        # 清除应用版本标志
        st.session_state["_applying_version"] = False

    # 检查配置是否有效
    if not st.session_state.cfg_valid:
        st.warning("⚠️ 请先在侧边栏完成配置并点击'应用配置'")
        st.info("配置优化助手需要有效的配置才能进行分析。")
    else:
        # 显示当前配置
        with st.expander("📋 当前配置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                brand_display = cfg.get("brand", "") or brand or "未设置"
                st.markdown(f"**品牌名**：{brand_display}")
            with col2:
                st.markdown(f"**竞品数量**：{len(competitor_list)}个")
            advantages_display = cfg.get("advantages", "") or advantages or "未设置"
            st.markdown(f"**核心优势**：{advantages_display}")
            if competitor_list:
                st.markdown(f"**竞品列表**：{', '.join(competitor_list[:5])}{'...' if len(competitor_list) > 5 else ''}")

        # 分析按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            analyze_btn = st.button("🔍 分析配置优化", type="primary", use_container_width=True, key="tab10_optimize_config")

        with col2:
            if st.session_state.config_optimization_result:
                st.success("✅ 已有优化结果")

        # 执行分析
        if analyze_btn:
            with st.spinner("正在分析配置，优化建议生成中..."):
                try:
                    optimizer = ConfigOptimizer()

                    # 从配置中获取品牌名、优势描述和竞品列表（确保使用最新配置）
                    brand_for_optimizer = cfg.get("brand", "").strip() or brand or ""
                    advantages_for_optimizer = cfg.get("advantages", "").strip() or advantages or ""
                    competitors_str = cfg.get("competitors", "")
                    competitor_list_for_optimizer = [c.strip() for c in competitors_str.split("\n") if c.strip()]

                    # 验证必要配置
                    if not brand_for_optimizer:
                        st.error("❌ 品牌名不能为空，请在侧边栏配置主品牌名称")
                        st.stop()

                    if not advantages_for_optimizer:
                        st.warning("⚠️ 优势描述为空，建议在侧边栏配置核心优势/卖点")

                    # 临时构建LLM用于分析（使用当前配置）
                    temp_llm = build_llm(
                        cfg["gen_provider"],
                        cfg["gen_api_key"],
                        model_defaults(cfg["gen_provider"]),
                        float(cfg.get("temperature", 0.7))
                    )

                    result = optimizer.optimize_config(
                        brand=brand_for_optimizer,
                        advantages=advantages_for_optimizer,
                        competitors=competitor_list_for_optimizer,
                        llm_chain=temp_llm
                    )
                    st.session_state.config_optimization_result = result
                    st.session_state.config_hash = current_config_hash
                    st.success("✅ 配置分析完成！")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 配置优化分析失败：{e}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
                    st.session_state.config_optimization_result = None

        # 显示优化结果
        if st.session_state.config_optimization_result:
            result = st.session_state.config_optimization_result
            if result.get("success", False):
                st.markdown("---")
                st.markdown("#### 📊 优化分析结果")

                # 评估总结
                if result.get("summary"):
                    st.markdown("**📝 评估总结**")
                    st.info(result["summary"])

                # 优化建议
                if result.get("suggestions"):
                    st.markdown("**💡 优化建议**")
                    suggestions = result["suggestions"]

                    if suggestions.get("brand", {}).get("problem"):
                        st.markdown("**🔸 品牌名问题**：")
                        # 直接使用st.markdown渲染，CSS会限制标题大小
                        problem_text = suggestions["brand"]["problem"]
                        st.markdown(problem_text)
                        if suggestions["brand"].get("suggestion"):
                            st.markdown("**✅ 建议**：")
                            suggestion_text = suggestions["brand"]["suggestion"]
                            st.markdown(suggestion_text)

                    if suggestions.get("advantages", {}).get("problem"):
                        st.markdown("**🔸 优势描述问题**：")
                        problem_text = suggestions["advantages"]["problem"]
                        st.markdown(problem_text)
                        if suggestions["advantages"].get("suggestion"):
                            st.markdown("**✅ 建议**：")
                            suggestion_text = suggestions["advantages"]["suggestion"]
                            st.markdown(suggestion_text)

                # 推荐版本
                recommended_versions = result.get("recommended_versions", [])
                if recommended_versions:
                    st.markdown("**🎯 推荐版本**")
                    st.caption("选择最适合的版本，点击「应用版本」按钮即可更新配置")

                    # 检查是否有有效的推荐版本
                    valid_versions = [v for v in recommended_versions if v.get("brand") or v.get("advantages")]
                    if not valid_versions:
                        st.warning("⚠️ 推荐版本数据为空，可能是解析失败。请查看完整报告或重新分析。")
                        if result.get("raw_result"):
                            with st.expander("查看原始输出中的推荐版本部分"):
                                raw = result["raw_result"]
                                if "【推荐版本】" in raw:
                                    raw_versions = raw.split("【推荐版本】")[1].split("【")[0]
                                    st.code(raw_versions)

                    for i, version in enumerate(recommended_versions[:3], 1):
                        version_name_map = {
                            1: "保守优化",
                            2: "平衡优化",
                            3: "激进优化"
                        }
                        version_name = version_name_map.get(i, f"版本{i}")

                        with st.expander(f"版本{i}：{version_name}", expanded=False):  # 默认不展开，用户自行选择
                            # 检查版本数据是否有效
                            has_brand = bool(version.get("brand", "").strip())
                            has_advantages = bool(version.get("advantages", "").strip())
                            has_reason = bool(version.get("reason", "").strip())

                            if not has_brand and not has_advantages:
                                st.warning("⚠️ 该版本数据不完整，请查看完整报告或重新分析")
                                if result.get("raw_result"):
                                    with st.expander("查看原始输出中的该版本"):
                                        # 尝试从原始输出中提取
                                        raw = result["raw_result"]
                                        if f"版本{i}" in raw:
                                            version_raw = raw.split(f"版本{i}")[1]
                                            if i < 3:
                                                next_version = f"版本{i+1}"
                                                if next_version in version_raw:
                                                    version_raw = version_raw.split(next_version)[0]
                                            st.code(version_raw[:500])  # 显示前500字符
                            else:
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    if has_brand:
                                        st.markdown(f"**品牌名**：`{version['brand']}`")
                                    else:
                                        st.warning("⚠️ 品牌名为空")

                                    if has_advantages:
                                        st.markdown(f"**优势描述**：{version['advantages']}")
                                    else:
                                        st.warning("⚠️ 优势描述为空")

                                    if has_reason:
                                        st.caption(f"💭 理由：{version['reason']}")
                                    else:
                                        st.caption("💭 理由：未提供")

                                with col2:
                                    # 应用按钮
                                    apply_disabled = not (has_brand and has_advantages)
                                    if st.button(
                                        f"✅ 应用版本{i}", 
                                        key=f"tab10_apply_version_{i}", 
                                        use_container_width=True, 
                                        type="primary",
                                        disabled=apply_disabled
                                    ):
                                        if has_brand and has_advantages:
                                            # 设置标志，表示正在应用版本（防止优化结果被清除）
                                            st.session_state["_applying_version"] = True
                                            # 更新配置
                                            st.session_state.cfg["brand"] = version["brand"]
                                            st.session_state.cfg["advantages"] = version["advantages"]
                                            # 设置标志，表示需要更新侧边栏输入框
                                            st.session_state["_pending_brand_update"] = version["brand"]
                                            st.session_state["_pending_advantages_update"] = version["advantages"]
                                            st.session_state.cfg_applied = False  # 需要重新应用配置
                                            st.success(f"✅ 已应用版本{i}，侧边栏已更新，请点击'应用配置'以生效")
                                            st.info("💡 配置更新后，建议重新运行关键词蒸馏和内容创作，以获得最佳效果")
                                            st.rerun()
                                    if apply_disabled:
                                        st.caption("⚠️ 数据不完整，无法应用")

                # 预期效果
                if result.get("expected_effects"):
                    st.markdown("**📈 预期效果**")
                    effects = result["expected_effects"]
                    # 使用文本而不是 metric，避免内容被截断
                    if effects.get("mention_rate"):
                        st.markdown(f"- 提及率提升预期：{effects['mention_rate']}")
                    if effects.get("geo_friendliness"):
                        st.markdown(f"- GEO友好度提升：{effects['geo_friendliness']}")

                # 完整报告
                if result.get("raw_result"):
                    with st.expander("📄 查看完整分析报告", expanded=False):
                        st.markdown(result["raw_result"])

                        # 如果推荐版本为空或解析失败，显示原始输出中的推荐版本部分
                        recommended_versions = result.get("recommended_versions", [])
                        if not recommended_versions or all(
                            not v.get("brand") and not v.get("advantages") 
                            for v in recommended_versions
                        ):
                            st.warning("⚠️ 推荐版本解析失败，以下是原始输出中的推荐版本部分，请检查格式：")
                            raw = result["raw_result"]
                            if "【推荐版本】" in raw:
                                raw_versions = raw.split("【推荐版本】")[1].split("【")[0]
                                st.code(raw_versions, language="text")
                                st.info("💡 如果原始输出中包含推荐版本但解析失败，请检查格式是否符合要求")

                # 调试信息（可选）
                if st.checkbox("🔍 显示调试信息", key="tab10_debug"):
                    st.markdown("#### 调试信息")
                    debug_info = {
                        "推荐版本数量": len(result.get("recommended_versions", [])),
                        "版本详情": result.get("recommended_versions", []),
                        "配置hash": st.session_state.config_hash,
                        "解析错误": result.get("parse_errors", [])
                    }
                    st.json(debug_info)

                    # 显示原始输出的关键部分
                    if result.get("raw_result"):
                        raw = result["raw_result"]
                        if "【推荐版本】" in raw:
                            st.markdown("**原始输出中的推荐版本部分：**")
                            raw_versions = raw.split("【推荐版本】")[1].split("【")[0]
                            st.code(raw_versions[:1000], language="text")  # 显示前1000字符
            else:
                st.error(f"❌ 分析失败：{result.get('error', '未知错误')}")
                if result.get("raw_result"):
                    with st.expander("查看原始输出"):
                        st.code(result["raw_result"])
        else:
            st.info("💡 点击上方「分析配置优化」按钮开始分析，系统会根据当前配置生成优化建议。")
            st.caption("提示：当您修改品牌名、优势描述或竞品列表后，系统会自动清除旧结果，需要重新分析。")
