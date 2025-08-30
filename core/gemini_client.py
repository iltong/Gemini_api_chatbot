"""
Gemini API 클라이언트 모듈
"""

import google.generativeai as genai
from google.generativeai.types import File
import time
import os
from typing import Generator, List, Dict, Any, Optional
from datetime import datetime

from config.settings import AppConfig, GenerationParams, APIUsage

class GeminiClient:
    """Gemini API 클라이언트"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.current_model_name = config.DEFAULT_MODEL
        self.system_prompt = ""
        self.chat_session = None
        self.model = None
        
        # API 사용량 추적
        self.api_usage = APIUsage()
        self.reset_daily_usage()
        
        self.setup_api()
    
    def setup_api(self):
        """API 초기 설정"""
        if not self.config.api_key:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        genai.configure(api_key=self.config.api_key)
        self.setup_model()
    
    def setup_model(self):
        """모델 설정"""
        self.model = genai.GenerativeModel(
            self.current_model_name,
            safety_settings=self.config.SAFETY_SETTINGS,
            system_instruction=self.system_prompt if self.system_prompt else None
        )
        self.chat_session = None
    
    def change_model(self, model_name: str):
        """모델 변경"""
        if model_name in self.config.AVAILABLE_MODELS:
            self.current_model_name = model_name
            self.setup_model()
            return True
        return False
    
    def set_system_prompt(self, prompt: str):
        """시스템 프롬프트 설정"""
        if prompt != self.system_prompt:
            self.system_prompt = prompt
            self.setup_model()
    
    def upload_video_to_gemini(self, video_path: str) -> Optional[File]:
        """동영상을 Gemini File API에 업로드"""
        try:
            print(f"동영상 업로드 시작: {video_path}")
            
            # 동영상 파일 업로드
            video_file = genai.upload_file(path=video_path)
            print(f"업로드 완료: {video_file.name}")
            
            # 처리 상태 확인 (필요한 경우)
            while video_file.state.name == "PROCESSING":
                print("동영상 처리 중...")
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                print(f"동영상 처리 실패: {video_file.state.name}")
                return None
            
            print(f"동영상 업로드 및 처리 완료: {video_file.name}")
            return video_file
            
        except Exception as e:
            print(f"동영상 업로드 오류: {e}")
            return None
    
    def reset_daily_usage(self):
        """일별 사용량 초기화"""
        today = datetime.now().date()
        if self.api_usage.last_reset != str(today):
            self.api_usage.requests_today = 0
            self.api_usage.tokens_used = 0
            self.api_usage.cost_estimate = 0.0
            self.api_usage.last_reset = str(today)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """비용 추정"""
        if self.current_model_name == "gemini-2.5-pro":
            input_cost = input_tokens * 0.00125 / 1000
            output_cost = output_tokens * 0.005 / 1000
        else:  # flash
            input_cost = input_tokens * 0.000075 / 1000
            output_cost = output_tokens * 0.0003 / 1000
        
        return input_cost + output_cost
    
    def update_api_usage(self, input_tokens: int = 0, output_tokens: int = 0):
        """API 사용량 업데이트"""
        self.reset_daily_usage()
        self.api_usage.requests_today += 1
        self.api_usage.tokens_used += input_tokens + output_tokens
        self.api_usage.cost_estimate += self.estimate_cost(input_tokens, output_tokens)
    
    def send_message_with_retry(self, message_parts: List[Any], 
                               generation_params: GenerationParams,
                               stream: bool = True,
                               retries: int = 0) -> Generator[Any, None, None]:
        """재시도 로직이 포함된 메시지 전송"""
        try:
            # 새 세션 시작
            if self.chat_session is None:
                self.chat_session = self.model.start_chat(history=[])
            
            # 생성 설정 구성
            generation_config = genai.GenerationConfig(
                max_output_tokens=generation_params.max_output_tokens,
                temperature=generation_params.temperature,
                top_p=generation_params.top_p,
                top_k=generation_params.top_k
            )
            
            # API 호출
            response_stream = self.chat_session.send_message(
                message_parts,
                safety_settings=self.config.SAFETY_SETTINGS,
                generation_config=generation_config,
                stream=stream
            )
            
            return response_stream
            
        except Exception as e:
            error_str = str(e).lower()
            
            # 재시도 가능한 오류들
            retryable_errors = [
                "rate limit", "quota", "temporarily unavailable", 
                "server error", "timeout", "connection", "network"
            ]
            
            is_retryable = any(error in error_str for error in retryable_errors)
            
            if is_retryable and retries < self.config.MAX_RETRIES:
                time.sleep(self.config.RETRY_DELAY * (retries + 1))
                return self.send_message_with_retry(message_parts, generation_params, stream, retries + 1)
            else:
                raise e
    
    def clear_conversation(self):
        """대화 초기화"""
        self.chat_session = None
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """대화 히스토리 반환"""
        if not self.chat_session or not self.chat_session.history:
            return []
        
        history = []
        for message in self.chat_session.history:
            message_data = {
                "role": message.role,
                "parts": []
            }
            
            for part in message.parts:
                if hasattr(part, 'text'):
                    message_data["parts"].append({"text": part.text})
                elif hasattr(part, 'inline_data'):
                    message_data["parts"].append({"image": "[이미지 첨부됨]"})
            
            history.append(message_data)
        
        return history
    
    def restore_conversation_history(self, history: List[Dict[str, Any]]):
        """대화 히스토리 복원"""
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
        
        self.chat_session = self.model.start_chat(history=history_messages)
    
    def get_model_display_name(self) -> str:
        """현재 모델의 표시명 반환"""
        return self.config.AVAILABLE_MODELS.get(self.current_model_name, self.current_model_name)