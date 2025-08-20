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
from PIL import Image, ImageTk

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

class ImagePreviewWindow:
    """이미지 임시 미리보기 창"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.window = None
        self.current_images = []
        self.current_index = 0
        self.preview_label = None
        self.info_label = None
        
    def show_preview(self, image_handler, newly_added_index=None):
        """미리보기 창 표시"""
        print(f"DEBUG: show_preview 호출됨 - 모드: {image_handler.current_mode}, 이미지 수: {image_handler.get_image_count()}")
        
        if image_handler.current_mode == "multiple" and image_handler.get_image_count() > 0:
            self.current_images = image_handler.images
            self.current_index = newly_added_index if newly_added_index is not None else len(self.current_images) - 1
            print(f"DEBUG: 다중 이미지 모드 - 현재 인덱스: {self.current_index}, 전체 이미지: {len(self.current_images)}")
        elif image_handler.current_mode == "single" and image_handler.has_image():
            # 단일 모드도 미리보기 창에서 표시하도록 변경
            single_image_info = {
                'path': image_handler.selected_image_path,
                'image': image_handler.selected_image,
                'filename': os.path.basename(image_handler.selected_image_path) if image_handler.selected_image_path else "단일이미지"
            }
            self.current_images = [single_image_info]
            self.current_index = 0
            print(f"DEBUG: 단일 이미지 모드 - 파일: {single_image_info['filename']}")
        else:
            print("DEBUG: 표시할 이미지가 없음")
            return
            
        self.create_window()
        # 창 생성 후 약간의 지연을 두고 이미지 업데이트
        self.window.after(50, self.update_preview)
        
    def create_window(self):
        """미리보기 창 생성"""
        if self.window:
            self.window.destroy()
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("이미지 미리보기")
        self.window.configure(bg=self.config.THEME["bg_primary"])
        
        # 창 크기 및 위치 설정
        window_width = 600
        window_height = 500
        
        # 부모 창 중앙에 위치
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(True, True)  # 크기 조절 가능하게 변경
        self.window.transient(self.parent)  # 항상 부모 창 위에
        self.window.grab_set()  # 모달 창
        self.window.lift()  # 창을 최상위로
        self.window.attributes('-topmost', True)  # 항상 위에 표시
        self.window.after(100, lambda: self.window.attributes('-topmost', False))  # 0.1초 후 해제
        
        # 상단 정보 바
        info_frame = tk.Frame(self.window, bg=self.config.THEME["bg_secondary"], height=50)
        info_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        info_frame.pack_propagate(False)
        
        self.info_label = tk.Label(
            info_frame,
            text="",
            bg=self.config.THEME["bg_secondary"],
            fg=self.config.THEME["fg_primary"],
            font=("맑은 고딕", 12, "bold")
        )
        self.info_label.pack(expand=True)
        
        # 이미지 표시 영역
        image_frame = tk.Frame(self.window, bg="#ffffff", relief=tk.SUNKEN, bd=2)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.preview_label = tk.Label(
            image_frame,
            bg="#ffffff",
            text="이미지를 불러오는 중...",
            fg="#666666",
            font=("맑은 고딕", 12)
        )
        self.preview_label.pack(expand=True, padx=10, pady=10)
        
        # 하단 버튼 영역
        button_frame = tk.Frame(self.window, bg=self.config.THEME["bg_primary"])
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # 네비게이션 버튼들 (다중 이미지인 경우만)
        if len(self.current_images) > 1:
            nav_frame = tk.Frame(button_frame, bg=self.config.THEME["bg_primary"])
            nav_frame.pack(side=tk.LEFT)
            
            prev_btn = tk.Button(
                nav_frame,
                text="◀ 이전",
                command=self.prev_image,
                font=("맑은 고딕", 10),
                bg="#6366f1",
                fg="#ffffff",
                border=0,
                padx=15, pady=8,
                activebackground="#4f46e5",
                relief=tk.FLAT,
                cursor="hand2"
            )
            prev_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            next_btn = tk.Button(
                nav_frame,
                text="다음 ▶",
                command=self.next_image,
                font=("맑은 고딕", 10),
                bg="#6366f1",
                fg="#ffffff",
                border=0,
                padx=15, pady=8,
                activebackground="#4f46e5",
                relief=tk.FLAT,
                cursor="hand2"
            )
            next_btn.pack(side=tk.LEFT)
        
        # 닫기 버튼
        close_btn = tk.Button(
            button_frame,
            text="✕ 닫기",
            command=self.close_window,
            font=("맑은 고딕", 10),
            bg="#6b7280",
            fg="#ffffff",
            border=0,
            padx=20, pady=8,
            activebackground="#4b5563",
            relief=tk.FLAT,
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT)
        
        # ESC 키로 닫기
        self.window.bind('<Escape>', lambda e: self.close_window())
        
        # 포커스 설정
        self.window.focus_set()
        
    def update_preview(self):
        """현재 이미지 미리보기 업데이트"""
        if not self.current_images or self.current_index >= len(self.current_images):
            self.preview_label.config(image="", text="이미지가 없습니다.")
            return
            
        current_image_info = self.current_images[self.current_index]
        
        # 정보 업데이트
        if len(self.current_images) > 1:
            info_text = f"이미지 {self.current_index + 1} / {len(self.current_images)} - {current_image_info['filename']}"
        else:
            info_text = f"이미지: {current_image_info['filename']}"
        
        if self.info_label:
            self.info_label.config(text=info_text)
        
        # 이미지 미리보기 생성 (큰 크기)
        try:
            print(f"DEBUG: 이미지 미리보기 업데이트 시작 - {current_image_info['filename']}")
            
            # 원본 이미지가 있는지 확인
            if 'image' not in current_image_info or current_image_info['image'] is None:
                self.preview_label.config(image="", text="이미지 데이터가 없습니다.")
                return
            
            # 이미지 복사 및 크기 조정
            original_image = current_image_info['image']
            display_image = original_image.copy()
            
            # 원본 크기 정보
            orig_width, orig_height = display_image.size
            print(f"DEBUG: 원본 이미지 크기: {orig_width}x{orig_height}")
            
            # 큰 미리보기 크기로 조정 (비율 유지)
            max_width, max_height = 500, 350
            display_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            new_width, new_height = display_image.size
            print(f"DEBUG: 조정된 이미지 크기: {new_width}x{new_height}")
            
            # Tkinter PhotoImage로 변환
            photo = ImageTk.PhotoImage(display_image)
            
            # 라벨에 이미지 설정
            self.preview_label.config(image=photo, text="", compound='center')
            self.preview_label.image = photo  # 참조 유지 (중요!)
            
            print(f"DEBUG: 이미지 미리보기 성공적으로 표시됨")
            
        except Exception as e:
            error_msg = f"이미지 표시 오류: {str(e)}"
            print(f"DEBUG: {error_msg}")
            self.preview_label.config(image="", text=error_msg)
    
    def prev_image(self):
        """이전 이미지"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_preview()
    
    def next_image(self):
        """다음 이미지"""
        if self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.update_preview()
    
    def close_window(self):
        """창 닫기"""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def is_open(self):
        """창이 열려있는지 확인"""
        return self.window is not None and self.window.winfo_exists()

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
        self.image_handler.set_mode("multiple")  # 타일 시스템을 위해 다중 모드 설정
        self.file_handler = FileHandler()
        self.file_handler.set_mode("multiple")  # 타일 시스템을 위해 다중 모드 설정
        
        # UI 컴포넌트 참조
        self.attachment_button = None
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
        self.attachment_button = None
        self.image_preview_frame = None
        
        # 이미지 미리보기 창
        self.preview_window = None
        
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
        
        # 호버 미리보기를 위한 변수
        self.hover_preview_window = None
        
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
        
        # 이미지 미리보기 영역 (채팅창 아래, 입력창 위에 배치)
        self.image_preview_frame = tk.Frame(self.main_container, bg=self.config.THEME["bg_input"])
        self.image_preview_frame.pack(fill=tk.X, padx=15, pady=(5, 0))  # 채팅 영역 뒤에 팩
        self.image_preview_frame.config(height=90)  # 고정 높이 감소 (100 -> 90)
        self.image_preview_frame.pack_propagate(False)  # 자식 위젯 크기에 의한 변경 방지
        self.image_preview_frame.pack_forget()  # 초기에는 숨김
    
    def create_input_area(self):
        """입력 영역 생성"""
        # 입력 영역 - 더 모던한 디자인
        self.input_container = tk.Frame(self.main_container, 
                                 bg=self.config.THEME["bg_input"], 
                                 relief=tk.FLAT)
        self.input_container.pack(fill=tk.X, pady=(10, 0))  # 상단 여백 감소 (15 -> 10)
        # pack_propagate 제거하여 자연스러운 크기 조정 허용
        
        # 이미지 미리보기 프레임은 create_chat_area()에서 생성됨
        
        input_inner = tk.Frame(self.input_container, bg=self.config.THEME["bg_input"])
        input_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)  # 세로 패딩 감소 (20 -> 15)
        
        # 입력 텍스트 영역 (고정 크기 유지)
        text_input_frame = tk.Frame(input_inner, bg=self.config.THEME["bg_input"])
        text_input_frame.pack(fill=tk.BOTH, expand=True)
        # text_input_frame.pack_propagate(False)  # 원래 레이아웃이 깨지지 않도록 주석 처리
        
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
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 18))  # 원래대로 복구
        
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
        
        # 이미지 모드 전환 버튼
        
        # 통합 파일 선택 버튼 - 이미지와 파일을 자동 구분
        self.attachment_button = tk.Button(
            button_container,
            text="📎 파일 첨부",
            command=self.select_attachment,
            font=self.button_font,
            bg="#6366f1",
            fg="#ffffff",
            border=0,
            padx=18, pady=10,
            activebackground="#4f46e5",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.attachment_button.pack(fill=tk.X, pady=(0, 8))
        
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
            self.update_attachment_tiles()  # 새로운 타일 시스템 사용
    
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
        """이미지 선택 (더 이상 사용하지 않음 - select_attachment로 대체됨)"""
        # 통합 파일 선택 함수로 리다이렉트
        self.select_attachment()
    
    def select_file(self):
        """파일 선택 (더 이상 사용하지 않음 - select_attachment로 대체됨)"""
        # 통합 파일 선택 함수로 리다이렉트
        self.select_attachment()
    
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
        """선택된 이미지 제거 (더 이상 사용하지 않음 - remove_all_attachments로 대체됨)"""
        self.remove_all_attachments()
    
    def remove_image_preview(self):
        """이미지 미리보기 제거"""
        self.image_preview_frame.pack_forget()
    
    def select_attachment(self):
        """통합 파일 선택 - 이미지와 파일을 자동으로 구분하여 처리"""
        # 지원되는 파일 확장자 목록을 파일 다이얼로그 형식으로 변환
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff']
        file_extensions = self.file_handler.get_supported_extensions_list()
        
        # 모든 지원되는 확장자 조합
        all_extensions = image_extensions + file_extensions
        
        # 확장자별로 그룹핑
        image_files = [ext for ext in image_extensions]
        code_files = [ext for ext in file_extensions if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go']]
        web_files = [ext for ext in file_extensions if ext in ['.html', '.htm', '.css', '.scss', '.sass', '.vue', '.svelte']]
        data_files = [ext for ext in file_extensions if ext in ['.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg']]
        doc_files = [ext for ext in file_extensions if ext in ['.txt', '.md', '.rst']]
        
        filetypes = [
            ("이미지 파일", " ".join(f"*{ext}" for ext in image_files)),
            ("코드 파일", " ".join(f"*{ext}" for ext in code_files)),
            ("웹 파일", " ".join(f"*{ext}" for ext in web_files)),
            ("데이터 파일", " ".join(f"*{ext}" for ext in data_files)),
            ("문서 파일", " ".join(f"*{ext}" for ext in doc_files)),
            ("지원되는 모든 파일", " ".join(f"*{ext}" for ext in all_extensions)),
            ("모든 파일", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="파일 첨부 (다중 선택 가능)",
            filetypes=filetypes
        )
        
        if filenames:
            for filename in filenames:
                self.process_selected_file(filename)
    
    def process_selected_file(self, file_path):
        """선택된 파일을 유형에 따라 자동으로 처리"""
        # 파일 확장자 확인
        file_ext = os.path.splitext(file_path.lower())[1]
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff']
        
        if file_ext in image_extensions:
            # 이미지 파일 처리
            success, error_msg = self.image_handler.load_image(file_path)
            if success:
                self.update_attachment_tiles()
                self.update_attachment_button()
            else:
                messagebox.showerror("이미지 오류", error_msg)
        
        elif self.file_handler.is_supported_file(file_path):
            # 텍스트/코드 파일 처리
            success, error_msg = self.file_handler.load_file(file_path)
            if success:
                self.update_attachment_tiles()
                self.update_attachment_button()
            else:
                messagebox.showerror("파일 오류", error_msg)
        
        else:
            # 지원하지 않는 파일 형식
            supported_exts = image_extensions + self.file_handler.get_supported_extensions_list()
            messagebox.showerror("지원하지 않는 파일", 
                               f"지원하지 않는 파일 형식입니다.\n\n지원되는 형식:\n{', '.join(supported_exts)}")
    
    def update_attachment_button(self):
        """첨부 파일 상태에 따라 버튼 텍스트와 기능 업데이트"""
        has_images = self.image_handler.has_image()
        has_files = self.file_handler.has_file()
        
        if has_images or has_files:
            # 첨부 파일이 있으면 삭제 버튼으로 변경
            self.attachment_button.config(
                text="🗑️ 첨부 삭제",
                command=self.remove_all_attachments,
                bg="#F44336"
            )
        else:
            # 첨부 파일이 없으면 기본 상태
            self.attachment_button.config(
                text="📎 파일 첨부",
                command=self.select_attachment,
                bg="#6366f1"
            )
    
    def remove_all_attachments(self):
        """모든 첨부 파일 제거"""
        self.image_handler.clear_all_images()
        self.file_handler.clear_all_files()
        self.update_attachment_tiles()
        self.update_attachment_button()
    
    def update_attachment_tiles(self):
        """입력창 위에 체부파일(이미지 + 파일) 타일들 표시"""
        # 기존 미리보기 제거
        for widget in self.image_preview_frame.winfo_children():
            widget.destroy()
        
        # 이미지나 파일이 없으면 숨김
        if not self.image_handler.has_image() and not self.file_handler.has_file():
            self.image_preview_frame.pack_forget()
            return
        
        # 미리보기 프레임 표시 (입력창 삻전에 강제 배치)
        self.image_preview_frame.pack(fill=tk.X, padx=15, pady=(5, 0), before=self.input_container)
        
        # 타일 컨테이너 (수평 스크롤 가능)
        tiles_container = tk.Frame(self.image_preview_frame, 
                                 bg=self.config.THEME["bg_input"])
        tiles_container.pack(fill=tk.X, pady=5)
        
        # 모든 체부파일(이미지 + 파일) 타일 생성
        tile_index = 0
        
        # 이미지 타일 추가 (항상 다중 모드로 처리)
        if self.image_handler.has_image():
            # 다중 모드: 모든 이미지 추가
            images = self.image_handler.images
            for img_info in images:
                self.create_attachment_tile(tiles_container, tile_index, img_info, "image")
                tile_index += 1
        
        # 파일 타일 추가 (다중 파일 지원)
        if self.file_handler.has_file():
            if self.file_handler.current_mode == "multiple":
                # 다중 모드: 모든 파일 추가
                files = self.file_handler.files
                for file_info in files:
                    self.create_attachment_tile(tiles_container, tile_index, file_info, "file")
                    tile_index += 1
            else:
                # 단일 모드 (하위 호환성)
                file_info = {
                    'path': self.file_handler.selected_file_path,
                    'filename': os.path.basename(self.file_handler.selected_file_path) if self.file_handler.selected_file_path else "파일"
                }
                self.create_attachment_tile(tiles_container, tile_index, file_info, "file")
                tile_index += 1
    
    def create_attachment_tile(self, parent, index, item_info, item_type):
        """호버 기능이 있는 체부파일(이미진/파일) 타일 생성"""
        # 타일 프레임 (80x80 고정 크기)
        tile_frame = tk.Frame(parent, 
                             bg=self.config.THEME["bg_secondary"], 
                             relief=tk.RAISED, 
                             bd=2,
                             width=80, 
                             height=80,
                             cursor="hand2")
        tile_frame.pack(side=tk.LEFT, padx=3, pady=3)
        tile_frame.pack_propagate(False)  # 크기 고정
        
        # 체부파일 타입에 따른 내용 표시
        if item_type == "image":
            # 이미지 타일
            try:
                preview_image = item_info['image'].copy()
                preview_image.thumbnail((70, 70), Image.Resampling.LANCZOS)
                preview_photo = ImageTk.PhotoImage(preview_image)
                
                # 이미지 라벨
                content_label = tk.Label(tile_frame, 
                                       image=preview_photo, 
                                       bg=self.config.THEME["bg_secondary"],
                                       cursor="hand2")
                content_label.pack(expand=True)
                content_label.image = preview_photo  # 참조 유지
                
            except Exception as e:
                # 이미지 로드 실패시 텍스트 표시
                content_label = tk.Label(tile_frame, 
                                     text="🖼️", 
                                     bg=self.config.THEME["bg_secondary"],
                                     fg=self.config.THEME["fg_secondary"],
                                     font=("맑은 고딕", 20))
                content_label.pack(expand=True)
        else:
            # 파일 타일 - 파일 확장자에 따른 아이콘 표시
            file_ext = os.path.splitext(item_info['filename'])[1].lower()
            icon = self.get_file_icon(file_ext)
            
            content_label = tk.Label(tile_frame, 
                                   text=icon, 
                                   bg=self.config.THEME["bg_secondary"],
                                   fg=self.config.THEME["fg_accent"],
                                   font=("맑은 고딕", 24),
                                   cursor="hand2")
            content_label.pack(expand=True)
        
        # 파일명 표시 (하단) - 모든 타입에 대해 표시
        filename = item_info['filename']
        if len(filename) > 10:
            filename = filename[:7] + "..."
        
        name_label = tk.Label(tile_frame, 
                            text=filename,
                            bg=self.config.THEME["bg_secondary"],
                            fg=self.config.THEME["fg_secondary"],
                            font=("맑은 고딕", 7))
        name_label.pack(side=tk.BOTTOM)
        
        # 호버 이벤트 바인딩
        def on_enter(event):
            self.show_attachment_preview(event, item_info, item_type)
            tile_frame.config(relief=tk.SOLID, bd=3)
        
        def on_leave(event):
            self.hide_hover_preview()
            tile_frame.config(relief=tk.RAISED, bd=2)
        
        def on_click(event):
            self.remove_attachment_by_index(index, item_type)
        
        # 이벤트 바인딩 (모든 위젯에 적용)
        for widget in [tile_frame, content_label, name_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
    
    def get_file_icon(self, file_ext):
        """파일 확장자에 따른 아이콘 반환"""
        icon_map = {
            '.pdf': '📄',
            '.doc': '📝', '.docx': '📝',
            '.xls': '📊', '.xlsx': '📊',
            '.ppt': '📊', '.pptx': '📊',
            '.txt': '📄',
            '.py': '🐍',
            '.js': '📜',
            '.html': '🌐', '.htm': '🌐',
            '.css': '🎨',
            '.json': '📊',
            '.xml': '📜',
            '.zip': '🗄', '.rar': '🗄', '.7z': '🗄',
            '.mp4': '🎥', '.avi': '🎥', '.mov': '🎥',
            '.mp3': '🎵', '.wav': '🎵', '.m4a': '🎵',
        }
        return icon_map.get(file_ext, '📁')  # 기본 폴더 아이콘
    
    def show_attachment_preview(self, event, item_info, item_type):
        """마우스 호버시 체부파일 미리보기 표시"""
        if self.hover_preview_window:
            self.hide_hover_preview()
        
        if item_type == "image":
            # 이미지 미리보기
            try:
                # 큰 미리보기 이미지 생성 (300x300)
                large_image = item_info['image'].copy()
                large_image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                large_photo = ImageTk.PhotoImage(large_image)
                
                # 호버 미리보기 창 생성 (Toplevel)
                self.hover_preview_window = tk.Toplevel(self.root)
                self.hover_preview_window.wm_overrideredirect(True)  # 타이틀바 없음
                self.hover_preview_window.configure(bg="#ffffff", relief=tk.SOLID, bd=2)
                
                # 이미지 표시
                preview_label = tk.Label(self.hover_preview_window,
                                       image=large_photo,
                                       bg="#ffffff")
                preview_label.pack(padx=5, pady=5)
                preview_label.image = large_photo  # 참조 유지
                
                # 파일명 표시
                name_label = tk.Label(self.hover_preview_window,
                                    text=item_info['filename'],
                                    bg="#ffffff",
                                    fg="#333333",
                                    font=("맑은 고딕", 10, "bold"))
                name_label.pack(pady=(0, 5))
                
            except Exception as e:
                print(f"이미지 호버 미리보기 오류: {e}")
        else:
            # 파일 미리보기 (단순히 파일명만 표시)
            try:
                self.hover_preview_window = tk.Toplevel(self.root)
                self.hover_preview_window.wm_overrideredirect(True)
                self.hover_preview_window.configure(bg="#f8f9fa", relief=tk.SOLID, bd=1)
                
                # 파일명만 표시
                name_label = tk.Label(self.hover_preview_window,
                                    text=item_info['filename'],
                                    bg="#f8f9fa",
                                    fg="#333333",
                                    font=("맑은 고딕", 11, "bold"),
                                    padx=15, pady=8)
                name_label.pack()
                
            except Exception as e:
                print(f"파일 호버 미리보기 오류: {e}")
        
        # 위치 계산 (마우스 근처에 표시)
        if self.hover_preview_window:
            x = event.x_root + 10
            y = event.y_root - 150  # 마우스 위쪽에 표시
            
            # 화면 경계 확인 및 조정
            if y < 50:  # 화면 위쪽 경계
                y = event.y_root + 30
            
            self.hover_preview_window.geometry(f"+{x}+{y}")
            self.hover_preview_window.lift()
    
    def remove_attachment_by_index(self, index, item_type):
        """인덱스로 체부파일 제거"""
        if item_type == "image":
            if self.image_handler.current_mode == "multiple":
                self.remove_image_by_index(index)
            else:
                self.remove_image()
        else:
            # 파일 제거
            self.remove_file()
    
    # 기존 show_hover_preview 함수 제거 - show_attachment_preview 사용
    
    def hide_hover_preview(self):
        """호버 미리보기 숨기기"""
        if self.hover_preview_window:
            self.hover_preview_window.destroy()
            self.hover_preview_window = None
    
    def update_multiple_image_preview(self):
        """다중 이미지 미리보기 업데이트"""
        if self.image_handler.current_mode != "multiple":
            return
            
        # 기존 미리보기 제거
        for widget in self.image_preview_frame.winfo_children():
            widget.destroy()
        
        if not self.image_handler.has_image():
            self.image_preview_frame.pack_forget()
            return
        
        # 미리보기 프레임 표시
        self.image_preview_frame.pack(fill=tk.X, padx=15, pady=(15, 0))
        
        # 다중 이미지 컨테이너
        preview_container = tk.Frame(self.image_preview_frame, 
                                   bg=self.config.THEME["bg_input"], 
                                   relief=tk.SOLID, bd=1)
        preview_container.pack(fill=tk.X, pady=5)
        
        # 헤더 정보
        count = self.image_handler.get_image_count()
        header_frame = tk.Frame(preview_container, bg=self.config.THEME["bg_input"])
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        header_label = tk.Label(
            header_frame,
            text=f"🖼️ 이미지 {count}개 첨부됨 (최대 {self.image_handler.max_images}개)",
            bg=self.config.THEME["bg_input"],
            fg=self.config.THEME["fg_primary"],
            font=self.chat_font
        )
        header_label.pack(side=tk.LEFT)
        
        # 전체 삭제 버튼
        clear_all_button = tk.Button(
            header_frame,
            text="🗑️ 모두삭제",
            command=self.remove_all_images,
            font=("맑은 고딕", 9),
            bg="#ef4444",
            fg="#ffffff",
            border=0,
            padx=10, pady=4,
            activebackground="#dc2626",
            relief=tk.FLAT,
            cursor="hand2"
        )
        clear_all_button.pack(side=tk.RIGHT)
        
        # 이미지 그리드 컨테이너
        grid_frame = tk.Frame(preview_container, bg=self.config.THEME["bg_input"])
        grid_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 이미지들을 2x2 그리드로 배치
        for i in range(count):
            self.create_image_tile(grid_frame, i)
    
    def create_image_tile(self, parent, index):
        """개별 이미지 타일 생성"""
        row = index // 2
        col = index % 2
        
        # 타일 프레임
        tile_frame = tk.Frame(parent, bg=self.config.THEME["bg_secondary"], relief=tk.SOLID, bd=1)
        tile_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # 그리드 가중치 설정
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        
        # 이미지 미리보기
        preview_photo = self.image_handler.create_multiple_preview(index, (120, 80))
        if preview_photo:
            image_label = tk.Label(tile_frame, image=preview_photo, bg=self.config.THEME["bg_secondary"], cursor="hand2")
            image_label.image = preview_photo  # 참조 유지
            image_label.pack(side=tk.LEFT, padx=8, pady=8)
            
            # 이미지 클릭으로 큰 미리보기 창 열기
            image_label.bind("<Button-1>", lambda e, idx=index: self.show_image_detail(idx))
        
        # 정보 및 버튼 영역
        info_frame = tk.Frame(tile_frame, bg=self.config.THEME["bg_secondary"])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        
        # 파일명
        filename = self.image_handler.get_short_filename(index)
        if filename and len(filename) > 20:
            filename = filename[:17] + "..."
        
        filename_label = tk.Label(
            info_frame,
            text=filename or f"이미지 {index+1}",
            bg=self.config.THEME["bg_secondary"],
            fg=self.config.THEME["fg_primary"],
            font=("맑은 고딕", 9),
            anchor="w"
        )
        filename_label.pack(fill=tk.X)
        
        # 개별 삭제 버튼
        remove_button = tk.Button(
            info_frame,
            text="🗑️ 삭제",
            command=lambda idx=index: self.remove_image_by_index(idx),
            font=("맑은 고딕", 8),
            bg="#f87171",
            fg="#ffffff",
            border=0,
            padx=8, pady=2,
            activebackground="#ef4444",
            relief=tk.FLAT,
            cursor="hand2"
        )
        remove_button.pack(anchor="e", pady=(5, 0))
    
    def remove_image_by_index(self, index):
        """인덱스로 이미지 제거"""
        if self.image_handler.remove_image_by_index(index):
            self.update_attachment_tiles()  # 새로운 타일 시스템 사용
            
            # 버튼 상태 업데이트
            count = self.image_handler.get_image_count()
            if count == 0:
                self.update_attachment_button()
            elif count < self.image_handler.max_images:
                self.update_attachment_button()
    
    def remove_attachment_by_index(self, index, item_type):
        """인덱스로 첨부파일 제거 (이미지 또는 파일)"""
        if item_type == "image":
            # 이미지 제거
            if self.image_handler.remove_image_by_index(index):
                self.update_attachment_tiles()
                self.update_attachment_button()
        elif item_type == "file":
            # 파일 제거 - 실제 파일 리스트에서의 인덱스 계산
            image_count = self.image_handler.get_image_count()
            file_index = index - image_count
            if self.file_handler.remove_file_by_index(file_index):
                self.update_attachment_tiles()
                self.update_attachment_button()
    
    def remove_all_images(self):
        """모든 이미지 제거"""
        self.image_handler.clear_all_images()
        self.update_attachment_tiles()  # 새로운 타일 시스템 사용
        self.update_attachment_button()
    
    def show_image_detail(self, index):
        """특정 인덱스의 이미지를 큰 미리보기 창에서 표시"""
        if self.image_handler.current_mode == "multiple" and 0 <= index < self.image_handler.get_image_count():
            self.preview_window.show_preview(self.image_handler, index)
    
    def show_file_preview(self, filename):
        """파일 미리보기 표시 (더 이상 사용하지 않음 - 타일 시스템으로 대체됨)"""
        # 이 함수는 타일 시스템으로 대체되었으므로 update_attachment_tiles()를 호출합니다.
        self.update_attachment_tiles()
    
    def remove_file(self):
        """선택된 파일 제거 (더 이상 사용하지 않음 - remove_all_attachments로 대체됨)"""
        self.remove_all_attachments()
    
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
        multiple_images = None
        
        # 이미지 정보
        if self.image_handler.has_image():
            image_info = self.image_handler.get_image_info()
            
            if self.image_handler.current_mode == "multiple" and self.image_handler.get_image_count() > 1:
                # 다중 이미지 모드
                multiple_images = self.image_handler.get_all_chat_previews()
            else:
                # 단일 이미지 모드
                chat_image_preview = self.image_handler.create_chat_preview()
        
        # 파일 정보 (다중 파일 지원)
        file_info = None
        multiple_files_info = []
        if self.file_handler.has_file():
            if self.file_handler.current_mode == "multiple" and self.file_handler.get_file_count() > 1:
                # 다중 파일 모드
                for i in range(self.file_handler.get_file_count()):
                    info = self.file_handler.get_file_info_by_index(i)
                    if info:
                        multiple_files_info.append(info)
                file_info = f"파일 {self.file_handler.get_file_count()}개 첨부"
            else:
                # 단일 파일 또는 파일 1개
                file_info = self.file_handler.get_file_info()
        
        # 메시지 표시 (다중 이미지 우선)
        if multiple_images and len(multiple_images) > 1:
            self.chat_display.display_user_message(user_input, image_info, None, file_info, multiple_images)
        elif image_info and file_info:
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
        if multiple_files_info:
            combined_attachment.extend(multiple_files_info)
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
                
                # 이미지 처리 (다중 또는 단일)
                images = self.image_handler.get_images_for_api()
                for image in images:
                    if image:
                        message_parts.append(image)
                
                # 파일이 있으면 추가 (다중 파일 지원)
                file_contents = self.file_handler.get_all_files_for_api()
                for file_content in file_contents:
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
        
        # 미리보기 창 닫기
        if self.preview_window and self.preview_window.is_open():
            self.preview_window.close_window()
        
        # 이미지와 파일 초기화
        if self.image_handler.has_image():
            self.image_handler.clear_all_images()
            self.update_attachment_tiles()  # 새로운 타일 시스템 사용
            if self.image_handler.current_mode == "multiple":
                self.update_attachment_button()
            else:
                self.update_attachment_button()
        
        if self.file_handler.has_file():
            self.file_handler.clear_all_files()
            self.update_attachment_tiles()  # 새로운 타일 시스템 사용 (같은 프레임 사용)
            self.update_attachment_button()
        
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
        
        # 새로운 통합 파일 처리 함수 사용
        self.process_selected_file(file_path)
        
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
                
                # 기존 이미지가 있으면 모드에 따라 처리
                if self.image_handler.has_image():
                    if self.image_handler.current_mode == "single":
                        result = messagebox.askyesno(
                            "이미지 교체", 
                            "이미 선택된 이미지가 있습니다. 클립보드의 이미지로 교체하시겠습니까?"
                        )
                        if not result:
                            os.remove(temp_path)
                            return "break"
                    elif self.image_handler.get_image_count() >= self.image_handler.max_images:
                        messagebox.showwarning(
                            "이미지 최대 개수",
                            f"최대 {self.image_handler.max_images}개까지만 추가할 수 있습니다."
                        )
                        os.remove(temp_path)
                        return "break"
                
                # 이미지 로드
                success, error_msg = self.image_handler.load_image(temp_path)
                if success:
                    # 새로운 타일 기반 미리보기 시스템 사용
                    self.update_attachment_tiles()
                    
                    if self.image_handler.current_mode == "multiple":
                        # 다중 모드
                        count = self.image_handler.get_image_count()
                        
                        if count >= self.image_handler.max_images:
                            pass  # 최대 개수 도달은 update_attachment_button에서 처리
                        else:
                            self.update_attachment_button()
                        messagebox.showinfo("이미지 첨부", f"클립보드의 이미지가 추가되었습니다. ({count}/{self.image_handler.max_images})")
                    else:
                        # 단일 모드
                        self.update_attachment_button()
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