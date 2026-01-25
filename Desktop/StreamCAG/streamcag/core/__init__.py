import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from ..cache import PersistentCache, SemanticCache
from ..optimizer import ContextOptimizer


@dataclass
class StreamCAGConfig:
    """Configuration for StreamCAG system."""

    model_name: str = "mistralai/Mistral-7B-Instruct-v0.1"
    cache_max_size: int = 1000
    use_l2_cache: bool = True
    cache_storage_path: str = "./streamcag_cache"
    optimize_context: bool = True
    target_context_tokens: int = 2048
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    use_4bit_quantization: bool = True


class StreamCAG:
    """Main StreamCAG system orchestrating cache management and LLM interaction."""

    def __init__(self, config: Optional[StreamCAGConfig] = None):
        self.config = config or StreamCAGConfig()

        # Initialize components
        self.model = None
        self.tokenizer = None
        self.l1_cache = SemanticCache(max_size=self.config.cache_max_size // 2)
        self.l2_cache = (
            PersistentCache(
                storage_path=self.config.cache_storage_path,
                max_size=self.config.cache_max_size,
            )
            if self.config.use_l2_cache
            else None
        )
        self.optimizer = ContextOptimizer()

        # Load model
        self._load_model()

        # Statistics
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "tokens_saved": 0,
            "avg_response_time": 0,
            "total_context_tokens": 0,
            "optimized_context_tokens": 0,
        }

    def _load_model(self):
        """Load the LLM model and tokenizer."""
        print(f"Loading model: {self.config.model_name}")

        # Configure quantization if enabled
        if self.config.use_4bit_quantization and self.config.device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            bnb_config = None

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name, padding_side="left"
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            quantization_config=bnb_config,
            torch_dtype=torch.float16 if self.config.device == "cuda" else torch.float32,
            device_map="auto" if self.config.device == "cuda" else None,
            low_cpu_mem_usage=True,
        )

        print(f"Model loaded successfully on {self.config.device}")

    def preload_knowledge(self, documents: List[str], metadata: Optional[List[Dict]] = None):
        """Preload knowledge documents into the cache."""
        print(f"Preloading {len(documents)} documents into cache...")

        for i, doc in enumerate(documents):
            meta = metadata[i] if metadata and i < len(metadata) else {"source": f"doc_{i}"}

            # Add to L2 cache (persistent)
            if self.l2_cache:
                self.l2_cache.add(doc, meta)

            # Also add to L1 cache for immediate access
            self.l1_cache.add(doc, meta)

        print(f"Knowledge preloaded. L1 cache size: {len(self.l1_cache.entries)}")
        if self.l2_cache:
            print(f"L2 cache size: {len(self.l2_cache.entries)}")

    def query(self, question: str, use_cache: bool = True, max_new_tokens: int = 512) -> Dict:
        """
        Process a query with intelligent cache usage.

        Args:
            question: User question
            use_cache: Whether to use cache augmentation
            max_new_tokens: Maximum tokens in response

        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        self.stats["total_queries"] += 1

        # Step 1: Search in caches
        cache_results = []
        if use_cache:
            # Search L1 cache first
            l1_results = self.l1_cache.search(question, k=3)
            cache_results.extend(l1_results)

            # Search L2 cache if available
            if self.l2_cache:
                l2_results = self.l2_cache.search(question, k=5)
                cache_results.extend(l2_results)

        # Step 2: Prepare context
        context_parts = []
        if cache_results:
            self.stats["cache_hits"] += 1

            # Sort by similarity score
            cache_results.sort(key=lambda x: x[1], reverse=True)

            # Build context from cache hits
            for entry, score in cache_results[:5]:  # Top 5 hits
                context_parts.append(
                    f"[Relevant knowledge: {entry.metadata.get('source', 'cache')}]"
                )
                context_parts.append(entry.text)

        # Step 3: Optimize context if too long
        full_context = "\n\n".join(context_parts) if context_parts else ""

        if self.config.optimize_context and full_context:
            optimization = self.optimizer.compress_context(
                full_context, self.config.target_context_tokens, question
            )

            optimized_context = optimization.compressed_text
            self.stats["total_context_tokens"] += optimization.original_tokens
            self.stats["optimized_context_tokens"] += optimization.compressed_tokens
            self.stats["tokens_saved"] += (
                optimization.original_tokens - optimization.compressed_tokens
            )
        else:
            optimized_context = full_context

        # Step 4: Prepare prompt
        if optimized_context:
            prompt = f"""Based on the following context, answer the question.

