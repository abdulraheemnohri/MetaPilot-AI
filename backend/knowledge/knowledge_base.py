"""
Knowledge Base for MetaPilot AI

Manages documents, embeddings, and provides semantic search capabilities.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from dataclasses import dataclass, field
import asyncio

from ..config import settings
from ..database.models import KnowledgeDocument, KnowledgeChunk, Embedding
from ..database.connection import get_async_db_session
from .embeddings import EmbeddingManager
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A search result from the knowledge base."""
    id: str
    content: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }


@dataclass
class DocumentInfo:
    """Information about a document in the knowledge base."""
    id: str
    file_name: str
    file_type: str
    file_size: int
    is_processed: bool
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "is_processed": self.is_processed,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class KnowledgeBase:
    """
    Knowledge base for storing and searching documents.
    
    Features:
    - Document ingestion and processing
    - Chunking and embedding generation
    - Vector similarity search
    - Metadata filtering
    """
    
    def __init__(
        self,
        embedding_manager: Optional[EmbeddingManager] = None,
        document_processor: Optional[DocumentProcessor] = None,
    ):
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.document_processor = document_processor or DocumentProcessor()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the knowledge base."""
        if self._initialized:
            return
        
        logger.info("Initializing Knowledge Base")
        
        # Ensure knowledge directory exists
        settings.KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding manager
        await self.embedding_manager.initialize()
        
        self._initialized = True
        logger.info("Knowledge Base initialized")
    
    async def ingest_document(
        self,
        file_path: Union[str, Path],
        user_id: Optional[int] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentInfo:
        """
        Ingest a document into the knowledge base.
        
        Args:
            file_path: Path to the document file
            user_id: Optional user ID for ownership
            project_id: Optional project ID for organization
            metadata: Optional metadata to attach to the document
        
        Returns:
            DocumentInfo with the ingested document details
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        logger.info(f"Ingesting document: {file_path.name}")
        
        # Read and process the document
        file_content = file_path.read_text(encoding="utf-8", errors="replace")
        file_hash = self._compute_hash(file_content)
        
        # Check if document already exists
        async for session in get_async_db_session():
            existing_doc = await session.execute(
                KnowledgeDocument.__table__.select()
                .where(KnowledgeDocument.content_hash == file_hash)
            )
            existing_doc = existing_doc.scalar_one_or_none()
            
            if existing_doc:
                logger.info(f"Document already exists: {file_path.name}")
                return DocumentInfo(
                    id=existing_doc.id,
                    file_name=existing_doc.file_name,
                    file_type=existing_doc.file_type,
                    file_size=existing_doc.file_size,
                    is_processed=existing_doc.is_processed,
                    chunk_count=len(existing_doc.chunks) if existing_doc.chunks else 0,
                    created_at=existing_doc.created_at,
                    updated_at=existing_doc.updated_at,
                    metadata=existing_doc.metadata or {},
                )
            
            # Create document record
            doc = KnowledgeDocument(
                id=str(asyncio.get_event_loop().time()),
                user_id=user_id,
                project_id=project_id,
                file_name=file_path.name,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_type=self._get_file_type(file_path),
                content=file_content,
                content_hash=file_hash,
                metadata=metadata or {},
                is_processed=False,
            )
            
            session.add(doc)
            await session.flush()
            
            # Process the document (chunking and embedding)
            await self._process_document(doc, file_content)
            
            # Refresh to get updated values
            await session.refresh(doc)
            
            return DocumentInfo(
                id=doc.id,
                file_name=doc.file_name,
                file_type=doc.file_type,
                file_size=doc.file_size,
                is_processed=doc.is_processed,
                chunk_count=len(doc.chunks) if doc.chunks else 0,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                metadata=doc.metadata or {},
            )
    
    async def _process_document(self, doc: KnowledgeDocument, content: str):
        """Process a document by chunking and embedding."""
        logger.info(f"Processing document: {doc.file_name}")
        
        try:
            # Chunk the document
            chunks = self.document_processor.chunk_text(content)
            
            async for session in get_async_db_session():
                for i, chunk in enumerate(chunks):
                    # Create chunk record
                    chunk_record = KnowledgeChunk(
                        id=f"{doc.id}-{i}",
                        document_id=doc.id,
                        content=chunk,
                        chunk_index=i,
                        metadata={"document_name": doc.file_name},
                    )
                    
                    session.add(chunk_record)
                    await session.flush()
                    
                    # Generate embedding
                    embedding = await self.embedding_manager.embed(chunk)
                    
                    # Create embedding record
                    embedding_record = Embedding(
                        id=f"{chunk_record.id}-embedding",
                        chunk_id=chunk_record.id,
                        vector=embedding,
                        dimension=len(embedding),
                        model_name=self.embedding_manager.model_name,
                        metadata={"chunk_index": i},
                    )
                    
                    session.add(embedding_record)
                
                # Mark document as processed
                doc.is_processed = True
                doc.updated_at = datetime.utcnow()
                
                await session.commit()
                
                logger.info(f"Processed document: {doc.file_name} ({len(chunks)} chunks)")
                
        except Exception as e:
            logger.error(f"Failed to process document {doc.file_name}: {e}")
            async for session in get_async_db_session():
                doc.processing_error = str(e)
                await session.commit()
            raise
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        project_id: Optional[str] = None,
        user_id: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search the knowledge base for similar content.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            project_id: Optional project ID to filter by
            user_id: Optional user ID to filter by
            metadata_filter: Optional metadata to filter by
        
        Returns:
            List of SearchResult objects
        """
        # Generate embedding for the query
        query_embedding = await self.embedding_manager.embed(query)
        
        # Search for similar embeddings
        async for session in get_async_db_session():
            # Build query
            from sqlalchemy import select, func
            from sqlalchemy.orm import joinedload
            
            stmt = (
                select(Embedding, KnowledgeChunk, KnowledgeDocument)
                .join(KnowledgeChunk, Embedding.chunk_id == KnowledgeChunk.id)
                .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
                .where(KnowledgeDocument.is_processed == True)
            )
            
            # Apply filters
            if project_id:
                stmt = stmt.where(KnowledgeDocument.project_id == project_id)
            if user_id:
                stmt = stmt.where(KnowledgeDocument.user_id == user_id)
            
            # Execute query
            result = await session.execute(stmt)
            embeddings = result.scalars().all()
            
            # Calculate similarity scores
            results = []
            for embedding in embeddings:
                score = self._cosine_similarity(query_embedding, embedding.vector)
                
                # Apply metadata filter if provided
                if metadata_filter:
                    chunk = embedding.chunk
                    if not self._matches_metadata_filter(chunk.metadata or {}, metadata_filter):
                        continue
                
                results.append({
                    "embedding": embedding,
                    "chunk": embedding.chunk,
                    "document": embedding.chunk.document,
                    "score": score,
                })
            
            # Sort by score (descending)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Convert to SearchResult objects
            search_results = []
            for result in results[:limit]:
                search_results.append(SearchResult(
                    id=result["embedding"].id,
                    content=result["chunk"].content,
                    score=result["score"],
                    document_id=result["document"].id,
                    chunk_id=result["chunk"].id,
                    metadata={
                        "document_name": result["document"].file_name,
                        "chunk_index": result["chunk"].chunk_index,
                        ** (result["chunk"].metadata or {}),
                    },
                ))
            
            return search_results
    
    async def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """Get a document by ID."""
        async for session in get_async_db_session():
            doc = await session.get(KnowledgeDocument, document_id)
            
            if not doc:
                return None
            
            return DocumentInfo(
                id=doc.id,
                file_name=doc.file_name,
                file_type=doc.file_type,
                file_size=doc.file_size,
                is_processed=doc.is_processed,
                chunk_count=len(doc.chunks) if doc.chunks else 0,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                metadata=doc.metadata or {},
            )
    
    async def list_documents(
        self,
        user_id: Optional[int] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentInfo]:
        """List all documents in the knowledge base."""
        async for session in get_async_db_session():
            from sqlalchemy import select
            
            stmt = select(KnowledgeDocument)
            
            if user_id:
                stmt = stmt.where(KnowledgeDocument.user_id == user_id)
            if project_id:
                stmt = stmt.where(KnowledgeDocument.project_id == project_id)
            
            stmt = stmt.order_by(KnowledgeDocument.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            docs = result.scalars().all()
            
            return [
                DocumentInfo(
                    id=doc.id,
                    file_name=doc.file_name,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    is_processed=doc.is_processed,
                    chunk_count=len(doc.chunks) if doc.chunks else 0,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    metadata=doc.metadata or {},
                )
                for doc in docs
            ]
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the knowledge base."""
        async for session in get_async_db_session():
            doc = await session.get(KnowledgeDocument, document_id)
            
            if not doc:
                return False
            
            # Delete related records
            await session.delete(doc)
            await session.commit()
            
            return True
    
    async def update_document_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Update document metadata."""
        async for session in get_async_db_session():
            doc = await session.get(KnowledgeDocument, document_id)
            
            if not doc:
                return False
            
            doc.metadata = {**(doc.metadata or {}), **metadata}
            doc.updated_at = datetime.utcnow()
            
            await session.commit()
            return True
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def _get_file_type(self, file_path: Path) -> str:
        """Get file type from extension."""
        ext = file_path.suffix.lower()
        if ext in [".txt", ".md", ".markdown"]:
            return "text"
        elif ext == ".pdf":
            return "pdf"
        elif ext in [".doc", ".docx"]:
            return "word"
        elif ext in [".json"]:
            return "json"
        elif ext in [".csv"]:
            return "csv"
        else:
            return "unknown"
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        
        a_arr = np.array(a)
        b_arr = np.array(b)
        
        dot_product = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def _matches_metadata_filter(
        self,
        document_metadata: Dict[str, Any],
        filter_metadata: Dict[str, Any],
    ) -> bool:
        """Check if document metadata matches the filter."""
        for key, value in filter_metadata.items():
            if key not in document_metadata:
                return False
            if document_metadata[key] != value:
                return False
        return True
    
    async def reindex_document(self, document_id: str) -> bool:
        """Re-process and re-index a document."""
        async for session in get_async_db_session():
            doc = await session.get(KnowledgeDocument, document_id)
            
            if not doc:
                return False
            
            # Delete existing chunks and embeddings
            if doc.chunks:
                for chunk in doc.chunks:
                    if chunk.embeddings:
                        for embedding in chunk.embeddings:
                            await session.delete(embedding)
                    await session.delete(chunk)
            
            # Re-process
            await self._process_document(doc, doc.content)
            
            return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        async for session in get_async_db_session():
            from sqlalchemy import select, func
            
            # Count documents
            doc_count = await session.scalar(
                select(func.count()).select_from(KnowledgeDocument)
            )
            
            # Count chunks
            chunk_count = await session.scalar(
                select(func.count()).select_from(KnowledgeChunk)
            )
            
            # Count embeddings
            embedding_count = await session.scalar(
                select(func.count()).select_from(Embedding)
            )
            
            # Get storage size
            total_size = await session.scalar(
                select(func.sum(KnowledgeDocument.file_size))
            ) or 0
            
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "model_name": self.embedding_manager.model_name,
                "embedding_dimension": self.embedding_manager.dimension,
            }
