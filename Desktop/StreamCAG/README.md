## Quick Start

```python
from streamcag import StreamCAG, StreamCAGConfig

# Configure system
config = StreamCAGConfig(
    model_name="mistralai/Mistral-7B-Instruct-v0.1",
    cache_max_size=1000,
    optimize_context=True
)

# Initialize
cag = StreamCAG(config)

# Preload knowledge
knowledge = [
    "Paris is the capital of France.",
    "Machine learning is a subset of artificial intelligence."
]
cag.preload_knowledge(knowledge)

# Query with intelligent caching
result = cag.query("What is the capital of France?")
print(result['answer'])
```

## StreamCAG Architecture

```

## Configuration

Customize StreamCAG through the configuration object:

```python
config = StreamCAGConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    cache_max_size=2000,
    target_context_tokens=2048,
    use_4bit_quantization=True,
    cache_storage_path="./my_cache",
    optimize_context=True
)
```
StreamCAG Architecture
├── Layer 1: Query Interface
│   ├── Intent Detection
│   └── Context Optimization
├── Layer 2: Semantic Cache Manager
│   ├── L1 Cache (In-memory)
│   ├── L2 Cache (Persistent)
│   └── Cache Coherence Engine
├── Layer 3: LLM Integration
│   ├── Multi-Model Support
│   ├── Prompt Engineering
│   └── Response Generation
└── Layer 4: Storage & Analytics
    ├── Vector Storage
    ├── Performance Metrics
    └── Cache Persistence
```
