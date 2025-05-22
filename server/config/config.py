import os
import yaml
from sentence_transformers import SentenceTransformer

CONFIG_PATH = os.getenv("CONFIG_PATH", "config/config.yaml")


def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"加载配置文件时发生错误: {str(e)}")
        return None


config = load_config()

model = SentenceTransformer(
    config.get("model_name", "paraphrase-multilingual-MiniLM-L12-v2")
)
