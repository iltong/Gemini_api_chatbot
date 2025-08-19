"""
설정 및 구성 관리 모듈
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple
import os
import tkinter.font as tkfont
from dotenv import load_dotenv

@dataclass
class GenerationParams:
    """생성 파라미터 설정"""
    max_output_tokens: int = 32768
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenerationParams':
        return cls(
            max_output_tokens=data.get("max_output_tokens", 32768),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 0.95),
            top_k=data.get("top_k", 40),
            presence_penalty=data.get("presence_penalty", 0.0),
            frequency_penalty=data.get("frequency_penalty", 0.0)
        )

@dataclass
class APIUsage:
    """API 사용량 추적"""
    requests_today: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    last_reset: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requests_today": self.requests_today,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "last_reset": self.last_reset
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIUsage':
        return cls(
            requests_today=data.get("requests_today", 0),
            tokens_used=data.get("tokens_used", 0),
            cost_estimate=data.get("cost_estimate", 0.0),
            last_reset=data.get("last_reset", "")
        )

@dataclass
class FontSettings:
    """폰트 설정"""
    chat_font_family: str = "맑은 고딕"
    chat_font_size: int = 13  # 11 -> 13으로 증가
    input_font_family: str = "맑은 고딕"  
    input_font_size: int = 13  # 11 -> 13으로 증가
    button_font_family: str = "맑은 고딕"
    button_font_size: int = 11  # 10 -> 11로 증가
    title_font_family: str = "맑은 고딕"
    title_font_size: int = 18  # 16 -> 18로 증가
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chat_font_family": self.chat_font_family,
            "chat_font_size": self.chat_font_size,
            "input_font_family": self.input_font_family,
            "input_font_size": self.input_font_size,
            "button_font_family": self.button_font_family,
            "button_font_size": self.button_font_size,
            "title_font_family": self.title_font_family,
            "title_font_size": self.title_font_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FontSettings':
        return cls(
            chat_font_family=data.get("chat_font_family", "맑은 고딕"),
            chat_font_size=data.get("chat_font_size", 13),  # 11 -> 13
            input_font_family=data.get("input_font_family", "맑은 고딕"),
            input_font_size=data.get("input_font_size", 13),  # 11 -> 13
            button_font_family=data.get("button_font_family", "맑은 고딕"),
            button_font_size=data.get("button_font_size", 11),  # 10 -> 11
            title_font_family=data.get("title_font_family", "맑은 고딕"),
            title_font_size=data.get("title_font_size", 18)  # 16 -> 18
        )
    
    def get_chat_font(self) -> Tuple[str, int]:
        """채팅 폰트 반환"""
        return (self.chat_font_family, self.chat_font_size)
    
    def get_input_font(self) -> Tuple[str, int]:
        """입력 폰트 반환"""
        return (self.input_font_family, self.input_font_size)
    
    def get_button_font(self) -> Tuple[str, int, str]:
        """버튼 폰트 반환"""
        return (self.button_font_family, self.button_font_size, "bold")
    
    def get_title_font(self) -> Tuple[str, int, str]:
        """제목 폰트 반환"""
        return (self.title_font_family, self.title_font_size, "bold")

class AppConfig:
    """애플리케이션 설정 관리"""
    
    def __init__(self):
        load_dotenv()
        
        # 기본 설정
        self.AVAILABLE_MODELS = {
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "gemini-2.5-flash": "Gemini 2.5 Flash"
        }
        
        self.DEFAULT_MODEL = "gemini-2.5-pro"
        
        # API 설정
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        # 안전 설정
        self.SAFETY_SETTINGS = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        # 재시도 설정
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1.0
        
        # UI 설정
        self.WINDOW_TITLE = "✨ Gemini Chat Studio"
        self.WINDOW_GEOMETRY = "1200x850"
        self.MIN_WINDOW_SIZE = (900, 650)
        
        # 폰트 설정
        self.AVAILABLE_FONTS = [
            "맑은 고딕", "Arial", "Helvetica", "Times New Roman", 
            "Courier New", "Verdana", "Tahoma", "Georgia",
            "Comic Sans MS", "Trebuchet MS", "나눔고딕", "D2Coding"
        ]
        
        # 사용 가능한 폰트 중에서 시스템에 설치된 것만 필터링
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # 창을 숨김
            available_system_fonts = list(tkfont.families())
            self.AVAILABLE_FONTS = [font for font in self.AVAILABLE_FONTS 
                                  if font in available_system_fonts or font == "맑은 고딕"]
            root.destroy()
        except:
            pass  # 오류 시 기본 폰트 목록 사용
        
        # 기본 폰트 설정
        self.font_settings = FontSettings()
        
        # 기본 테마 설정 (모던 다크 테마)
        self.THEME = {
            "bg_primary": "#0f1419",      # 깊이 있는 검정 블루
            "bg_secondary": "#1a1f2e",    # 채팅창 배경
            "bg_tertiary": "#2d3748",     # 버튼 배경
            "bg_input": "#232a3b",        # 입력창 배경
            "bg_user_bubble": "#2563eb",  # 사용자 버블
            "bg_bot_bubble": "#1f2937",   # AI 버블
            "fg_primary": "#f8fafc",      # 메인 타읋합
            "fg_secondary": "#cbd5e1",    # 보조 텍스트
            "fg_accent": "#22c55e",       # AI 이름 그린
            "fg_user": "#3b82f6",         # 사용자 이름 블루
            "fg_system": "#94a3b8",       # 시스템 메시지
            "fg_error": "#ef4444",        # 오류 메시지
            "fg_timestamp": "#64748b",    # 타임스탬프
            "border": "#374151",          # 경계선
            "shadow": "#000000"           # 그림자
        }
        
        # 시스템 프롬프트 프리셋
        self.PROMPT_PRESETS = {
            "기본": "",
            "번역사": "당신은 전문 번역가입니다. 정확하고 자연스러운 번역을 제공해주세요.",
            "코딩 도우미": "당신은 프로그래밍 전문가입니다. 코드 작성, 디버깅, 최적화에 도움을 주세요.",
            "학습 도우미": "당신은 친절한 선생님입니다. 복잡한 개념을 쉽게 설명해주세요."
        }
        
        # 파라미터 범위 설정
        self.PARAM_RANGES = {
            "max_output_tokens": (1, 32768, "int"),
            "temperature": (0.0, 2.0, "float"),
            "top_p": (0.0, 1.0, "float"),
            "top_k": (1, 100, "int"),
            "presence_penalty": (-2.0, 2.0, "float"),
            "frequency_penalty": (-2.0, 2.0, "float")
        }
        
        # 파라미터 설명
        self.PARAM_DESCRIPTIONS = {
            "max_output_tokens": "최대 출력 토큰",
            "temperature": "창의성 (Temperature)",
            "top_p": "다양성 (Top-p)",
            "top_k": "후보 수 (Top-k)",
            "presence_penalty": "주제 다양성",
            "frequency_penalty": "반복 방지"
        }
    
    def get_api_key(self) -> str:
        """API 키 반환"""
        return self.api_key
    
    def set_api_key(self, api_key: str):
        """API 키 설정"""
        self.api_key = api_key
    
