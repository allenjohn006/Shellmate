FREE = [
    {"id": "google/gemini-2.0-flash-exp:free", "provider": "Google", "speed": "fast", "best_for": "general suggestions"},
    {"id": "deepseek/deepseek-r1:free", "provider": "DeepSeek", "speed": "medium", "best_for": "complex reasoning, agent mode"},
    {"id": "meta-llama/llama-3.1-8b-instruct:free", "provider": "Meta", "speed": "very fast", "best_for": "quick commands"},
    {"id": "mistralai/mistral-7b-instruct:free", "provider": "Mistral", "speed": "fast", "best_for": "instruction following"},
    {"id": "qwen/qwen-2.5-72b-instruct:free", "provider": "Alibaba", "speed": "medium", "best_for": "large context tasks"},
]

PAID = [
    {"id": "anthropic/claude-sonnet-4-6", "provider": "Anthropic", "speed": "fast", "best_for": "best overall quality"},
    {"id": "openai/gpt-4o", "provider": "OpenAI", "speed": "fast", "best_for": "general purpose"},
    {"id": "google/gemini-1.5-pro", "provider": "Google", "speed": "medium", "best_for": "long context"},
]

def get_all_models():
    return FREE + PAID

def get_model_by_id(model_id: str):
    for model in get_all_models():
        if model["id"] == model_id:
            return model
    return None
