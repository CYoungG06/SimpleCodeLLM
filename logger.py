import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import Config


class MessageLogger:
    def __init__(self, config: Config):
        self.config = config
        self.session_id = self._generate_session_id()
        self.session_start_time = datetime.now()
        self.messages_log = []
        self.log_enabled = config.get("logging.enabled", True)
        self.save_path = config.get("logging.save_path", "logs/")
        self.log_format = config.get("logging.format", "json")
        self.include_tool_calls = config.get("logging.include_tool_calls", True)
        self.include_responses = config.get("logging.include_responses", True)
        
        # Create logs directory if it doesn't exist
        if self.log_enabled:
            os.makedirs(self.save_path, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"
    
    def log_message(self, message: Dict[str, Any], message_type: str = "chat"):
        """Log a single message"""
        if not self.log_enabled:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "message_type": message_type,
            "content": message
        }
        
        self.messages_log.append(log_entry)
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Any):
        """Log tool call and result"""
        if not self.log_enabled or not self.include_tool_calls:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "message_type": "tool_call",
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result
        }
        
        self.messages_log.append(log_entry)
    
    def log_session_start(self, user_prompt: str, system_prompt: str, provider: str, model: str):
        """Log session start information"""
        if not self.log_enabled:
            return
        
        session_info = {
            "timestamp": self.session_start_time.isoformat(),
            "session_id": self.session_id,
            "message_type": "session_start",
            "user_prompt": user_prompt,
            "system_prompt": system_prompt,
            "provider": provider,
            "model": model
        }
        
        self.messages_log.append(session_info)
    
    def log_session_end(self, task_complete: bool, task_message: str = "", iteration_count: int = 0):
        """Log session end information"""
        if not self.log_enabled:
            return
        
        session_end_info = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "message_type": "session_end",
            "task_complete": task_complete,
            "task_message": task_message,
            "iteration_count": iteration_count,
            "session_duration": (datetime.now() - self.session_start_time).total_seconds()
        }
        
        self.messages_log.append(session_end_info)
        
        # Save the complete log
        self._save_log()
    
    def _save_log(self):
        """Save the complete message log to file"""
        if not self.log_enabled:
            return
        
        filename = f"{self.session_id}.json"
        filepath = os.path.join(self.save_path, filename)
        
        log_data = {
            "session_metadata": {
                "session_id": self.session_id,
                "start_time": self.session_start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_messages": len(self.messages_log)
            },
            "messages": self.messages_log
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            print(f"\n📝 Session log saved to: {filepath}")
        except Exception as e:
            print(f"❌ Error saving log: {e}")
    
    def get_session_id(self) -> str:
        """Get current session ID"""
        return self.session_id
