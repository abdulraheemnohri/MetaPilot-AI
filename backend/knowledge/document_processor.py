"""
Document Processor for MetaPilot AI

Processes documents by extracting text, chunking, and preparing for embedding.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
import hashlib

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A chunk of text from a document."""
    text: str
    start_index: int
    end_index: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DocumentProcessor:
    """
    Processes documents for the knowledge base.
    
    Features:
    - Text extraction from various file formats
    - Chunking with configurable parameters
    - Text cleaning and normalization
    - Metadata extraction
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self._text_extractors = {
            ".txt": self._extract_text,
            ".md": self._extract_text,
            ".markdown": self._extract_text,
            ".json": self._extract_json,
            ".csv": self._extract_csv,
            ".pdf": self._extract_pdf,
            ".docx": self._extract_docx,
        }
    
    def process_file(self, file_path: Union[str, Path]) -> List[TextChunk]:
        """
        Process a file and extract text chunks.
        
        Args:
            file_path: Path to the file
        
        Returns:
            List of TextChunk objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text based on file type
        text = self._extract_text_from_file(file_path)
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        return chunks
    
    def extract_text(self, file_path: Union[str, Path]) -> str:
        """
        Extract raw text from a file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Extracted text
        """
        return self._extract_text_from_file(file_path)
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: The text to chunk
            chunk_size: Size of each chunk (in characters)
            overlap: Overlap between chunks (in characters)
        
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        
        if chunk_size <= 0:
            return [text]
        
        # First, split by separator if possible
        if self.separator:
            paragraphs = text.split(self.separator)
            chunks = []
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) + len(self.separator) <= chunk_size:
                    current_chunk += para + self.separator
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + self.separator
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If chunks are still too large, split them further
            final_chunks = []
            for chunk in chunks:
                if len(chunk) > chunk_size:
                    final_chunks.extend(self._split_chunk(chunk, chunk_size, overlap))
                else:
                    final_chunks.append(chunk)
            
            return final_chunks
        else:
            # Simple character-based splitting
            return self._split_chunk(text, chunk_size, overlap)
    
    def _split_chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split a chunk of text into smaller chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            
            # Try to split at a sentence boundary
            if end < len(text):
                # Look for the last period, exclamation, or question mark
                last_punct = max(
                    chunk.rfind("."),
                    chunk.rfind("!"),
                    chunk.rfind("?"),
                )
                
                if last_punct > chunk_size * 0.8:  # Only split if we found a good boundary
                    end = start + last_punct + 1
                    chunk = text[start:end]
            
            chunks.append(chunk)
            start = end - overlap if overlap > 0 else end
        
        return chunks
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from a file based on its extension."""
        ext = file_path.suffix.lower()
        
        if ext in self._text_extractors:
            return self._text_extractors[ext](file_path)
        
        # Try to read as text
        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from text files."""
        return file_path.read_text(encoding="utf-8", errors="replace")
    
    def _extract_json(self, file_path: Path) -> str:
        """Extract text from JSON files."""
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            return file_path.read_text(encoding="utf-8", errors="replace")
    
    def _extract_csv(self, file_path: Path) -> str:
        """Extract text from CSV files."""
        try:
            import csv
            
            with file_path.open(encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                text = ""
                for row in reader:
                    text += ", ".join(row) + "\n"
                return text
        except Exception:
            return file_path.read_text(encoding="utf-8", errors="replace")
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF files."""
        try:
            from pdfminer.high_level import extract_text
            return extract_text(str(file_path))
        except ImportError:
            logger.warning("pdfminer.six not installed, PDF extraction not available")
            return ""
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return ""
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX files."""
        try:
            from docx import Document
            
            doc = Document(str(file_path))
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            logger.warning("python-docx not installed, DOCX extraction not available")
            return ""
        except Exception as e:
            logger.error(f"Failed to extract DOCX text: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary with file metadata
        """
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_extension": file_path.suffix.lower(),
            "file_type": self._get_file_type(file_path),
        }
        
        # Add file hash
        try:
            with file_path.open("rb") as f:
                content = f.read()
                metadata["file_hash"] = hashlib.sha256(content).hexdigest()
        except Exception:
            pass
        
        return metadata
    
    def _get_file_type(self, file_path: Path) -> str:
        """Get file type from extension."""
        ext = file_path.suffix.lower()
        if ext in [".txt", ".md", ".markdown"]:
            return "text"
        elif ext == ".pdf":
            return "pdf"
        elif ext in [".doc", ".docx"]:
            return "word"
        elif ext == ".json":
            return "json"
        elif ext == ".csv":
            return "csv"
        else:
            return "unknown"
    
    def remove_stopwords(self, text: str, language: str = "english") -> str:
        """
        Remove stopwords from text.
        
        Args:
            text: The text to process
            language: Language for stopwords
        
        Returns:
            Text with stopwords removed
        """
        try:
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            
            stop_words = set(stopwords.words(language))
            words = word_tokenize(text.lower())
            filtered_words = [word for word in words if word not in stop_words]
            return ' '.join(filtered_words)
        except ImportError:
            logger.warning("nltk not installed, stopword removal not available")
            return text
        except Exception:
            return text
    
    def lemmatize(self, text: str, language: str = "english") -> str:
        """
        Lemmatize text.
        
        Args:
            text: The text to process
            language: Language for lemmatization
        
        Returns:
            Lemmatized text
        """
        try:
            from nltk.stem import WordNetLemmatizer
            from nltk.tokenize import word_tokenize
            
            lemmatizer = WordNetLemmatizer()
            words = word_tokenize(text)
            lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
            return ' '.join(lemmatized_words)
        except ImportError:
            logger.warning("nltk not installed, lemmatization not available")
            return text
        except Exception:
            return text
    
    def preprocess_for_embedding(self, text: str) -> str:
        """
        Preprocess text for embedding.
        
        Args:
            text: The text to preprocess
        
        Returns:
            Preprocessed text
        """
        # Clean text
        text = self._clean_text(text)
        
        # Remove stopwords
        text = self.remove_stopwords(text)
        
        # Lemmatize
        text = self.lemmatize(text)
        
        return text
