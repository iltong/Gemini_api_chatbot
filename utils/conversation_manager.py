"""
대화 저장/불러오기 유틸리티
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from config.settings import GenerationParams, APIUsage

class ConversationManager:
    """대화 저장/불러오기 관리 클래스"""
    
    def __init__(self):
        self.conversation_log: List[Dict[str, Any]] = []
    
    def add_to_log(self, sender: str, message: str, image_info: Optional[str], model: str):
        """대화 로그에 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "sender": sender,
            "message": message,
            "image_info": image_info,
            "model": model
        }
        self.conversation_log.append(log_entry)
    
    def clear_log(self):
        """대화 로그 초기화"""
        self.conversation_log.clear()
    
    def save_conversation(self, filename: str, model_name: str, model_display_name: str,
                         generation_params: GenerationParams, system_prompt: str,
                         api_usage: APIUsage, history: List[Dict[str, Any]]) -> bool:
        """대화 저장"""
        try:
            conversation_data = {
                "timestamp": datetime.now().isoformat(),
                "model": model_name,
                "model_display_name": model_display_name,
                "supports_vision": True,
                "generation_params": generation_params.to_dict(),
                "system_prompt": system_prompt,
                "api_usage": api_usage.to_dict(),
                "conversation_log": self.conversation_log,
                "history": history
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"대화 저장 오류: {e}")
            return False
    
    def load_conversation(self, filename: str) -> Optional[Dict[str, Any]]:
        """대화 불러오기"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            # 대화 로그 복원
            if "conversation_log" in conversation_data:
                self.conversation_log = conversation_data["conversation_log"]
            
            return conversation_data
            
        except Exception as e:
            print(f"대화 불러오기 오류: {e}")
            return None
    
    def extract_display_messages(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """히스토리에서 화면 표시용 메시지 추출"""
        display_messages = []
        
        for message in history:
            role = message["role"]
            display_text = ""
            has_image = False
            
            for part in message["parts"]:
                if "text" in part:
                    display_text += part["text"]
                elif "image" in part:
                    has_image = True
            
            display_messages.append({
                "role": role,
                "text": display_text,
                "has_image": has_image
            })
        
        return display_messages
    
    def create_history_for_api(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """API용 히스토리 생성 (텍스트만)"""
        history_messages = []
        
        for message in history:
            role = message["role"]
            display_text = ""
            
            for part in message["parts"]:
                if "text" in part:
                    display_text += part["text"]
            
            if display_text:
                history_messages.append({
                    "role": role,
                    "parts": [{"text": display_text}]
                })
        
        return history_messages