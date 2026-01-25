import json
import yaml
import pickle
from typing import Any, Dict, List
import pandas as pd
from datetime import datetime

def save_json(data: Any, filepath: str):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_pickle(data: Any, filepath: str):
    """Save data to pickle file."""
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

def load_pickle(filepath: str) -> Any:
    """Load data from pickle file."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

class StreamCAGLogger:
    """Logging utility for StreamCAG."""
    
    def __init__(self, log_file: str = "streamcag.log"):
        self.log_file = log_file
        self.logs = []
    
    def log(self, 
            level: str, 
            message: str, 
            data: Dict = None,
            save_immediately: bool = False):
        """Log a message with metadata."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        self.logs.append(log_entry)
        
        # Print to console
        print(f"[{level.upper()}] {message}")
        
        # Save to file if requested
        if save_immediately:
            self.save_logs()
    
    def save_logs(self):
        """Save all logs to file."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            for log in self.logs[-100:]:  # Keep last 100 logs
                f.write(json.dumps(log) + '\n')
        
        # Clear logs after saving
        self.logs = self.logs[-100:]  # Keep last 100 in memory
    
    def get_recent_logs(self, n: int = 10) -> List[Dict]:
        """Get recent log entries."""
        return self.logs[-n:]

def create_benchmark_dataset(n_samples: int = 100) -> List[Dict]:
    """Create a benchmark dataset for testing."""
    import random
    
    questions = [
        "What is the capital of France?",
        "Explain the theory of relativity in simple terms.",
        "What are the benefits of regular exercise?",
        "How does photosynthesis work?",
        "What is machine learning and how is it different from AI?",
        "Describe the water cycle.",
        "What causes seasons on Earth?",
        "How do vaccines work?",
        "What is blockchain technology?",
        "Explain quantum computing basics."
    ]
    
    # Create knowledge base
    knowledge_base = [
        "Paris is the capital and largest city of France.",
        "Regular exercise improves cardiovascular health and reduces stress.",
        "Photosynthesis is the process by which plants convert sunlight into energy.",
        "Machine learning is a subset of AI focused on algorithms that learn from data.",
        "The water cycle involves evaporation, condensation, and precipitation.",
        "Earth's seasons are caused by the tilt of its axis relative to its orbit.",
        "Vaccines work by training the immune system to recognize and fight pathogens.",
        "Blockchain is a decentralized digital ledger technology.",
        "Quantum computing uses quantum bits that can exist in multiple states simultaneously."
    ]
    
    dataset = []
    for i in range(min(n_samples, len(questions))):
        dataset.append({
            "id": i + 1,
            "question": questions[i % len(questions)],
            "expected_context": knowledge_base[i % len(knowledge_base)],
            "complexity": random.uniform(0.3, 0.9)
        })
    
    return dataset

def analyze_results(results: List[Dict]) -> pd.DataFrame:
    """Analyze and summarize benchmark results."""
    df = pd.DataFrame(results)
    
    if df.empty:
        return df
    
    # Calculate statistics
    summary = {
        "Total Queries": len(df),
        "Avg Response Time": df['response_time'].mean(),
        "Cache Hit Rate": df['context_used'].mean(),
        "Avg Cache Hits": df['cache_hits'].mean(),
    }
    
    # Add optimization stats if available
    if 'optimization_stats' in df.columns and df['optimization_stats'].notna().any():
        opt_stats = df['optimization_stats'].dropna().tolist()
        if opt_stats:
            before_tokens = [s.get('context_tokens_before', 0) for s in opt_stats]
            after_tokens = [s.get('context_tokens_after', 0) for s in opt_stats]
            
            summary["Avg Tokens Before"] = sum(before_tokens) / len(before_tokens)
            summary["Avg Tokens After"] = sum(after_tokens) / len(after_tokens)
            summary["Token Savings %"] = (1 - (sum(after_tokens) / sum(before_tokens))) * 100
    
    return pd.DataFrame([summary])
