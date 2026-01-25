import re
from typing import List, Dict, Tuple
import numpy as np
from collections import Counter
import spacy
from dataclasses import dataclass
from transformers import AutoTokenizer

@dataclass
class OptimizationResult:
    """Result of context optimization."""
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    preserved_entities: List[str]
    removed_sections: List[str]

class ContextOptimizer:
    """Intelligent context compression and optimization."""
    
    def __init__(self, model_name: str = "gpt2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Try to load spaCy for NLP features
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            print("spaCy not available. Installing with: pip install spacy && python -m spacy download en_core_web_sm")
        
        # Compression strategies with weights
        self.strategies = {
            "remove_redundant": 0.3,
            "summarize_long": 0.4,
            "extract_key_points": 0.2,
            "remove_formatting": 0.1
        }
    
    def compress_context(self, 
                        text: str, 
                        target_tokens: int,
                        query: str = None) -> OptimizationResult:
        """
        Intelligently compress context while preserving meaning.
        
        Args:
            text: Original context text
            target_tokens: Maximum tokens after compression
            query: Optional query to guide compression
        
        Returns:
            OptimizationResult with compressed text and metrics
        """
        # Tokenize to check current size
        original_tokens = len(self.tokenizer.encode(text))
        
        if original_tokens <= target_tokens:
            # No compression needed
            return OptimizationResult(
                compressed_text=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                preserved_entities=[],
                removed_sections=[]
            )
        
        # Apply compression strategies based on content type
        compressed = text
        removed_sections = []
        
        # Strategy 1: Remove redundant information
        if self.strategies["remove_redundant"] > 0:
            compressed, removed = self._remove_redundancy(compressed)
            removed_sections.extend(removed)
        
        # Strategy 2: Summarize long paragraphs
        if self.strategies["summarize_long"] > 0:
            compressed = self._summarize_long_passages(compressed)
        
        # Strategy 3: Extract key points if query provided
        if query and self.strategies["extract_key_points"] > 0:
            compressed = self._extract_relevant_points(compressed, query)
        
        # Strategy 4: Remove excessive formatting
        if self.strategies["remove_formatting"] > 0:
            compressed = self._remove_excessive_formatting(compressed)
        
        # If still too long, apply aggressive compression
        compressed_tokens = len(self.tokenizer.encode(compressed))
        if compressed_tokens > target_tokens:
            compressed = self._aggressive_compression(compressed, target_tokens)
            compressed_tokens = len(self.tokenizer.encode(compressed))
        
        # Extract preserved entities
        preserved_entities = self._extract_entities(compressed)
        
        return OptimizationResult(
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / max(1, original_tokens),
            preserved_entities=preserved_entities,
            removed_sections=removed_sections[:5]  # Limit to top 5
        )
    
    def _remove_redundancy(self, text: str) -> Tuple[str, List[str]]:
        """Remove duplicate sentences and phrases."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        unique_sentences = []
        seen_content = set()
        removed = []
        
        for sentence in sentences:
            # Create a simplified version for comparison
            simplified = sentence.lower().strip()
            simplified = re.sub(r'\s+', ' ', simplified)
            
            # Check if we've seen similar content
            is_redundant = False
            for seen in seen_content:
                if self._calculate_similarity(simplified, seen) > 0.8:
                    is_redundant = True
                    removed.append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
                    break
            
            if not is_redundant and len(sentence.strip()) > 10:
                unique_sentences.append(sentence)
                seen_content.add(simplified[:100])  # Store first 100 chars
        
        return ' '.join(unique_sentences), removed
    
    def _summarize_long_passages(self, text: str) -> str:
        """Summarize long paragraphs using extractive methods."""
        paragraphs = text.split('\n\n')
        summarized = []
        
        for para in paragraphs:
            if len(para.split()) > 100:  # Long paragraph
                sentences = re.split(r'(?<=[.!?])\s+', para)
                if len(sentences) > 3:
                    # Keep first, middle, and last sentences for long paragraphs
                    important_indices = [0, len(sentences)//2, -1]
                    key_sentences = [sentences[i] for i in important_indices if i < len(sentences)]
                    summarized.append(' '.join(key_sentences))
                else:
                    summarized.append(para)
            else:
                summarized.append(para)
        
        return '\n\n'.join(summarized)
    
    def _extract_relevant_points(self, text: str, query: str) -> str:
        """Extract points most relevant to the query."""
        if not self.nlp:
            return text
        
        query_doc = self.nlp(query.lower())
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by relevance to query
        scored_sentences = []
        for sentence in sentences:
            sentence_doc = self.nlp(sentence.lower())
            
            # Simple relevance scoring
            relevance = 0
            for token1 in query_doc:
                for token2 in sentence_doc:
                    if token1.text == token2.text:
                        relevance += 1
                    elif token1.similarity(token2) > 0.7:
                        relevance += token1.similarity(token2)
            
            scored_sentences.append((sentence, relevance))
        
        # Sort by relevance and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s for s, _ in scored_sentences[:max(10, len(scored_sentences)//2)]]
        
        return ' '.join(top_sentences)
    
    def _remove_excessive_formatting(self, text: str) -> str:
        """Clean up excessive whitespace and formatting."""
        # Replace multiple newlines with single newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        # Remove markdown formatting if present
        text = re.sub(r'#{1,6}\s*', '', text)  # Headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
        return text.strip()
    
    def _aggressive_compression(self, text: str, target_tokens: int) -> str:
        """Apply aggressive compression when needed."""
        # Tokenize and keep only most important tokens
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= target_tokens:
            return text
        
        # Simple heuristic: keep beginning, middle, and end
        keep_ratio = target_tokens / len(tokens)
        keep_start = int(len(tokens) * keep_ratio * 0.3)
        keep_middle = int(len(tokens) * keep_ratio * 0.4)
        keep_end = int(len(tokens) * keep_ratio * 0.3)
        
        kept_tokens = (
            tokens[:keep_start] + 
            tokens[len(tokens)//2 - keep_middle//2:len(tokens)//2 + keep_middle//2] + 
            tokens[-keep_end:]
        )
        
        return self.tokenizer.decode(kept_tokens)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        if not self.nlp or not text:
            return []
        
        try:
            doc = self.nlp(text[:1000])  # Limit for speed
            entities = set()
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']:
                    entities.add(ent.text)
            return list(entities)[:10]  # Limit to 10 entities
        except:
            return []
    
    def adaptive_chunking(self, 
                         text: str, 
                         query_complexity: float = 0.5) -> List[str]:
        """
        Dynamically adjust chunk size based on content complexity.
        
        Args:
            text: Input text to chunk
            query_complexity: 0-1 score of query complexity
        
        Returns:
            List of optimally sized chunks
        """
        # Calculate optimal chunk size based on complexity
        base_chunk_size = 512
        if query_complexity > 0.7:
            chunk_size = int(base_chunk_size * 0.7)  # Smaller for complex queries
        elif query_complexity < 0.3:
            chunk_size = int(base_chunk_size * 1.3)  # Larger for simple queries
        else:
            chunk_size = base_chunk_size
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(self.tokenizer.encode(para))
            
            if para_length > chunk_size:
                # Paragraph too long, split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sent_length = len(self.tokenizer.encode(sentence))
                    if current_length + sent_length > chunk_size and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = [sentence]
                        current_length = sent_length
                    else:
                        current_chunk.append(sentence)
                        current_length += sent_length
            else:
                if current_length + para_length > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [para]
                    current_length = para_length
                else:
                    current_chunk.append(para)
                    current_length += para_length
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
