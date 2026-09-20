from core.classification.config import config

print("Classification API key loaded:", bool(config.api_key))
print("Classification model:", config.llm_model_name)