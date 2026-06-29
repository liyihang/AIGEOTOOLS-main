"""
公共 UI 组件与工具函数，供各 tab_*.py 复用。

- 纯函数（如 sanitize_filename）不依赖 streamlit，避免循环导入。
- 渲染组件（如 render_section_header、render_download_button）依赖 streamlit。
"""

import re
import json
from typing import Callable, Optional, List, Any

import streamlit as st

# 文件名非法字符，与 geo_tool 主入口规则一致
INVALID_FS_CHARS = r'<>:"/\\|?*\n\r\t'


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """将字符串清理为安全文件名（用于下载等）。各 Tab 统一由此处提供，避免重复实现。"""
    if not name:
        return "untitled"
    name = name.strip()
    name = re.sub(rf"[{re.escape(INVALID_FS_CHARS)}]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name[:max_len] if len(name) > max_len else name


def extract_json_array(text: str) -> Optional[List[Any]]:
    """从模型输出中抽取 JSON 数组（JsonOutputParser 失败时兜底）。"""
    if not text:
        return None
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def safe_decode_uploaded(uploaded) -> str:
    """安全解码上传的文件内容"""
    if not uploaded:
        return ""
    b = uploaded.getvalue()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return b.decode(enc)
        except Exception:
            pass
    return b.decode("utf-8", errors="replace")


def render_section_header(
    title: str,
    caption: Optional[str] = None,
    level: int = 3,
) -> None:
    """渲染区块标题与可选说明。level=3 为 ###，4 为 ####。"""
    prefix = "#" * level
    st.markdown(f"{prefix} {title}")
    if caption:
        st.caption(caption)


def render_download_button(
    label: str,
    data: str | bytes,
    filename: str,
    mime: str,
    key: str,
    use_container_width: bool = True,
) -> None:
    """统一风格的下载按钮。"""
    st.download_button(
        label,
        data=data,
        file_name=filename,
        mime=mime,
        key=key,
        use_container_width=use_container_width,
    )


def render_tab_top_with_clear(
    title: str,
    caption: Optional[str] = None,
    clear_key: str = "tab_clear",
    clear_label: str = "清空本模块结果",
    on_clear: Optional[Callable[[], None]] = None,
) -> None:
    """
    Tab 顶部：左侧标题+说明，右侧「清空本模块结果」按钮。
    on_clear 若提供，会在点击清空时调用（可在此内清空 session_state 并 st.toast）。
    """
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown(f"**{title}**")
        if caption:
            st.caption(caption)
    with col_right:
        if st.button(clear_label, use_container_width=True, key=clear_key):
            if on_clear:
                on_clear()
            st.toast("已清空。")
            st.rerun()


# ========== 统一的消息提示组件 ==========

def show_success(message: str, toast: bool = True) -> None:
    """显示成功消息"""
    st.success(message)
    if toast:
        st.toast(message, icon="✅")


def show_error(message: str, toast: bool = True) -> None:
    """显示错误消息"""
    st.error(message)
    if toast:
        st.toast(message, icon="❌")


def show_warning(message: str, toast: bool = True) -> None:
    """显示警告消息"""
    st.warning(message)
    if toast:
        st.toast(message, icon="⚠️")


def show_info(message: str, toast: bool = True) -> None:
    """显示信息消息"""
    st.info(message)
    if toast:
        st.toast(message, icon="ℹ️")


def show_loading(func, message: str = "加载中..."):
    """统一的加载状态包装器"""
    with st.spinner(message):
        return func()
