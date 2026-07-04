"""
Memory System for MetaPilot AI

Manages conversation history, context windows, and memory for AI interactions.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from collections import deque
import hashlib

from ..config import settings
from ..database.models import Conversation, Message
from ..database.connection import get_async_db_session
from ..knowledge.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """An entry in the memory system."""
    id: str
    content: str
    role: str  # "system", "user", "assistant"
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "embedding": self.embedding,
        }


@dataclass
class ContextWindow:
    """A context window for AI interactions."""
    messages: List[Dict[str, Any]]
    token_count: int
    memory_entries: List[MemoryEntry] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": self.messages,
            "token_count": self.token_count,
            "memory_entries": [e.to_dict() for e in self.memory_entries],
        }


class MemorySystem:
    """
    Memory system for managing conversation context and history.
    
    Features:
    - Conversation history management
    - Context window generation
    - Short-term and long-term memory
    - Token-aware context trimming
    - Memory compression and summarization
    """
    
    def __init__(
        self,
        max_context_tokens: int = 4096,
        max_memory_entries: int = 1000,
        short_term_memory_size: int = 50,
        long_term_memory_size: int = 500,
        embedding_manager: Optional[EmbeddingManager] = None,
    ):
        self.max_context_tokens = max_context_tokens
        self.max_memory_entries = max_memory_entries
        self.short_term_memory_size = short_term_memory_size
        self.long_term_memory_size = long_term_memory_size
        self.embedding_manager = embedding_manager
        
        # In-memory storage for active conversations
        self._conversations: Dict[str, List[MemoryEntry]] = {}
        self._context_windows: Dict[str, ContextWindow] = {}
        
        # Token estimation (approximate)
        self._token_per_char = 0.25  # Rough estimate
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the memory system."""
        if self._initialized:
            return
        
        logger.info("Initializing Memory System")
        
        # Initialize embedding manager if not provided
        if not self.embedding_manager:
            self.embedding_manager = EmbeddingManager()
            await self.embedding_manager.initialize()
        
        self._initialized = True
        logger.info("Memory System initialized")
    
    async def add_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        Add a message to the conversation memory.
        
        Args:
            conversation_id: ID of the conversation
            content: Message content
            role: Role of the message sender ("system", "user", "assistant")
            metadata: Optional metadata
        
        Returns:
            The created MemoryEntry
        """
        if not self._initialized:
            await self.initialize()
        
        # Create memory entry
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            role=role,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )
        
        # Store in memory
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        self._conversations[conversation_id].append(entry)
        
        # Trim memory if needed
        await self._trim_memory(conversation_id)
        
        # Also save to database
        await self._save_to_database(conversation_id, entry)
        
        return entry
    
    async def get_conversation_memory(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """
        Get all memory entries for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of entries to return
        
        Returns:
            List of MemoryEntry objects
        """
        if not self._initialized:
            await self.initialize()
        
        entries = self._conversations.get(conversation_id, [])
        
        if limit:
            entries = entries[-limit:]
        
        return entries
    
    async def get_context_window(
        self,
        conversation_id: str,
        max_tokens: Optional[int] = None,
    ) -> ContextWindow:
        """
        Get a context window for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            max_tokens: Maximum number of tokens in the context window
        
        Returns:
            ContextWindow with messages and token count
        """
        if not self._initialized:
            await self.initialize()
        
        max_tokens = max_tokens or self.max_context_tokens
        
        # Get conversation entries
        entries = self._conversations.get(conversation_id, [])
        
        if not entries:
            return ContextWindow(messages=[], token_count=0)
        
        # Convert entries to messages
        messages = []
        for entry in entries:
            messages.append({
                "role": entry.role,
                "content": entry.content,
            })
        
        # Calculate token count
        token_count = self._estimate_token_count(entries)
        
        # Trim messages to fit in context window
        if token_count > max_tokens:
            messages = self._trim_messages_to_tokens(messages, max_tokens)
            token_count = self._estimate_token_count_from_messages(messages)
        
        return ContextWindow(
            messages=messages,
            token_count=token_count,
            memory_entries=entries,
        )
    
    async def search_memory(
        self,
        conversation_id: str,
        query: str,
        limit: int = 5,
    ) -> List[MemoryEntry]:
        """
        Search conversation memory for relevant entries.
        
        Args:
            conversation_id: ID of the conversation
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of relevant MemoryEntry objects
        """
        if not self._initialized:
            await self.initialize()
        
        entries = self._conversations.get(conversation_id, [])
        
        if not entries:
            return []
        
        # Generate embedding for query
        query_embedding = await self.embedding_manager.embed(query)
        
        # Calculate similarity scores
        scored_entries = []
        for entry in entries:
            if entry.embedding:
                score = self.embedding_manager.cosine_similarity(
                    query_embedding, entry.embedding
                )
            else:
                # Fallback to text-based similarity
                score = self._text_similarity(query, entry.content)
            
            scored_entries.append((entry, score))
        
        # Sort by score
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        # Return top entries
        return [entry for entry, score in scored_entries[:limit]]
    
    async def summarize_conversation(
        self,
        conversation_id: str,
        max_length: int = 500,
    ) -> str:
        """
        Generate a summary of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            max_length: Maximum length of the summary
        
        Returns:
            Summary text
        """
        entries = await self.get_conversation_memory(conversation_id)
        
        if not entries:
            return ""
        
        # Simple summary: concatenate user messages
        summary = ""
        for entry in entries:
            if entry.role == "user":
                summary += entry.content + " "
        
        # Truncate to max length
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary.strip()
    
    async def compress_memory(
        self,
        conversation_id: str,
        threshold: int = 100,
    ) -> int:
        """
        Compress memory by summarizing old entries.
        
        Args:
            conversation_id: ID of the conversation
            threshold: Number of entries to keep before compressing
        
        Returns:
            Number of entries compressed
        """
        entries = self._conversations.get(conversation_id, [])
        
        if len(entries) <= threshold:
            return 0
        
        # Get old entries (all except the last threshold)
        old_entries = entries[:-threshold]
        new_entries = entries[-threshold:]
        
        # Summarize old entries
        summary = await self.summarize_conversation(conversation_id)
        
        # Create summary entry
        summary_entry = MemoryEntry(
            id=self._generate_id(summary),
            content=f"[Memory Compression] Previous conversation summary: {summary}",
            role="system",
            timestamp=datetime.utcnow(),
            metadata={"compressed": True, "original_count": len(old_entries)},
        )
        
        # Replace old entries with summary
        self._conversations[conversation_id] = [summary_entry] + new_entries
        
        return len(old_entries)
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all memory for a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    async def delete_message(
        self,
        conversation_id: str,
        message_id: str,
    ) -> bool:
        """Delete a specific message from memory."""
        entries = self._conversations.get(conversation_id, [])
        
        for i, entry in enumerate(entries):
            if entry.id == message_id:
                del entries[i]
                return True
        
        return False
    
    async def update_message(
        self,
        conversation_id: str,
        message_id: str,
        new_content: str,
    ) -> bool:
        """Update a message in memory."""
        entries = self._conversations.get(conversation_id, [])
        
        for entry in entries:
            if entry.id == message_id:
                entry.content = new_content
                entry.timestamp = datetime.utcnow()
                return True
        
        return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        total_entries = sum(len(entries) for entries in self._conversations.values())
        total_conversations = len(self._conversations)
        
        return {
            "total_entries": total_entries,
            "total_conversations": total_conversations,
            "max_context_tokens": self.max_context_tokens,
            "max_memory_entries": self.max_memory_entries,
            "short_term_memory_size": self.short_term_memory_size,
            "long_term_memory_size": self.long_term_memory_size,
        }
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for a memory entry."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _trim_memory(self, conversation_id: str):
        """Trim memory to maximum size."""
        entries = self._conversations.get(conversation_id, [])
        
        if len(entries) > self.max_memory_entries:
            # Compress old entries
            await self.compress_memory(conversation_id, self.max_memory_entries // 2)
    
    def _estimate_token_count(self, entries: List[MemoryEntry]) -> int:
        """Estimate token count for a list of entries."""
        return sum(self._estimate_token_count_for_text(e.content) for e in entries)
    
    def _estimate_token_count_from_messages(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count from a list of messages."""
        return sum(
            self._estimate_token_count_for_text(msg.get("content", ""))
            for msg in messages
        )
    
    def _estimate_token_count_for_text(self, text: str) -> int:
        """Estimate token count for a text string."""
        return int(len(text) * self._token_per_char)
    
    def _trim_messages_to_tokens(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
    ) -> List[Dict[str, Any]]:
        """Trim messages to fit within a token budget."""
        trimmed = []
        current_tokens = 0
        
        # Start from the beginning (oldest messages)
        for msg in messages:
            msg_tokens = self._estimate_token_count_for_text(msg.get("content", ""))
            
            if current_tokens + msg_tokens <= max_tokens:
                trimmed.append(msg)
                current_tokens += msg_tokens
            else:
                # Try to add at least the system message
                if msg.get("role") == "system":
                    trimmed.append(msg)
                    current_tokens += msg_tokens
        
        return trimmed
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple string matching."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    async def _save_to_database(
        self,
        conversation_id: str,
        entry: MemoryEntry,
    ):
        """Save a memory entry to the database."""
        try:
            async with get_async_db_session() as session:
                # Find or create conversation
                conv = await session.get(Conversation, conversation_id)
                
                if not conv:
                    conv = Conversation(id=conversation_id)
                    session.add(conv)
                
                # Create message
                msg = Message(
                    id=entry.id,
                    conversation_id=conversation_id,
                    role=entry.role,
                    content=entry.content,
                    extra_info=entry.metadata,
                )
                
                session.add(msg)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
    
    async def load_from_database(self, conversation_id: str):
        """Load memory entries from the database."""
        try:
            async with get_async_db_session() as session:
                result = await session.execute(
                    Message.__table__.select()
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                )
                
                messages = result.scalars().all()
                
                entries = []
                for msg in messages:
                    entry = MemoryEntry(
                        id=msg.id,
                        content=msg.content,
                        role=msg.role,
                        timestamp=msg.created_at,
                        extra_info=msg.extra_info or {},
                    )
                    entries.append(entry)
                
                self._conversations[conversation_id] = entries
                
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
