import json
from datetime import datetime

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np

from streamcag import StreamCAG, StreamCAGConfig


class StreamCAGWeb:
    def __init__(self):
        self.cag = None
        self.history = []

    def initialize_system(self, model_name, use_4bit, cache_size, optimize_context):
        """Initialize StreamCAG system."""
        try:
            config = StreamCAGConfig(
                model_name=model_name,
                use_4bit_quantization=use_4bit,
                cache_max_size=int(cache_size),
                optimize_context=optimize_context,
            )
            self.cag = StreamCAG(config)
            return "StreamCAG initialized successfully."
        except Exception as e:
            return f"Error: {str(e)}"

    def process_query(self, query, use_cache):
        """Process a user query."""
        if not self.cag:
            return "Please initialize the system first.", None, None

        try:
            result = self.cag.query(query, use_cache=use_cache)

            # Add to history
            self.history.append(
                {"timestamp": datetime.now().isoformat(), "query": query, "result": result}
            )

            stats = self.cag.get_system_stats()

            metrics = {
                "Response Time": f"{result['response_time']:.2f}s",
                "Cache Used": "Yes" if result["context_used"] else "No",
                "Cache Hits": result["cache_hits"],
                "Total Queries": stats["total_queries"],
                "Cache Hit Rate": f"{stats['cache_hit_rate']*100:.1f}%",
                "Token Savings": f"{stats.get('token_savings_percentage', 0):.1f}%",
            }

            metrics_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])

            return result["answer"], metrics_text, self.create_plot(stats)

        except Exception as e:
            return f"Error: {str(e)}", None, None

    def create_plot(self, stats):
        """Create performance visualization."""
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        # Cache performance
        cache_labels = ["Hits", "Misses"]
        cache_values = [stats["cache_hits"], stats["total_queries"] - stats["cache_hits"]]
        axes[0].pie(
            cache_values,
            labels=cache_labels,
            autopct="%1.1f%%",
            colors=["#4CAF50", "#F44336"],
        )
        axes[0].set_title("Cache Performance")

        # Token savings
        if "token_savings_percentage" in stats:
            savings = stats["token_savings_percentage"]
            axes[1].bar(["Token Savings"], [savings], color="#2196F3")
            axes[1].set_ylim(0, 100)
            axes[1].set_ylabel("Percentage (%)")
            axes[1].set_title("Token Savings")

        plt.tight_layout()
        return fig

    def launch(self):
        """Launch the web interface."""
        with gr.Blocks(title="StreamCAG Demo", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# StreamCAG: Streamlined Cache-Augmented Generation")
            gr.Markdown("Intelligent caching for LLMs with real-time optimization")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("Configuration")

                    model_name = gr.Dropdown(
                        choices=[
                            "mistralai/Mistral-7B-Instruct-v0.1",
                            "gpt2",
                            "facebook/opt-1.3b",
                        ],
                        value="gpt2",
                        label="Model",
                    )

                    use_4bit = gr.Checkbox(value=True, label="Use 4-bit Quantization")
                    cache_size = gr.Slider(100, 5000, value=1000, step=100, label="Cache Size")
                    optimize_context = gr.Checkbox(value=True, label="Optimize Context")

                    init_btn = gr.Button("Initialize System", variant="primary")
                    init_output = gr.Textbox(label="Initialization Status")

                with gr.Column(scale=2):
                    gr.Markdown("Chat Interface")

                    chatbot = gr.Chatbot(label="StreamCAG", height=400)
                    query_input = gr.Textbox(label="Your Question", placeholder="Ask me anything...")

                    with gr.Row():
                        use_cache = gr.Checkbox(value=True, label="Use Cache")
                        submit_btn = gr.Button("Submit", variant="primary")

                    gr.Markdown("Performance Metrics")
                    metrics_output = gr.Textbox(label="Current Query Metrics")
                    plot_output = gr.Plot(label="System Performance")

            # Event handlers
            init_btn.click(
                self.initialize_system,
                inputs=[model_name, use_4bit, cache_size, optimize_context],
                outputs=init_output,
            )

            def respond(message, chat_history, use_cache):
                answer, metrics, plot = self.process_query(message, use_cache)
                chat_history.append((message, answer))
                return "", chat_history, metrics, plot

            query_input.submit(
                respond,
                inputs=[query_input, chatbot, use_cache],
                outputs=[query_input, chatbot, metrics_output, plot_output],
            )

            submit_btn.click(
                respond,
                inputs=[query_input, chatbot, use_cache],
                outputs=[query_input, chatbot, metrics_output, plot_output],
            )

        demo.launch(share=False)


def main():
    web_app = StreamCAGWeb()
    web_app.launch()


if __name__ == "__main__":
    main()
