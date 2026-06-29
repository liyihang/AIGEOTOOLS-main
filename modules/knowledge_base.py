"""
RAG 知识库模块
支持用户上传品牌文档，自动分块、索引，生成内容时自动检索相关内容
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentChunk:
    """文档分块"""
    
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
        self.chunk_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DocumentChunk':
        chunk = cls(data["content"], data["metadata"])
        chunk.chunk_id = data["chunk_id"]
        return chunk


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, storage_path: str = "knowledge_base"):
        """
        Args:
            storage_path: 知识库存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 文档元数据
        self.documents_file = self.storage_path / "documents.json"
        # 分块数据
        self.chunks_file = self.storage_path / "chunks.json"
        
        self.documents: Dict[str, Dict] = self._load_json(self.documents_file, {})
        self.chunks: List[Dict] = self._load_json(self.chunks_file, [])
    
    def _load_json(self, path: Path, default: Any) -> Any:
        """加载 JSON 文件"""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载 {path} 失败: {e}")
        return default
    
    def _save_json(self, path: Path, data: Any):
        """保存 JSON 文件"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 {path} 失败: {e}")
    
    def add_document(self, filename: str, content: str, doc_type: str = "text",
                     metadata: Optional[Dict] = None) -> Dict:
        """
        添加文档到知识库
        
        Args:
            filename: 文件名
            content: 文档内容
            doc_type: 文档类型 (text, markdown, faq, case, product)
            metadata: 额外元数据
            
        Returns:
            文档信息
        """
        doc_id = hashlib.md5(f"{filename}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        doc_info = {
            "doc_id": doc_id,
            "filename": filename,
            "doc_type": doc_type,
            "content_length": len(content),
            "chunk_count": 0,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # 分块
        chunks = self._split_document(content, doc_id, filename, doc_type)
        doc_info["chunk_count"] = len(chunks)
        
        # 保存
        self.documents[doc_id] = doc_info
        self.chunks.extend([c.to_dict() for c in chunks])
        
        self._save_json(self.documents_file, self.documents)
        self._save_json(self.chunks_file, self.chunks)
        
        logger.info(f"文档 '{filename}' 已添加，分为 {len(chunks)} 个分块")
        return doc_info
    
    def _split_document(self, content: str, doc_id: str, filename: str, 
                        doc_type: str, chunk_size: int = 500, overlap: int = 50) -> List[DocumentChunk]:
        """
        将文档分割为多个分块
        
        Args:
            content: 文档内容
            doc_id: 文档 ID
            filename: 文件名
            doc_type: 文档类型
            chunk_size: 分块大小（字符数）
            overlap: 重叠字符数
            
        Returns:
            分块列表
        """
        chunks = []
        
        # 根据文档类型选择分块策略
        if doc_type == "faq":
            # FAQ 文档按 Q&A 对分块
            chunks = self._split_faq(content, doc_id, filename)
        elif doc_type == "product":
            # 产品文档按功能/特性分块
            chunks = self._split_by_sections(content, doc_id, filename, doc_type)
        else:
            # 通用文档按段落/长度分块
            chunks = self._split_by_length(content, doc_id, filename, doc_type, 
                                          chunk_size, overlap)
        
        return chunks
    
    def _split_faq(self, content: str, doc_id: str, filename: str) -> List[DocumentChunk]:
        """FAQ 文档分块：每个 Q&A 对为一个分块"""
        chunks = []
        lines = content.split('\n')
        
        current_q = ""
        current_a = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测问题行
            if line.startswith('Q:') or line.startswith('问：') or line.startswith('Q：'):
                # 保存上一个 Q&A 对
                if current_q and current_a:
                    chunk_content = f"问题：{current_q}\n回答：{current_a}"
                    chunks.append(DocumentChunk(
                        content=chunk_content,
                        metadata={
                            "doc_id": doc_id,
                            "filename": filename,
                            "type": "faq",
                            "question": current_q
                        }
                    ))
                current_q = line[2:].strip()
                current_a = ""
            elif line.startswith('A:') or line.startswith('答：') or line.startswith('A：'):
                current_a = line[2:].strip()
            elif current_a:
                current_a += "\n" + line
            elif current_q and not current_a:
                current_q += "\n" + line
        
        # 保存最后一个 Q&A 对
        if current_q and current_a:
            chunk_content = f"问题：{current_q}\n回答：{current_a}"
            chunks.append(DocumentChunk(
                content=chunk_content,
                metadata={
                    "doc_id": doc_id,
                    "filename": filename,
                    "type": "faq",
                    "question": current_q
                }
            ))
        
        return chunks
    
    def _split_by_sections(self, content: str, doc_id: str, filename: str,
                           doc_type: str) -> List[DocumentChunk]:
        """按章节分块（适用于产品文档、Markdown 等）"""
        chunks = []
        sections = content.split('\n# ')
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            # 提取标题
            lines = section.split('\n', 1)
            title = lines[0].strip('# ').strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            
            if body:
                chunks.append(DocumentChunk(
                    content=f"## {title}\n{body}",
                    metadata={
                        "doc_id": doc_id,
                        "filename": filename,
                        "type": doc_type,
                        "section_title": title
                    }
                ))
        
        return chunks
    
    def _split_by_length(self, content: str, doc_id: str, filename: str,
                         doc_type: str, chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """按长度分块"""
        chunks = []
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(DocumentChunk(
                    content=current_chunk,
                    metadata={
                        "doc_id": doc_id,
                        "filename": filename,
                        "type": doc_type
                    }
                ))
                # 保留重叠部分
                if overlap > 0:
                    current_chunk = current_chunk[-overlap:] + "\n" + para
                else:
                    current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
        
        # 保存最后一个分块
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                content=current_chunk,
                metadata={
                    "doc_id": doc_id,
                    "filename": filename,
                    "type": doc_type
                }
            ))
        
        return chunks
    
    def search(self, query: str, top_k: int = 5, 
               doc_type: Optional[str] = None) -> List[Dict]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_type: 过滤文档类型
            
        Returns:
            相关分块列表
        """
        if not self.chunks:
            return []
        
        # 计算相似度分数
        scored_chunks = []
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        for chunk_data in self.chunks:
            content_lower = chunk_data["content"].lower()
            
            # 计算关键词匹配分数
            keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
            keyword_score = keyword_matches / len(query_keywords) if query_keywords else 0
            
            # 计算内容相关性分数（包含查询词的比例）
            content_score = 0
            for kw in query_keywords:
                if kw in content_lower:
                    # 计算关键词在内容中的密度
                    count = content_lower.count(kw)
                    content_score += count * len(kw) / len(content_lower)
            
            # 综合分数
            total_score = keyword_score * 0.6 + content_score * 0.4
            
            if total_score > 0:
                # 过滤文档类型
                if doc_type and chunk_data["metadata"].get("type") != doc_type:
                    continue
                
                scored_chunks.append({
                    "chunk": chunk_data,
                    "score": total_score
                })
        
        # 按分数排序并返回 top_k
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        return [
            {
                "content": item["chunk"]["content"],
                "metadata": item["chunk"]["metadata"],
                "score": item["score"]
            }
            for item in scored_chunks[:top_k]
        ]
    
    def get_context_for_generation(self, query: str, brand: str, 
                                   platform: str, top_k: int = 3) -> str:
        """
        获取用于内容生成的上下文
        
        Args:
            query: 查询/主题
            brand: 品牌名
            platform: 目标平台
            
        Returns:
            格式化的上下文字符串
        """
        # 搜索相关文档
        results = self.search(query, top_k=top_k)
        
        if not results:
            return ""
        
        # 组装上下文
        context_parts = ["以下是相关的品牌/产品信息，可用于内容生成：\n"]
        
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("filename", "未知来源")
            content = result["content"]
            
            context_parts.append(f"--- 参考资料 {i}（来源：{source}）---")
            context_parts.append(content)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def list_documents(self) -> List[Dict]:
        """列出所有文档"""
        return list(self.documents.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档及其分块"""
        if doc_id not in self.documents:
            return False
        
        # 删除文档
        del self.documents[doc_id]
        
        # 删除相关分块
        self.chunks = [c for c in self.chunks if c["metadata"].get("doc_id") != doc_id]
        
        # 保存
        self._save_json(self.documents_file, self.documents)
        self._save_json(self.chunks_file, self.chunks)
        
        return True
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        doc_types = {}
        for doc in self.documents.values():
            doc_type = doc.get("doc_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "document_types": doc_types
        }


class SourceVerifier:
    """来源验证器"""
    
    def __init__(self):
        self.claim_patterns = [
            "根据",
            "据",
            "报告显示",
            "数据表明",
            "研究表明",
            "调查发现",
            "据统计",
            "根据报告",
            "根据数据",
            "根据研究",
            "according to",
            "based on",
            "as reported by",
            "research shows",
            "data shows"
        ]
    
    def extract_claims(self, content: str) -> List[Dict]:
        """
        从内容中提取来源声明
        
        Args:
            content: 文本内容
            
        Returns:
            声明列表
        """
        claims = []
        sentences = content.replace('。', '。\n').replace('.', '.\n').split('\n')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            for pattern in self.claim_patterns:
                if pattern in sentence.lower():
                    claims.append({
                        "text": sentence,
                        "pattern": pattern,
                        "verified": False,
                        "verification_result": None
                    })
                    break
        
        return claims
    
    def generate_verification_prompt(self, claim: str) -> str:
        """
        生成验证提示词
        
        Args:
            claim: 来源声明
            
        Returns:
            验证提示词
        """
        return f"""请验证以下声明的真实性：

声明：{claim}

请回答：
1. 这个声明是否包含可验证的具体来源（如具体报告名称、机构名称、数据年份）？
2. 如果包含，请判断这个来源是否可能存在且可信。
3. 如果无法验证或来源可疑，请说明原因。

回答格式：
- 来源具体性：[具体/模糊/无来源]
- 可信度评估：[高/中/低/无法判断]
- 建议：[保留/修改/删除]
- 原因：[简要说明]"""
    
    def assess_source_quality(self, content: str) -> Dict:
        """
        评估内容的来源质量
        
        Args:
            content: 文本内容
            
        Returns:
            质量评估结果
        """
        claims = self.extract_claims(content)
        
        if not claims:
            return {
                "has_sources": False,
                "claim_count": 0,
                "quality_score": 0,
                "suggestions": ["内容中没有引用任何来源，建议添加数据支撑"]
            }
        
        # 分析来源质量
        specific_count = 0
        vague_count = 0
        
        for claim in claims:
            text = claim["text"]
            # 检查是否有具体来源指标
            has_specific = any([
                any(year in text for year in ["2020", "2021", "2022", "2023", "2024", "2025"]),
                any(org in text for org in ["Gartner", "IDC", "Forrester", "McKinsey", 
                                           "哈佛", "MIT", "斯坦福", "中科院"]),
                "报告" in text and ("《" in text or "年" in text),
                "数据" in text and any(c.isdigit() for c in text)
            ])
            
            if has_specific:
                specific_count += 1
            else:
                vague_count += 1
        
        quality_score = min(100, (specific_count / len(claims)) * 100)
        
        suggestions = []
        if vague_count > 0:
            suggestions.append(f"有 {vague_count} 个来源描述模糊，建议补充具体报告名称或数据年份")
        if specific_count == 0:
            suggestions.append("所有来源都不够具体，建议引用真实的行业报告或权威机构数据")
        
        return {
            "has_sources": True,
            "claim_count": len(claims),
            "specific_count": specific_count,
            "vague_count": vague_count,
            "quality_score": quality_score,
            "claims": claims,
            "suggestions": suggestions
        }