Context:
{optimized_context}

Question: {question}

Answer:"""
        else:
            prompt = f"Question: {question}\n\nAnswer:"

        # Step 5: Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")

        if self.config.device == "cuda":
            inputs = {k: v.to(self.config.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                top_p=0.95,
                repetition_penalty=1.1,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the answer part
        answer = response.split("Answer:")[-1].strip()

        # Step 6: Update caches with new knowledge
        if len(answer.split()) > 10:  # Only cache substantial answers
            metadata = {"source": "generated", "question": question, "timestamp": time.time()}
            self.l1_cache.add(answer, metadata)
            if self.l2_cache:
                self.l2_cache.add(answer, metadata)

        # Step 7: Calculate metrics
        response_time = time.time() - start_time
        self.stats["avg_response_time"] = (
            (
                self.stats["avg_response_time"] * (self.stats["total_queries"] - 1)
                + response_time
            )
            / self.stats["total_queries"]
        )

        # Prepare result
        result = {
            "question": question,
            "answer": answer,
            "context_used": bool(cache_results),
            "cache_hits": len(cache_results),
            "response_time": response_time,
            "optimization_stats": {
                "context_tokens_before": self.optimizer.tokenizer.encode(full_context)
                if full_context
                else 0,
                "context_tokens_after": len(self.optimizer.tokenizer.encode(optimized_context))
                if optimized_context
                else 0,
            }
            if self.config.optimize_context
            else None,
            "cache_stats": self.l1_cache.get_stats(),
        }

        if self.l2_cache:
            result["l2_cache_stats"] = self.l2_cache.get_stats()

        return result

    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics."""
        stats = self.stats.copy()
        stats.update(
            {
                "cache_hit_rate": stats["cache_hits"]
                / max(1, stats["total_queries"]),
                "token_savings_percentage": (
                    stats["tokens_saved"] / max(1, stats["total_context_tokens"]) * 100
                    if stats["total_context_tokens"] > 0
                    else 0
                ),
                "compression_ratio": (
                    stats["optimized_context_tokens"]
                    / max(1, stats["total_context_tokens"])
                    if stats["total_context_tokens"] > 0
                    else 1.0
                ),
            }
        )

        # Add cache statistics
        stats["l1_cache"] = self.l1_cache.get_stats()
        if self.l2_cache:
            stats["l2_cache"] = self.l2_cache.get_stats()

        return stats

    def save_caches(self):
        """Persist all caches to disk."""
        if self.l2_cache:
            self.l2_cache.save()

        # Also save L1 cache hot entries to L2
        for entry in self.l1_cache.entries.values():
            if entry.access_count > 2:  # Frequently accessed
                if self.l2_cache:
                    self.l2_cache.add(entry.text, entry.metadata)

        print("Caches saved successfully")

    def clear_caches(self, l1: bool = True, l2: bool = True):
        """Clear cache contents."""
        if l1:
            self.l1_cache.entries.clear()
            self.l1_cache.index = None
            self.l1_cache.id_to_index = {}
            print("L1 cache cleared")

        if l2 and self.l2_cache:
            self.l2_cache.entries.clear()
            self.l2_cache.index = None
            self.l2_cache.id_to_index = {}
            print("L2 cache cleared")
