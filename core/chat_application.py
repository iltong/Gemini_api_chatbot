"""
메인 채팅 애플리케이션 클래스
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import ctypes
import sys
import os
from typing import List, Any

# 드래그 앤 드롭 라이브러리 임포트 시도
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_TKINTERDND2 = True
except ImportError:
    HAS_TKINTERDND2 = False

try:
    import windnd
    HAS_WINDND = True
except ImportError:
    HAS_WINDND = False

from config.settings import AppConfig, GenerationParams, FontSettings
from core.gemini_client import GeminiClient
from ui.chat_display import ChatDisplay
from ui.settings_dialog import SettingsDialog
from utils.image_handler import ImageHandler
from utils.file_handler import FileHandler
from utils.conversation_manager import ConversationManager

class ChatApplication:
    """메인 채팅 애플리케이션 클래스"""
    
    def __init__(self):
        # 설정 초기화
        self.config = AppConfig()
        
        # High DPI 지원 설정
        self.setup_high_dpi()
        
        # DPI 스케일링
        self.dpi_scale = self.get_dpi_scale()
        
        # 폰트 설정 - DPI 스케일링 적용
        self.apply_dpi_to_fonts()
        
        # 폰트 설정
        self.update_fonts()
        
        # 생성 파라미터
        self.generation_params = GenerationParams()
        
        # 컴포넌트 초기화
        self.gemini_client = None
        self.chat_display = None
        self.image_handler = ImageHandler()
        self.file_handler = FileHandler()
        self.conversation_manager = ConversationManager()
        
        # 스트리밍 관련
        self.is_streaming = False
        
        # 드래그 앤 드롭 상태
        self.drag_over = False
        self.original_input_bg = None
        
        # UI 컴포넌트 참조
        self.root = None
        self.model_var = None
        self.model_combo = None
        self.model_status_label = None
        self.usage_label = None
        self.input_text = None
        self.send_button = None
        self.stop_button = None
        self.image_button = None
        self.image_preview_frame = None
        
        self.setup_api_and_gui()
    
    def setup_high_dpi(self):
        """High DPI 지원 설정"""
        try:
            if sys.platform.startswith('win'):
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
    
    def get_dpi_scale(self):
        """DPI 스케일 계산"""
        try:
            if sys.platform.startswith('win'):
                user32 = ctypes.windll.user32
                dpi = user32.GetDpiForSystem()
                return dpi / 96.0
            else:
                return 1.0
        except:
            return 1.0
    
    def apply_dpi_to_fonts(self):
        """DPI 스케일링을 폰트 설정에 적용"""
        font_settings = self.config.font_settings
        
        # DPI 스케일링 적용
        font_settings.chat_font_size = max(8, int(font_settings.chat_font_size * self.dpi_scale))
        font_settings.input_font_size = max(8, int(font_settings.input_font_size * self.dpi_scale))
        font_settings.button_font_size = max(8, int(font_settings.button_font_size * self.dpi_scale))
        font_settings.title_font_size = max(10, int(font_settings.title_font_size * self.dpi_scale))
    
    def update_fonts(self):
        """폰트 설정 업데이트"""
        font_settings = self.config.font_settings
        
        self.chat_font = font_settings.get_chat_font()
        self.title_font = font_settings.get_title_font()
        self.input_font = font_settings.get_input_font()
        self.button_font = font_settings.get_button_font()
    
    def update_ui_fonts(self):
        """UI 컴포넌트들의 폰트 업데이트"""
        # 채팅 디스플레이 폰트 업데이트
        if hasattr(self, 'chat_display') and self.chat_display:
            self.chat_display.update_fonts(self.config.font_settings)
        
        # 입력 텍스트 폰트 업데이트
        if hasattr(self, 'input_text') and self.input_text:
            self.input_text.configure(font=self.input_font)
        
        # 버튼들 폰트 업데이트 (필요시 추가 구현)
        # 전체 UI를 다시 그리는 것보다는 개별 컴포넌트를 업데이트하는 것이 효율적
    
    def setup_api_and_gui(self):
        """API 및 GUI 초기화"""
        # API 키 확인
        if not self.config.api_key:
            api_key = simpledialog.askstring("API Key", "Gemini API 키를 입력하세요:", show='*')
            if not api_key:
                messagebox.showerror("오류", "API 키가 필요합니다.")
                exit()
            self.config.set_api_key(api_key)
        
        # Gemini 클라이언트 초기화
        try:
            self.gemini_client = GeminiClient(self.config)
        except Exception as e:
            messagebox.showerror("API 오류", f"Gemini API 초기화 실패: {str(e)}")
            exit()
        
        # GUI 생성
        self.create_gui()
    
    def create_gui(self):
        """GUI 생성"""
        # tkinterdnd2가 있으면 DnD 지원 루트 창 생성
        if HAS_TKINTERDND2:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title(self.config.WINDOW_TITLE)
        self.root.configure(bg=self.config.THEME["bg_primary"])
        self.root.minsize(*self.config.MIN_WINDOW_SIZE)
        
        
        # 스타일 설정
        self.setup_styles()
        
        # GUI 컴포넌트 생성
        self.create_header()
        
        
        self.create_usage_display()
        self.create_chat_area()
        self.create_input_area()
        
        # 키보드 바인딩
        self.setup_key_bindings()
        
        # 초기 메시지 표시
        self.chat_display.display_welcome_message(
            self.gemini_client.get_model_display_name(),
            self.generation_params.to_dict()
        )
        
        # 드래그 앤 드롭 힌트 표시 (환영 메시지 이후)
        self.root.after(1000, self.show_drag_drop_hint)
        
        self.input_text.focus()
    
    def setup_styles(self):
        """스타일 설정"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 커스텀 스타일 정의
        self.style.configure('Title.TLabel', 
                           background=self.config.THEME["bg_primary"], 
                           foreground=self.config.THEME["fg_primary"],
                           font=self.title_font)
        
        self.style.configure('Modern.TButton',
                           font=self.button_font,
                           borderwidth=0,
                           focuscolor='none',
                           padding=(10, 5))
        
        self.style.map('Modern.TButton',
                      background=[('active', '#4a4a6a'), ('!active', self.config.THEME["bg_secondary"])])
        
        # Combobox 스타일
        self.style.configure('Model.TCombobox',
                           fieldbackground=self.config.THEME["bg_input"],
                           background=self.config.THEME["bg_secondary"],
                           foreground=self.config.THEME["fg_primary"],
                           arrowcolor=self.config.THEME["fg_primary"],
                           font=self.button_font)
    
    def create_header(self):
        """헤더 영역 생성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg=self.config.THEME["bg_primary"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 헤더 프레임 - 더 세련된 디자인
        header_frame = tk.Frame(main_container, bg=self.config.THEME["bg_primary"], height=90)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        header_frame.pack_propagate(False)
        
        # 제목
        title_label = tk.Label(header_frame, 
                             text=self.config.WINDOW_TITLE, 
                             font=self.title_font,
                             bg=self.config.THEME["bg_primary"], 
                             fg=self.config.THEME["fg_primary"])
        title_label.pack(side=tk.LEFT, pady=10)
        
        # 모델 선택 영역
        self.create_model_selection(header_frame)
        
        # 메뉴 버튼들
        self.create_menu_buttons(header_frame)
        
        # 메인 컨테이너를 인스턴스 변수로 저장
        self.main_container = main_container
    
    
    def create_model_selection(self, parent: tk.Widget):
        """모델 선택 영역 생성"""
        model_frame = tk.Frame(parent, bg=self.config.THEME["bg_primary"])
        model_frame.pack(side=tk.LEFT, padx=(30, 0), pady=10)
        
        # 모델 선택 라벨
        model_label = tk.Label(model_frame, 
                             text="모델:", 
                             bg=self.config.THEME["bg_primary"], 
                             fg=self.config.THEME["fg_primary"],
                             font=self.button_font)
        model_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 모델 선택 드롭다운
        self.model_var = tk.StringVar(value=self.gemini_client.current_model_name)
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=list(self.config.AVAILABLE_MODELS.keys()),
            state="readonly",
            width=20,
            style='Model.TCombobox',
            font=self.button_font
        )
        self.model_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.model_combo.bind('<<ComboboxSelected>>', self.change_model)
        
        # 현재 모델 상태 표시
        self.model_status_label = tk.Label(
            model_frame,
            text=f"🤖 {self.gemini_client.get_model_display_name()}",
            bg=self.config.THEME["bg_primary"],
            fg=self.config.THEME["fg_accent"],
            font=self.button_font
        )
        self.model_status_label.pack(side=tk.LEFT)
    
    def create_menu_buttons(self, parent: tk.Widget):
        """메뉴 버튼들 생성"""
        menu_frame = tk.Frame(parent, bg=self.config.THEME["bg_primary"])
        menu_frame.pack(side=tk.RIGHT, pady=10)
        
        
        
        # 설정 버튼 - 모던 스타일
        settings_button = tk.Button(menu_frame, 
                                   text="⚙️ 설정", 
                                   command=self.open_settings_dialog,
                                   font=self.button_font,
                                   bg="#8b5cf6", 
                                   fg="#ffffff",
                                   border=0,
                                   padx=18, pady=10,
                                   activebackground="#7c3aed",
                                   relief=tk.FLAT,
                                   cursor="hand2")
        settings_button.pack(side=tk.LEFT, padx=(0, 12))
        
        # 저장 버튼 - 모던 스타일
        save_button = tk.Button(menu_frame, 
                               text="💾 저장", 
                               command=self.save_conversation,
                               font=self.button_font,
                               bg="#6b7280", 
                               fg="#ffffff",
                               border=0,
                               padx=18, pady=10,
                               activebackground="#4b5563",
                               relief=tk.FLAT,
                               cursor="hand2")
        save_button.pack(side=tk.LEFT, padx=(0, 12))
        
        # 불러오기 버튼 - 모던 스타일
        load_button = tk.Button(menu_frame, 
                               text="📂 불러오기", 
                               command=self.load_conversation,
                               font=self.button_font,
                               bg="#6b7280", 
                               fg="#ffffff",
                               border=0,
                               padx=18, pady=10,
                               activebackground="#4b5563",
                               relief=tk.FLAT,
                               cursor="hand2")
        load_button.pack(side=tk.LEFT, padx=(0, 12))
        
        # 새로시작 버튼 - 모던 스타일
        new_button = tk.Button(menu_frame, 
                              text="🆕 새로시작", 
                              command=self.new_conversation,
                              font=self.button_font,
                              bg="#6b7280", 
                              fg="#ffffff",
                              border=0,
                              padx=18, pady=10,
                              activebackground="#4b5563",
                              relief=tk.FLAT,
                              cursor="hand2")
        new_button.pack(side=tk.LEFT)
    
    def create_usage_display(self):
        """API 사용량 표시 영역 생성"""
        usage_frame = tk.Frame(self.main_container, bg=self.config.THEME["bg_primary"])
        usage_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.gemini_client.reset_daily_usage()
        usage = self.gemini_client.api_usage
        self.usage_label = tk.Label(usage_frame, 
                                  text=f"📊 API 사용량: {usage.requests_today}회 | 토큰: {usage.tokens_used:,} | 예상비용: ${usage.cost_estimate:.4f}",
                                  bg=self.config.THEME["bg_primary"], 
                                  fg=self.config.THEME["fg_system"],
                                  font=self.chat_font)
        self.usage_label.pack(side=tk.LEFT)
    
    def create_chat_area(self):
        """채팅 영역 생성"""
        self.chat_display = ChatDisplay(self.main_container, self.config)
    
    def create_input_area(self):
        """입력 영역 생성"""
        # 입력 영역 - 더 모던한 디자인
        input_container = tk.Frame(self.main_container, 
                                 bg=self.config.THEME["bg_input"], 
                                 relief=tk.FLAT)
        input_container.pack(fill=tk.X, pady=(15, 0))
        
        # 이미지 미리보기 영역
        self.image_preview_frame = tk.Frame(input_container, bg=self.config.THEME["bg_input"])
        
        input_inner = tk.Frame(input_container, bg=self.config.THEME["bg_input"])
        input_inner.pack(fill=tk.BOTH, padx=20, pady=20)
        
        # 입력 텍스트 영역
        text_input_frame = tk.Frame(input_inner, bg=self.config.THEME["bg_input"])
        text_input_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_text = tk.Text(
            text_input_frame,
            height=4,
            font=self.input_font,
            wrap=tk.WORD,
            bg=self.config.THEME["bg_secondary"],
            fg=self.config.THEME["fg_primary"],
            insertbackground=self.config.THEME["fg_accent"],
            selectbackground="#4338ca",
            relief=tk.FLAT,
            borderwidth=0,
            padx=18,
            pady=12
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 18))
        
        # 원본 배경색 저장
        self.original_input_bg = self.config.THEME["bg_secondary"]
        
        # 버튼 영역
        self.create_button_area(text_input_frame)
    
    def create_button_area(self, parent: tk.Widget):
        """버튼 영역 생성"""
        button_container = tk.Frame(parent, bg=self.config.THEME["bg_input"])
        button_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 중단 버튼 (초기에는 숨김) - 모던 스타일
        self.stop_button = tk.Button(
            button_container,
            text="⏹️ 중단",
            command=self.stop_streaming,
            font=self.button_font,
            bg="#ef4444",
            fg="#ffffff",
            border=0,
            padx=18, pady=10,
            activebackground="#dc2626",
            relief=tk.FLAT,
            cursor="hand2"
        )
        
        # 이미지 선택 버튼 - 모던 스타일
        self.image_button = tk.Button(
            button_container,
            text="🖼️ 이미지",
            command=self.select_image,
            font=self.button_font,
            bg="#f59e0b",
            fg="#ffffff",
            border=0,
            padx=18, pady=10,
            activebackground="#d97706",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.image_button.pack(fill=tk.X, pady=(0, 8))
        
        # 파일 선택 버튼 - 모던 스타일
        self.file_button = tk.Button(
            button_container,
            text="📄 파일",
            command=self.select_file,
            font=self.button_font,
            bg="#8b5cf6",
            fg="#ffffff",
            border=0,
            padx=18, pady=10,
            activebackground="#7c3aed",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.file_button.pack(fill=tk.X, pady=(0, 8))
        
        # 전송 버튼 - 모던 스타일
        self.send_button = tk.Button(
            button_container,
            text="🚀 전송",
            command=self.send_message,
            font=self.button_font,
            bg="#22c55e",
            fg="#ffffff",
            border=0,
            padx=22, pady=18,
            activebackground="#16a34a",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.send_button.pack(fill=tk.BOTH, expand=True)
    
    def setup_key_bindings(self):
        """키보드 바인딩 설정"""
        self.input_text.bind('<Return>', self.on_enter_key)
        self.input_text.bind('<Control-Return>', self.insert_newline)
        self.input_text.bind('<Shift-Return>', self.insert_newline)
        
        # 전역 단축키 설정
        self.root.bind('<Control-n>', lambda e: self.new_conversation())
        self.root.bind('<Control-N>', lambda e: self.new_conversation())
        self.root.bind('<Control-s>', lambda e: self.save_conversation())
        self.root.bind('<Control-S>', lambda e: self.save_conversation())
        self.root.bind('<Control-o>', lambda e: self.load_conversation())
        self.root.bind('<Control-O>', lambda e: self.load_conversation())
        
        # 드래그 앤 드롭 이벤트 바인딩 (기본 tkinter 방식)
        self.setup_drag_and_drop()
    
    
    def open_settings_dialog(self):
        """설정 대화상자 열기"""
        def on_save(new_params: GenerationParams, new_prompt: str, new_font_settings: FontSettings):
            self.generation_params = new_params
            self.gemini_client.set_system_prompt(new_prompt)
            
            # 폰트 설정 업데이트
            self.config.font_settings = new_font_settings
            self.update_fonts()
            self.update_ui_fonts()
        
        SettingsDialog(
            self.root, 
            self.config, 
            self.generation_params,
            self.gemini_client.system_prompt,
            self.config.font_settings,
            on_save
        )
    
    def change_model(self, event=None):
        """모델 변경 처리"""
        new_model = self.model_var.get()
        if new_model != self.gemini_client.current_model_name:
            if self.gemini_client.chat_session and self.gemini_client.chat_session.history:
                result = messagebox.askyesno(
                    "모델 변경", 
                    f"모델을 '{self.config.AVAILABLE_MODELS[new_model]}'로 변경하면 현재 대화 내용이 삭제됩니다.\n계속하시겠습니까?"
                )
                if not result:
                    self.model_var.set(self.gemini_client.current_model_name)
                    return
            
            # 모델 변경
            self.gemini_client.change_model(new_model)
            self.clear_conversation()
            self.update_model_status()
            self.chat_display.display_system_message(f"🔄 모델이 '{self.config.AVAILABLE_MODELS[new_model]}'로 변경되었습니다.")
    
    def update_model_status(self):
        """모델 상태 표시 업데이트"""
        model_display_name = self.gemini_client.get_model_display_name()
        self.model_status_label.config(text=f"🤖 {model_display_name}")
    
    def update_usage_display(self):
        """사용량 표시 업데이트"""
        usage = self.gemini_client.api_usage
        usage_text = f"📊 API 사용량: {usage.requests_today}회 | 토큰: {usage.tokens_used:,} | 예상비용: ${usage.cost_estimate:.4f}"
        self.usage_label.config(text=usage_text)
    
    def clear_conversation(self):
        """대화 내용 초기화"""
        self.gemini_client.clear_conversation()
        self.conversation_manager.clear_log()
        self.chat_display.clear_display()
        self.chat_display.display_welcome_message(
            self.gemini_client.get_model_display_name(),
            self.generation_params.to_dict()
        )
        
        if self.image_handler.has_image():
            self.image_handler.clear_image()
            self.remove_image_preview()
    
    def new_conversation(self):
        """새 대화 시작"""
        result = messagebox.askyesno("새 대화", "현재 대화를 저장하지 않고 새로 시작하시겠습니까?")
        if result:
            self.clear_conversation()
    
    
    def load_conversation(self, filename: str = None):
        """대화 불러오기"""
        if not filename:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="대화 불러오기"
            )
        
        if filename:
            conversation_data = self.conversation_manager.load_conversation(filename)
            if not conversation_data:
                messagebox.showerror("불러오기 오류", "대화 불러오기 중 오류가 발생했습니다.")
                return
            
            # 저장된 설정 복원
            self.restore_conversation_settings(conversation_data)
            
            # 대화 내용 표시
            self.display_loaded_conversation(conversation_data)
            
            messagebox.showinfo("불러오기 완료", "대화가 성공적으로 불러와졌습니다.\n이전 맥락과 설정이 유지됩니다.")
    
    def restore_conversation_settings(self, conversation_data: dict):
        """저장된 대화 설정 복원"""
        # 모델 변경
        saved_model = conversation_data.get('model', self.config.DEFAULT_MODEL)
        if saved_model != self.gemini_client.current_model_name:
            if self.gemini_client.change_model(saved_model):
                self.model_var.set(saved_model)
                self.update_model_status()
        
        # 생성 파라미터 복원
        if "generation_params" in conversation_data:
            self.generation_params = GenerationParams.from_dict(conversation_data["generation_params"])
        
        # 시스템 프롬프트 복원
        if "system_prompt" in conversation_data:
            self.gemini_client.set_system_prompt(conversation_data["system_prompt"])
    
    def display_loaded_conversation(self, conversation_data: dict):
        """불러온 대화 내용 표시"""
        self.chat_display.clear_display()
        
        # 로드 정보 표시
        model_info = conversation_data.get('model_display_name', 'Unknown')
        self.chat_display.display_system_message(f"📂 대화 불러오기 완료 ({conversation_data.get('timestamp', 'Unknown')})")
        self.chat_display.display_system_message(f"🤖 모델: {model_info}")
        
        # 히스토리 복원 및 표시
        if "history" in conversation_data:
            display_messages = self.conversation_manager.extract_display_messages(conversation_data["history"])
            
            for msg in display_messages:
                if msg["role"] == "user":
                    image_info = "이미지 첨부됨" if msg["has_image"] else None
                    self.chat_display.display_user_message(msg["text"], image_info)
                elif msg["role"] == "model":
                    self.chat_display.start_bot_response(self.gemini_client.get_model_display_name())
                    self.chat_display.display_bot_message(msg["text"])
            
            # API용 히스토리 복원
            history_for_api = self.conversation_manager.create_history_for_api(conversation_data["history"])
            self.gemini_client.restore_conversation_history(history_for_api)
    
    def select_image(self):
        """이미지 선택"""
        filename = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            success, error_msg = self.image_handler.load_image(filename)
            if success:
                preview_photo = self.image_handler.create_preview()
                if preview_photo:
                    self.show_image_preview(preview_photo, filename)
                    self.image_button.config(text="🗑️ 삭제", command=self.remove_image, bg="#F44336")
            else:
                messagebox.showerror("이미지 오류", error_msg)
    
    def select_file(self):
        """파일 선택"""
        # 지원되는 파일 확장자 목록을 파일 다이얼로그 형식으로 변환
        supported_exts = self.file_handler.get_supported_extensions_list()
        
        # 확장자별로 그룹핑
        code_files = [ext for ext in supported_exts if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go']]
        web_files = [ext for ext in supported_exts if ext in ['.html', '.htm', '.css', '.scss', '.sass', '.vue', '.svelte']]
        data_files = [ext for ext in supported_exts if ext in ['.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg']]
        doc_files = [ext for ext in supported_exts if ext in ['.txt', '.md', '.rst']]
        
        filetypes = [
            ("코드 파일", " ".join(f"*{ext}" for ext in code_files)),
            ("웹 파일", " ".join(f"*{ext}" for ext in web_files)),
            ("데이터 파일", " ".join(f"*{ext}" for ext in data_files)),
            ("문서 파일", " ".join(f"*{ext}" for ext in doc_files)),
            ("지원되는 모든 파일", " ".join(f"*{ext}" for ext in supported_exts)),
            ("모든 파일", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="파일 선택",
            filetypes=filetypes
        )
        
        if filename:
            success, error_msg = self.file_handler.load_file(filename)
            if success:
                self.show_file_preview(filename)
                self.file_button.config(text="🗑️ 삭제", command=self.remove_file, bg="#F44336")
            else:
                messagebox.showerror("파일 오류", error_msg)
    
    def show_image_preview(self, photo, filename):
        """이미지 미리보기 표시"""
        # 기존 미리보기 제거
        for widget in self.image_preview_frame.winfo_children():
            widget.destroy()
        
        # 미리보기 프레임 표시
        self.image_preview_frame.pack(fill=tk.X, padx=15, pady=(15, 0))
        
        preview_container = tk.Frame(self.image_preview_frame, 
                                   bg=self.config.THEME["bg_input"], 
                                   relief=tk.SOLID, bd=1)
        preview_container.pack(fill=tk.X, pady=5)
        
        # 이미지 라벨
        image_label = tk.Label(preview_container, image=photo, bg=self.config.THEME["bg_input"])
        image_label.image = photo  # 참조 유지
        image_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 파일명 라벨
        filename_short = self.image_handler.get_short_filename()
        info_label = tk.Label(
            preview_container, 
            text=f"📎 {filename_short}",
            bg=self.config.THEME["bg_input"], 
            fg=self.config.THEME["fg_primary"],
            font=self.chat_font
        )
        info_label.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    def remove_image(self):
        """선택된 이미지 제거"""
        self.image_handler.clear_image()
        self.remove_image_preview() 
        self.image_button.config(text="🖼️ 이미지", command=self.select_image, bg="#FF9800")
    
    def remove_image_preview(self):
        """이미지 미리보기 제거"""
        self.image_preview_frame.pack_forget()
    
    def show_file_preview(self, filename):
        """파일 미리보기 표시"""
        # 기존 미리보기 제거
        for widget in self.image_preview_frame.winfo_children():
            widget.destroy()
        
        # 미리보기 프레임 표시
        self.image_preview_frame.pack(fill=tk.X, padx=15, pady=(15, 0))
        
        preview_container = tk.Frame(self.image_preview_frame, 
                                   bg=self.config.THEME["bg_input"], 
                                   relief=tk.SOLID, bd=1)
        preview_container.pack(fill=tk.X, pady=5)
        
        # 파일 아이콘과 정보
        info_frame = tk.Frame(preview_container, bg=self.config.THEME["bg_input"])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 파일 정보 라벨
        file_info = self.file_handler.get_file_info()
        info_label = tk.Label(
            info_frame, 
            text=f"📄 {file_info}",
            bg=self.config.THEME["bg_input"], 
            fg=self.config.THEME["fg_primary"],
            font=self.chat_font,
            anchor="w"
        )
        info_label.pack(fill=tk.X)
        
        # 파일 미리보기 (처음 몇 줄)
        preview_text = self.file_handler.get_file_preview(10)
        if preview_text:
            preview_label = tk.Label(
                info_frame,
                text=preview_text[:200] + ("..." if len(preview_text) > 200 else ""),
                bg=self.config.THEME["bg_input"],
                fg=self.config.THEME["fg_secondary"],
                font=("Consolas", 9),
                anchor="nw",
                justify=tk.LEFT,
                wraplength=400
            )
            preview_label.pack(fill=tk.X, pady=(5, 0))
    
    def remove_file(self):
        """선택된 파일 제거"""
        self.file_handler.clear_file()
        self.remove_image_preview()  # 같은 프레임 사용
        self.file_button.config(text="📄 파일", command=self.select_file, bg="#8b5cf6")
    
    def send_message(self):
        """메시지 전송 처리"""
        user_input = self.input_text.get(1.0, tk.END).strip()
        
        # 텍스트나 이미지, 파일 중 하나는 있어야 함
        if not user_input and not self.image_handler.has_image() and not self.file_handler.has_file():
            messagebox.showwarning("입력 필요", "텍스트를 입력하거나 이미지/파일을 선택해주세요.")
            return
        
        # 텍스트가 없으면 기본 텍스트 설정
        if not user_input:
            if self.image_handler.has_image():
                user_input = "이 이미지에 대해 설명해주세요."
            elif self.file_handler.has_file():
                user_input = "이 파일을 분석해주세요."
        
        self.input_text.delete(1.0, tk.END)
        
        # UI 상태 변경
        self.send_button.pack_forget()
        self.stop_button.pack(fill=tk.BOTH, expand=True)
        self.is_streaming = True
        
        # 사용자 메시지 표시
        image_info = None
        file_info = None
        chat_image_preview = None
        
        # 이미지 정보
        if self.image_handler.has_image():
            image_info = self.image_handler.get_image_info()
            chat_image_preview = self.image_handler.create_chat_preview()
        
        # 파일 정보
        if self.file_handler.has_file():
            file_info = self.file_handler.get_file_info()
        
        # 둘 다 있으면 이미지 정보를 attachment_info로, 파일은 별도로
        if image_info and file_info:
            self.chat_display.display_user_message(user_input, image_info, chat_image_preview, file_info)
        elif image_info:
            self.chat_display.display_user_message(user_input, image_info, chat_image_preview)
        elif file_info:
            self.chat_display.display_user_message(user_input, None, None, file_info)
        else:
            self.chat_display.display_user_message(user_input)
        
        # 대화 로그에 추가 (첨부 정보 조합)
        combined_attachment = []
        if image_info:
            combined_attachment.append(image_info)
        if file_info:
            combined_attachment.append(file_info)
        attachment_log = " | ".join(combined_attachment) if combined_attachment else None
        
        self.conversation_manager.add_to_log("user", user_input, attachment_log, self.gemini_client.current_model_name)
        
        # 봇 응답 시작
        self.chat_display.start_bot_response(self.gemini_client.get_model_display_name())
        
        # 백그라운드에서 응답 처리
        self.process_response_in_background(user_input)
    
    def process_response_in_background(self, user_input: str):
        """백그라운드에서 응답 처리"""
        def get_response_thread():
            try:
                # 메시지 구성
                message_parts = []
                
                # 이미지가 있으면 추가
                image = self.image_handler.get_image_for_api()
                if image:
                    message_parts.append(image)
                
                # 파일이 있으면 추가
                file_content = self.file_handler.get_file_for_api()
                if file_content:
                    message_parts.append(file_content)
                
                # 텍스트 추가
                message_parts.append(user_input)
                
                # 토큰 추정
                estimated_input_tokens = len(user_input.split()) * 1.3
                
                # API 호출
                response_stream = self.gemini_client.send_message_with_retry(
                    message_parts, self.generation_params, stream=True
                )
                
                full_response = ""
                output_tokens = 0
                
                # 스트리밍 응답 처리
                for chunk in response_stream:
                    if not self.is_streaming:  # 중단 요청 시
                        break
                        
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                        full_response += chunk_text
                        
                        # 실시간으로 화면에 표시
                        self.root.after(0, lambda text=chunk_text: self.chat_display.display_streaming_chunk(text))
                        
                        # 토큰 추정
                        output_tokens += len(chunk_text.split()) * 1.3
                
                if self.is_streaming and full_response:
                    print(f"[DEBUG] Calling finalize_streaming_response, response length: {len(full_response)}")
                    # 최종적으로 마크다운 렌더링으로 교체
                    self.root.after(0, lambda: self.chat_display.finalize_streaming_response(
                        full_response, self.gemini_client.get_model_display_name()
                    ))
                    
                    # API 사용량 업데이트
                    self.gemini_client.update_api_usage(int(estimated_input_tokens), int(output_tokens))
                    self.root.after(0, self.update_usage_display)
                    
                    # 대화 로그에 추가
                    self.conversation_manager.add_to_log("bot", full_response, None, self.gemini_client.current_model_name)
                
                elif not full_response and self.is_streaming:
                    # 응답이 없는 경우
                    error_message = "🚫 응답을 생성할 수 없습니다. 이미지가 정책에 위배될 수 있습니다."
                    self.root.after(0, lambda: self.chat_display.display_streaming_chunk(error_message))
                
                self.root.after(0, self.complete_response)
                
            except Exception as e:
                error_str = str(e)
                
                # 오류 메시지 처리
                if "block_reason" in error_str.lower() or "safety" in error_str.lower():
                    if "OTHER" in error_str:
                        error_message = "🚫 이미지 안전 검열: 업로드된 이미지가 Google의 안전 정책에 위배되어 처리할 수 없습니다."
                    else:
                        error_message = f"🚫 안전 필터 차단: {error_str}"
                elif "api key" in error_str.lower():
                    error_message = "🔑 API 키 오류: API 키가 유효하지 않거나 만료되었습니다."
                else:
                    error_message = f"❌ 오류가 발생했습니다: {error_str}"
                
                self.root.after(0, lambda: self.chat_display.display_streaming_chunk(error_message))
                self.root.after(0, self.complete_response)
        
        thread = threading.Thread(target=get_response_thread)
        thread.daemon = True
        thread.start()
    
    def stop_streaming(self):
        """스트리밍 중단"""
        self.is_streaming = False
        self.complete_response()
        
        # 중단 메시지 표시
        self.chat_display.display_streaming_chunk("\n\n⏹️ 응답이 중단되었습니다.\n")
    
    def complete_response(self):
        """응답 완료 처리"""
        self.is_streaming = False
        
        # 버튼 상태 복원
        self.stop_button.pack_forget()
        self.send_button.pack(fill=tk.BOTH, expand=True)
        
        # 이미지와 파일 초기화
        if self.image_handler.has_image():
            self.image_handler.clear_image()
            self.remove_image_preview()
            self.image_button.config(text="🖼️ 이미지", command=self.select_image, bg="#FF9800")
        
        if self.file_handler.has_file():
            self.file_handler.clear_file()
            self.remove_image_preview()  # 같은 프레임 사용
            self.file_button.config(text="📄 파일", command=self.select_file, bg="#8b5cf6")
        
        self.input_text.focus()
    
    def on_enter_key(self, event):
        """Enter 키 이벤트 처리"""
        if event.state & 0x4 or event.state & 0x1:  # Ctrl+Enter 또는 Shift+Enter
            return
        self.send_message()
        return "break"
    
    def insert_newline(self, event):
        """Ctrl/Shift+Enter로 줄바꿈 삽입"""
        self.input_text.insert(tk.INSERT, "\n")
        return "break"
    
    def setup_drag_and_drop(self):
        """드래그 앤 드롭 설정"""
        drag_drop_setup = False
        
        # windnd 사용 시도 (Windows에서 한글 파일명 지원이 더 좋음)
        if HAS_WINDND and sys.platform.startswith('win'):
            try:
                windnd.hook_dropfiles(self.input_text, func=self.on_windnd_drop)
                drag_drop_setup = True
                print("windnd 드래그 앤 드롭 설정 완료")
            except Exception as e:
                print(f"windnd 설정 오류: {e}")
        
        # tkinterdnd2 사용 시도 (windnd가 실패한 경우)
        if not drag_drop_setup and HAS_TKINTERDND2:
            try:
                self.input_text.drop_target_register(DND_FILES)
                self.input_text.dnd_bind('<<Drop>>', self.on_tkinterdnd2_drop)
                self.input_text.dnd_bind('<<DragEnter>>', self.on_drag_enter)
                self.input_text.dnd_bind('<<DragLeave>>', self.on_drag_leave)
                drag_drop_setup = True
                print("tkinterdnd2 드래그 앤 드롭 설정 완료")
            except Exception as e:
                print(f"tkinterdnd2 설정 오류: {e}")
        
        # 둘 다 실패한 경우 기본 설정
        if not drag_drop_setup:
            self.setup_basic_drag_drop()
            print("기본 드래그 앤 드롭 설정 (클립보드만)")
    
    def setup_basic_drag_drop(self):
        """기본 드래그 앤 드롭 설정 (windnd 없이)"""
        # 클립보드를 통한 이미지 붙여넣기 지원
        self.input_text.bind('<Control-v>', self.on_paste)
        
        # 드래그 오버 시각적 피드백을 위한 이벤트
        self.input_text.bind('<Enter>', self.on_mouse_enter)
        self.input_text.bind('<Leave>', self.on_mouse_leave)
        
        # 사용법 힌트 표시
        self.show_drag_drop_hint()
    
    def on_tkinterdnd2_drop(self, event):
        """tkinterdnd2 드롭 이벤트 처리"""
        print(f"DEBUG: event.data 원본: '{event.data}'")
        
        # 여러 방법으로 파일 경로 파싱 시도
        file_path = None
        
        # 방법 1: 중괄호로 감싸진 경우
        if event.data.startswith('{') and event.data.endswith('}'):
            file_path = event.data.strip('{}')
            print(f"DEBUG: 중괄호 제거 후: '{file_path}'")
        
        # 방법 2: 공백으로 분할된 여러 파일 (첫 번째만 사용)
        elif ' ' in event.data:
            # 공백이 있는 경우, 전체를 하나의 경로로 처리
            file_path = event.data.strip()
            print(f"DEBUG: 공백 포함 경로: '{file_path}'")
        
        # 방법 3: 단순한 경우
        else:
            file_path = event.data.strip()
            print(f"DEBUG: 단순 경로: '{file_path}'")
        
        # 경로에서 불필요한 문자 제거
        if file_path:
            file_path = file_path.strip('\'"')
            print(f"DEBUG: 최종 정리된 경로: '{file_path}'")
            self.process_dropped_file(file_path)
        else:
            print("DEBUG: 파일 경로를 파싱할 수 없습니다.")
    
    def on_windnd_drop(self, files):
        """windnd 드롭 이벤트 처리"""
        if not files:
            return
        
        # 첫 번째 파일만 처리
        file_path = files[0]
        
        # bytes 타입인 경우 디코딩
        if isinstance(file_path, bytes):
            try:
                file_path = file_path.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    file_path = file_path.decode('cp949')  # 한글 Windows 인코딩
                except UnicodeDecodeError:
                    file_path = file_path.decode('utf-8', errors='replace')
        
        print(f"DEBUG: windnd 원본 파일 경로: '{file_path}'")
        self.process_dropped_file(file_path)
    
    def on_drag_enter(self, event):
        """드래그 진입 시 시각적 피드백"""
        self.highlight_drop_zone(True)
        return "copy"
    
    def on_drag_leave(self, event):
        """드래그 벗어날 시 시각적 피드백 제거"""
        self.highlight_drop_zone(False)
    
    def process_dropped_file(self, file_path):
        """드롭된 파일 처리 (공통 로직)"""
        print(f"DEBUG: 드롭된 파일 경로: '{file_path}'")
        print(f"DEBUG: 파일 존재 여부: {os.path.isfile(file_path)}")
        
        # 파일 존재 확인
        if not os.path.isfile(file_path):
            messagebox.showerror("파일 오류", "파일을 찾을 수 없습니다.")
            self.highlight_drop_zone(False)
            return
        
        # 이미지 파일인지 확인
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        file_ext = os.path.splitext(file_path.lower())[1]
        
        if file_ext in image_extensions:
            # 이미지 처리
            success, error_msg = self.image_handler.load_image(file_path)
            if success:
                preview_photo = self.image_handler.create_preview()
                if preview_photo:
                    self.show_image_preview(preview_photo, file_path)
                    self.image_button.config(text="🗑️ 삭제", command=self.remove_image, bg="#F44336")
                messagebox.showinfo("이미지 업로드", f"이미지가 업로드되었습니다: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("이미지 오류", error_msg)
        
        elif self.file_handler.is_supported_file(file_path):
            # 파일 처리
            success, error_msg = self.file_handler.load_file(file_path)
            if success:
                self.show_file_preview(file_path)
                self.file_button.config(text="🗑️ 삭제", command=self.remove_file, bg="#F44336")
                messagebox.showinfo("파일 업로드", f"파일이 업로드되었습니다: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("파일 오류", error_msg)
        
        else:
            # 지원하지 않는 파일 형식
            supported_exts = list(image_extensions) + self.file_handler.get_supported_extensions_list()
            messagebox.showerror("지원하지 않는 파일", 
                               f"지원하지 않는 파일 형식입니다.\n\n지원 형식:\n{', '.join(supported_exts)}")
        
        self.highlight_drop_zone(False)
    
    def on_paste(self, event):
        """Ctrl+V 붙여넣기 이벤트 처리"""
        try:
            # 클립보드에서 이미지 가져오기 시도
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            
            if img:
                # 임시 파일로 저장
                import tempfile
                temp_path = tempfile.mktemp(suffix='.png')
                img.save(temp_path, 'PNG')
                
                # 기존 이미지가 있으면 교체 확인
                if self.image_handler.has_image():
                    result = messagebox.askyesno(
                        "이미지 교체", 
                        "이미 선택된 이미지가 있습니다. 클립보드의 이미지로 교체하시겠습니까?"
                    )
                    if not result:
                        os.remove(temp_path)
                        return "break"
                
                # 이미지 로드
                success, error_msg = self.image_handler.load_image(temp_path)
                if success:
                    preview_photo = self.image_handler.create_preview()
                    if preview_photo:
                        self.show_image_preview(preview_photo, temp_path)
                        self.image_button.config(text="🗑️ 삭제", command=self.remove_image, bg="#F44336")
                        messagebox.showinfo("이미지 첨부", "클립보드의 이미지가 성공적으로 첨부되었습니다.")
                else:
                    messagebox.showerror("이미지 오류", error_msg)
                    os.remove(temp_path)
                
                return "break"  # 기본 붙여넣기 동작 방지
        except ImportError:
            pass  # PIL이 없는 경우 무시
        except Exception as e:
            print(f"클립보드 이미지 처리 오류: {e}")
        
        # 기본 텍스트 붙여넣기는 그대로 진행
        return None
    
    def show_drag_drop_hint(self):
        """드래그 앤 드롭 사용법 힌트 표시"""
        # 초기 사용법 힌트를 채팅창에 표시
        self.chat_display.display_system_message(
            "💡 팁: 이미지를 직접 텍스트 입력창에 드래그 앤 드롭하거나 Ctrl+V로 클립보드 이미지를 붙여넣을 수 있습니다!"
        )
    
    def on_mouse_enter(self, event):
        """마우스 입력창 진입 시"""
        # 현재는 특별한 처리 없음, 향후 드래그 힌트 확장 가능
        pass
    
    def on_mouse_leave(self, event):
        """마우스 입력창 벗어날 시"""
        # 현재는 특별한 처리 없음, 향후 드래그 힌트 확장 가능
        pass
    
    def highlight_drop_zone(self, highlight=True):
        """드롭 존 하이라이트"""
        if highlight:
            self.input_text.config(bg="#3b82f6", relief=tk.SOLID, borderwidth=3)
        else:
            self.input_text.config(bg=self.original_input_bg, relief=tk.FLAT, borderwidth=0)
    
    
    
    
    
    def save_conversation(self):
        """대화 저장 (사이드바 연동 개선)"""
        if (not self.gemini_client.chat_session or 
            not self.gemini_client.chat_session.history):
            messagebox.showwarning("저장 불가", "저장할 대화가 없습니다.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="대화 저장"
        )
        
        if filename:
            history = self.gemini_client.get_conversation_history()
            success = self.conversation_manager.save_conversation(
                filename,
                self.gemini_client.current_model_name,
                self.gemini_client.get_model_display_name(),
                self.generation_params,
                self.gemini_client.system_prompt,
                self.gemini_client.api_usage,
                history
            )
            
            if success:
                messagebox.showinfo("저장 완료", f"대화가 저장되었습니다:\n{filename}\n\n모델: {self.gemini_client.get_model_display_name()}")
            else:
                messagebox.showerror("저장 오류", "대화 저장 중 오류가 발생했습니다.")
    
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()