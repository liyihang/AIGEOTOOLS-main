import streamlit as st


def inject_global_theme():
    """注入全局 CSS 主题 - 紧凑、高信息密度的 C 端产品 UI"""
    st.markdown(
        """
<style>
/* ========== 字体导入 ========== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

/* ========== CSS 变量 ========== */
:root {
  --primary: #4F46E5;
  --primary-light: #818CF8;
  --primary-dark: #3730A3;
  --primary-bg: #EEF2FF;
  --success: #059669;
  --success-bg: #ECFDF5;
  --warning: #D97706;
  --warning-bg: #FFFBEB;
  --error: #DC2626;
  --error-bg: #FEF2F2;
  --bg-white: #FFFFFF;
  --bg-gray: #F9FAFB;
  --bg-light: #F3F4F6;
  --border: #E5E7EB;
  --border-light: #F3F4F6;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --text-muted: #9CA3AF;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  /* 间距变量 - 紧凑风格 */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 0.75rem;
  --space-lg: 1rem;
  --space-xl: 1.5rem;
}

/* ========== 全局基础 ========== */
html, body, .stApp {
  font-family: "Inter", "Noto Sans SC", -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text-primary);
  background: var(--bg-gray);
}

.main .block-container {
  max-width: 1200px;
  padding: 1.5rem 1.5rem 2rem;
}

/* ========== 页面标题 ========== */
h1 {
  font-weight: 700 !important;
  font-size: 1.5rem !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.025em;
  margin-bottom: 0.5rem !important;
}

/* 副标题 */
.main .block-container > div:first-child p {
  margin-bottom: 0.5rem;
}

/* ========== 侧边栏 ========== */
section[data-testid="stSidebar"] {
  background: var(--bg-white);
  border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] .block-container {
  padding: 1rem 0.75rem;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  font-size: 0.875rem !important;
  margin-bottom: 0.5rem !important;
}

/* 侧边栏 expander */
section[data-testid="stSidebar"] .streamlit-expanderHeader {
  background: var(--bg-gray);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  font-weight: 600;
  font-size: 0.8125rem;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.25rem;
}

section[data-testid="stSidebar"] .streamlit-expanderContent {
  background: var(--bg-white);
  border: none;
  padding: 0.5rem 0;
}

/* ========== KPI 卡片 - 统一大小 ========== */
[data-testid="stHorizontalBlock"] {
  display: flex !important;
  align-items: stretch !important;
  gap: 0.75rem !important;
  margin-bottom: 0.75rem !important;
}

[data-testid="stHorizontalBlock"] > div {
  flex: 1 1 0% !important;
  min-width: 0 !important;
}

[data-testid="stMetric"] {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
  height: 90px !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  overflow: hidden;
}

[data-testid="stMetric"]:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-light);
}

[data-testid="stMetricLabel"] {
  font-size: 0.6875rem !important;
  font-weight: 600 !important;
  color: var(--text-secondary) !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.25rem !important;
}

[data-testid="stMetricValue"] {
  font-size: 1.375rem !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-testid="stMetricDelta"] {
  font-size: 0.6875rem !important;
  font-weight: 500 !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-testid="stMetric"] > div {
  padding: 0 !important;
  margin: 0 !important;
}

/* ========== Tabs 导航 - 紧凑胶囊 ========== */
.stTabs {
  margin-top: 0 !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.25rem;
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  padding: 0.25rem;
  box-shadow: var(--shadow-xs);
  overflow-x: auto;
  flex-wrap: nowrap;
  margin-bottom: 0 !important;
}

.stTabs [data-baseweb="tab"] {
  padding: 0.5rem 0.875rem;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.8125rem;
  transition: all 0.15s ease;
  white-space: nowrap;
  border: none;
  min-height: unset;
}

.stTabs [data-baseweb="tab"]:hover {
  background: var(--bg-gray);
  color: var(--text-primary);
}

.stTabs [aria-selected="true"] {
  background: var(--primary) !important;
  color: white !important;
  font-weight: 600 !important;
  box-shadow: var(--shadow-sm);
}

.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] {
  display: none;
}

/* Tab 内容区域 - 紧凑 */
.stTabs [data-baseweb="tab-panel"] {
  padding: 0.75rem 0;
  border: none;
}

/* ========== 按钮 ========== */
button {
  border-radius: var(--radius-md) !important;
  font-weight: 500;
  font-size: 0.8125rem;
  transition: all 0.15s ease;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
}

button[kind="primary"] {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
  color: white !important;
  border: none !important;
  box-shadow: var(--shadow-sm);
}

button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--primary-dark), var(--primary)) !important;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

button[kind="secondary"] {
  background: var(--bg-white);
  color: var(--text-primary);
  border: 1px solid var(--border) !important;
}

button[kind="secondary"]:hover {
  background: var(--bg-gray);
  border-color: var(--primary-light) !important;
}

/* ========== 输入框 - 紧凑 ========== */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  transition: all 0.15s ease;
  background: var(--bg-white);
}

.stTextInput input:focus,
.stTextArea textarea:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px var(--primary-bg);
  outline: none;
}

.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label,
.stRadio label,
.stCheckbox label,
.stSlider label {
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--text-secondary) !important;
  margin-bottom: 0.25rem !important;
}

/* ========== 选择框 ========== */
.stSelectbox [data-baseweb="select"] > div {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
  min-height: 2.25rem;
  font-size: 0.8125rem;
}

.stSelectbox [data-baseweb="select"]:hover > div {
  border-color: var(--primary-light) !important;
}

.stSelectbox [data-baseweb="select"]:focus-within > div {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px var(--primary-bg) !important;
}

/* 多选框 */
.stMultiSelect [data-baseweb="select"] > div {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
}

.stMultiSelect [data-baseweb="tag"] {
  border-radius: var(--radius-sm) !important;
  background: var(--primary-bg) !important;
  color: var(--primary) !important;
  border: 1px solid var(--primary-light) !important;
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.375rem;
}

/* ========== Radio & Checkbox ========== */
.stRadio [data-baseweb="radio"] {
  font-size: 0.8125rem;
}

.stRadio [data-baseweb="radio-control"] {
  border-color: var(--border);
}

.stRadio [data-baseweb="radio-control"]:checked {
  background: var(--primary);
  border-color: var(--primary);
}

/* ========== Slider ========== */
.stSlider [data-baseweb="slider"] {
  height: 4px;
}

.stSlider [data-baseweb="thumb"] {
  background: var(--primary);
  border: 2px solid white;
  box-shadow: var(--shadow-sm);
}

/* ========== 容器 - 紧凑 ========== */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-xs);
  background: var(--bg-white);
  padding: 1rem !important;
  margin-bottom: 0.5rem !important;
}

/* ========== Expander - 紧凑 ========== */
.streamlit-expanderHeader {
  border-radius: var(--radius-md);
  background: var(--bg-white);
  border: 1px solid var(--border);
  font-weight: 500;
  font-size: 0.8125rem;
  padding: 0.5rem 0.75rem;
}

.streamlit-expanderHeader:hover {
  background: var(--bg-gray);
  border-color: var(--primary-light);
}

.streamlit-expanderContent {
  padding: 0.5rem 0 !important;
}

/* ========== 表格 ========== */
.stDataFrame {
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border);
  font-size: 0.8125rem;
}

/* ========== 提示框 - 紧凑 ========== */
.stAlert {
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  border: none;
  padding: 0.5rem 0.75rem;
}

div[data-baseweb="notification"] {
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  padding: 0.5rem 0.75rem;
}

/* ========== 分割线 - 紧凑 ========== */
hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.75rem 0;
}

/* ========== Markdown 内容 - 紧凑 ========== */
.stMarkdown {
  font-size: 0.8125rem;
  line-height: 1.5;
}

.stMarkdown p {
  margin-bottom: 0.375rem;
}

.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4 {
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 0.75rem;
  margin-bottom: 0.375rem;
  font-size: 0.875rem;
}

/* 表单 */
.stForm {
  border: none !important;
  padding: 0 !important;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .main .block-container {
    padding: 1rem;
  }
  
  [data-testid="stMetric"] {
    padding: 0.75rem;
    height: 80px !important;
  }
  
  [data-testid="stMetricValue"] {
    font-size: 1.125rem !important;
  }
  
  .stTabs [data-baseweb="tab"] {
    padding: 0.375rem 0.625rem;
    font-size: 0.75rem;
  }
  
  section[data-testid="stSidebar"] {
    width: 100% !important;
    min-width: unset !important;
  }
  
  div[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 0.75rem !important;
  }
}

@media (max-width: 480px) {
  h1 {
    font-size: 1.25rem !important;
  }
}

/* ========== 滚动条 ========== */
::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* ========== 选中文本 ========== */
::selection {
  background: var(--primary-bg);
  color: var(--primary-dark);
}

/* ========== 动画 ========== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.stApp > .main {
  animation: fadeIn 0.2s ease;
}

/* ========== 移除多余间距 ========== */
.element-container {
  margin-bottom: 0 !important;
}

div[data-testid="stVerticalBlock"] > div {
  margin-bottom: 0 !important;
}

/* 紧凑型 columns 间距 */
[data-testid="stHorizontalBlock"] {
  gap: 0.5rem !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
