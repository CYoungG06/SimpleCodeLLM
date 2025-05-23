import yaml
from typing import Dict, Any, Optional
import logging


class Config:

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            return {}

    
    def get(self, path: str, default: Any = None) -> Any:
        current = self.config
        for key in path.split('.'):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current
    

    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        return self.get(f"llm.{provider}", {})
    

    def get_api_key(self, provider: str) -> Optional[str]:
        return self.get(f"llm.{provider}.api_key")
    

    def get_base_url(self, provider: str) -> Optional[str]:
        return self.get(f"llm.{provider}.base_url")
    
    
    def get_model(self, provider: str) -> Optional[str]:
        return self.get(f"llm.{provider}.model")


    def get_search_key(self) -> Optional[str]:
        return self.get("tool.search.api_key")
        
    