"""
채팅 디스플레이 UI 컴포넌트
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from typing import Optional, Dict

from config.settings import AppConfig, FontSettings
from utils.markdown_parser_v2 import MarkdownRenderer
# from ui.code_block_widget import AdvancedMarkdownRenderer  # 구버전 제거

class ChatDisplay:
    """채팅 디스플레이 클래스"""
    
    def __init__(self, parent: tk.Widget, config: AppConfig):
        self.config = config
        self.parent = parent
        
        # 폰트 설정
        self.font_settings = config.font_settings
        self.chat_font = self.font_settings.get_chat_font()
        
        # 스트리밍 관련
        self.is_streaming = False
        self.stream_buffer = ""
        self.stream_start_pos = None
        
        # 이미지 참조 유지를 위한 리스트
        self.image_references = []
        
        self.create_display()
        self.setup_styles()
        
        # 새로운 마크다운 v2 렌더러 (통합)
        self.markdown_renderer = MarkdownRenderer(self.chat_display)
        self.markdown_renderer.update_font(self.chat_font)
        
        # 스트리밍용도 같은 렌더러 사용
        self.advanced_renderer = self.markdown_renderer
        
    
    def create_display(self):
        """채팅 디스플레이 생성"""
        # 채팅 영역 전체 컨테이너
        self.chat_container = tk.Frame(self.parent, 
                                      bg=self.config.THEME["bg_secondary"], 
                                      relief=tk.FLAT)
        self.chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 채팅 디스플레이
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_container,
            wrap=tk.WORD,
            font=self.chat_font,
            bg=self.config.THEME["bg_secondary"],
            fg=self.config.THEME["fg_secondary"],
            selectbackground="#4338ca",
            insertbackground=self.config.THEME["fg_primary"],
            relief=tk.FLAT,
            borderwidth=0,
            padx=25,
            pady=25
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.chat_display.config(state=tk.DISABLED)
        
    
    def setup_styles(self):
        """채팅 스타일 설정"""
        # 사용자 메시지 스타일 - 버블 스타일
        self.chat_display.tag_configure("user_name", 
                                      foreground=self.config.THEME["fg_user"], 
                                      font=(self.chat_font[0], self.chat_font[1], "bold"))
        self.chat_display.tag_configure("user_text", 
                                      foreground=self.config.THEME["fg_primary"], 
                                      font=self.chat_font,
                                      lmargin1=30, lmargin2=30,
                                      rmargin=50,
                                      spacing1=8, spacing3=8)
        
        # AI 메시지 스타일 - 버블 스타일
        self.chat_display.tag_configure("bot_name", 
                                      foreground=self.config.THEME["fg_accent"], 
                                      font=(self.chat_font[0], self.chat_font[1], "bold"))
        self.chat_display.tag_configure("bot_text", 
                                      foreground=self.config.THEME["fg_secondary"], 
                                      font=self.chat_font,
                                      lmargin1=30, lmargin2=30,
                                      rmargin=50,
                                      spacing1=8, spacing3=8)
        
        # 시간 스타일
        self.chat_display.tag_configure("timestamp", 
                                      foreground=self.config.THEME["fg_timestamp"], 
                                      font=(self.chat_font[0], self.chat_font[1]-2, "italic"),
                                      lmargin1=10, spacing3=5)
        
        # 시스템 메시지 스타일
        self.chat_display.tag_configure("system", 
                                      foreground=self.config.THEME["fg_system"], 
                                      font=(self.chat_font[0], self.chat_font[1], "italic"),
                                      justify=tk.CENTER,
                                      lmargin1=50, lmargin2=50,
                                      rmargin=50,
                                      spacing1=10, spacing3=10)
        
        # 이미지 첨부 표시 스타일
        self.chat_display.tag_configure("image_indicator", 
                                      foreground="#E1BEE7", 
                                      font=(self.chat_font[0], self.chat_font[1], "bold"))
        
        # 파일 첨부 표시 스타일
        self.chat_display.tag_configure("file_indicator", 
                                      foreground="#8b5cf6", 
                                      font=(self.chat_font[0], self.chat_font[1], "bold"))
        
        # 기타 첨부 표시 스타일
        self.chat_display.tag_configure("attachment_indicator", 
                                      foreground="#6b7280", 
                                      font=(self.chat_font[0], self.chat_font[1], "bold"))
        
        # 새로운 마크다운 v2 스타일 시스템
        self._configure_markdown_v2_styles()
        
        # 기존 호환성 스타일 (제거 예정)
        self.chat_display.tag_configure("markdown_bold", 
                                      foreground=self.config.THEME["fg_primary"], 
                                      font=(self.chat_font[0], self.chat_font[1], "bold"),
                                      lmargin1=35, lmargin2=35, rmargin=55)
        self.chat_display.tag_configure("markdown_italic", 
                                      foreground=self.config.THEME["fg_secondary"], 
                                      font=(self.chat_font[0], self.chat_font[1], "italic"),
                                      lmargin1=35, lmargin2=35, rmargin=55)
        self.chat_display.tag_configure("markdown_code", 
                                      foreground="#fbbf24", 
                                      font=("Consolas", self.chat_font[1], "normal"),
                                      background="#374151",
                                      lmargin1=35, lmargin2=35, rmargin=55)
        self.chat_display.tag_configure("markdown_code_block", 
                                      foreground="#f3f4f6", 
                                      font=("Consolas", self.chat_font[1], "normal"),
                                      background="#111827",
                                      lmargin1=40, lmargin2=40, rmargin=40,
                                      spacing1=5, spacing3=5)
        self.chat_display.tag_configure("markdown_header", 
                                      foreground="#60a5fa", 
                                      font=(self.chat_font[0], self.chat_font[1]+3, "bold"),
                                      lmargin1=35, lmargin2=35, rmargin=55,
                                      spacing1=5, spacing3=5)
        self.chat_display.tag_configure("markdown_header_bold", 
                                      foreground="#60a5fa", 
                                      font=(self.chat_font[0], self.chat_font[1]+3, "bold"),
                                      lmargin1=35, lmargin2=35, rmargin=55,
                                      spacing1=5, spacing3=5)
        self.chat_display.tag_configure("markdown_list", 
                                      foreground=self.config.THEME["fg_secondary"], 
                                      font=self.chat_font,
                                      lmargin1=50, lmargin2=50, rmargin=55)
        self.chat_display.tag_configure("markdown_hr", 
                                      foreground="#6b7280", 
                                      font=self.chat_font,
                                      justify=tk.CENTER,
                                      lmargin1=35, lmargin2=35, rmargin=55,
                                      spacing1=5, spacing3=5)
        
        # 스트리밍 텍스트 스타일
        self.chat_display.tag_configure("streaming", 
                                      foreground=self.config.THEME["fg_secondary"], 
                                      font=self.chat_font,
                                      lmargin1=30, lmargin2=30, rmargin=50,
                                      spacing1=8, spacing3=8)
        
        
    
    def display_welcome_message(self, current_model_display: str, generation_params: dict):
        """환영 메시지 표시"""
        welcome_text = f"""🌟 Gemini Chat Studio에 오신 것을 환영합니다!

✨ 주요 기능
• 🌊 실시간 스트리밍 응답
• 🖼️ 이미지 분석 및 대화  
• ⚙️ 사용자 지정 설정
• 📊 사용량 모니터링

🚀 빠른 시작
• 메시지를 입력하고 Enter로 전송
• 🖼️ 버튼으로 이미지 첨부
• 드래그 & 드롭 또는 Ctrl+V로 이미지 추가

📈 현재 설정: {current_model_display} | 최대 {generation_params['max_output_tokens']:,} 토큰

지금 바로 대화를 시작해보세요! 💬

"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, welcome_text, "system")
        self.chat_display.insert(tk.END, "="*80 + "\n\n", "system")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def display_system_message(self, message: str):
        """시스템 메시지 표시"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{message}\n", "system")
        self.chat_display.insert(tk.END, "-" * 50 + "\n\n", "system")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def display_user_message(self, message: str, attachment_info: Optional[str] = None, image_preview=None, file_info: Optional[str] = None, multiple_images: list = None):
        """사용자 메시지 표시 (다중 이미지 지원)"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.insert(tk.END, f"\n👤 You", "user_name")
        self.chat_display.insert(tk.END, f" • {timestamp}\n", "timestamp")
        
        # 첨부파일 정보 표시
        attachments_shown = False
        
        # 다중 이미지 표시 (우선순위)
        if multiple_images and len(multiple_images) > 1:
            self.display_multiple_images_in_chat(multiple_images)
            attachments_shown = True
        # 단일 이미지 첨부 시각적 표시 (기존 방식)
        elif image_preview:
            # 이미지를 채팅창에 직접 삽입
            self.chat_display.image_create(tk.END, image=image_preview)
            self.chat_display.insert(tk.END, "\n")
            # 이미지 참조 유지 (가비지 컬렉션 방지)
            self.image_references.append(image_preview)
            attachments_shown = True
        
        # 이미지 정보 표시
        if attachment_info and "이미지" in attachment_info:
            self.chat_display.insert(tk.END, f"🖼️ {attachment_info}\n", "image_indicator")
            attachments_shown = True
        
        # 파일 정보 표시
        if file_info:
            self.chat_display.insert(tk.END, f"📄 {file_info}\n", "file_indicator")
            attachments_shown = True
        
        # 기타 첨부 정보 표시
        if attachment_info and "이미지" not in attachment_info and not file_info:
            self.chat_display.insert(tk.END, f"📎 {attachment_info}\n", "attachment_indicator")
            attachments_shown = True
        
        # 버블 스타일로 메시지 표시 (새로운 마크다운 v2 렌더링 적용)
        self.chat_display.insert(tk.END, " ", "user_text")
        # 사용자 메시지에도 마크다운 렌더링 적용
        self.markdown_renderer.render_markdown(message)
        self.chat_display.insert(tk.END, " \n\n", "user_text")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def start_bot_response(self, model_display_name: str):
        """봇 응답 시작 (헤더 표시)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"🤖 {model_display_name}", "bot_name")
        self.chat_display.insert(tk.END, f" • {timestamp}\n", "timestamp")
        
        # 스트리밍 응답 시작 위치 저장
        self.stream_start_pos = self.chat_display.index(tk.END)
        
        self.chat_display.config(state=tk.DISABLED)
        
        self.is_streaming = True
        self.stream_buffer = ""
    
    def display_streaming_chunk(self, chunk_text: str):
        """스트리밍 텍스트 청크 표시"""
        if not self.is_streaming:
            return
            
        # 스트리밍 중에는 버퍼에만 저장하고 화면에는 표시하지 않음
        self.stream_buffer += chunk_text
    
    def finalize_streaming_response(self, full_response: str, model_display_name: str):
        """스트리밍 응답 완료 후 마크다운으로 최종 렌더링"""
        print(f"[DEBUG] finalize_streaming_response called, is_streaming: {self.is_streaming}")
        
        if not self.is_streaming:
            print("[DEBUG] Already completed or stopped, returning")
            return  # 이미 완료되었거나 중단된 경우
            
        self.chat_display.config(state=tk.NORMAL)
        
        # 고급 마크다운 렌더러로 코드 블록 위젯 포함하여 렌더링
        print(f"[DEBUG] Rendering advanced markdown for response length: {len(full_response)}")
        self.advanced_renderer.render_markdown(full_response)
        
        
        self.chat_display.insert(tk.END, "\n")
        print("[DEBUG] Markdown rendering completed")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        self.is_streaming = False
        self.stream_buffer = ""
        self.stream_start_pos = None
    
    def _delete_last_bot_response(self, model_display_name: str):
        """마지막 봇 응답 이후의 텍스트 삭제"""
        print("[DEBUG] _delete_last_bot_response called")
        content = self.chat_display.get(1.0, tk.END)
        lines = content.split('\n')
        print(f"[DEBUG] Total lines in content: {len(lines)}")
        
        # 마지막 봇 응답 헤더 찾기
        for i in range(len(lines) - 1, -1, -1):
            if f"🤖 {model_display_name}" in lines[i]:
                print(f"[DEBUG] Found bot header at line {i}: {lines[i][:50]}...")
                # 헤더 다음 라인부터 삭제
                line_start = sum(len(line) + 1 for line in lines[:i+1])
                delete_pos = f"1.0 + {line_start}c"
                print(f"[DEBUG] Calculated delete position: {delete_pos}")
                try:
                    self.chat_display.delete(delete_pos, tk.END)
                    print("[DEBUG] Backup deletion successful")
                except tk.TclError as e:
                    print(f"[DEBUG] Backup deletion failed: {e}, trying alternative")
                    # 삭제 실패 시 전체 내용을 다시 가져와서 처리
                    self.chat_display.delete(f"{i+2}.0", tk.END)
                break
    
    def display_bot_message(self, message: str):
        """봇 메시지 표시 (비스트리밍)"""
        self.chat_display.config(state=tk.NORMAL)
        self.markdown_renderer.render_markdown(message)
        
        
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def clear_display(self):
        """디스플레이 초기화"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.is_streaming = False
        self.stream_buffer = ""
        self.stream_start_pos = None
        
        # 이미지 참조 초기화
        self.image_references.clear()
        
        # 새로운 마크다운 v2 렌더러의 코드 블록 초기화
        if hasattr(self.markdown_renderer, 'clear_code_blocks'):
            self.markdown_renderer.clear_code_blocks()
    
    def get_widget(self) -> scrolledtext.ScrolledText:
        """위젯 반환"""
        return self.chat_display
    
    def update_fonts(self, font_settings: FontSettings):
        """폰트 설정 업데이트"""
        self.font_settings = font_settings
        self.chat_font = font_settings.get_chat_font()
        
        # 채팅 디스플레이 폰트 업데이트
        self.chat_display.configure(font=self.chat_font)
        
        # 스타일 다시 설정
        self.setup_styles()
        
        # 마크다운 렌더러 폰트 업데이트
        if hasattr(self.markdown_renderer, 'update_font'):
            self.markdown_renderer.update_font(self.chat_font)
    
    def _configure_markdown_v2_styles(self):
        """새로운 마크다운 v2 스타일 설정"""
        font_family, font_size = self.chat_font
        
        # 기본 텍스트
        self.chat_display.tag_configure("md_text", 
                                      foreground=self.config.THEME["fg_secondary"],
                                      font=(font_family, font_size),
                                      lmargin1=30, lmargin2=30, rmargin=50)
        
        # 헤더 스타일 (1-6)
        for i in range(1, 7):
            size_offset = max(6 - i, 0)
            # 모든 헤더를 하늘색으로
            header_color = "#87CEEB"
            
            self.chat_display.tag_configure(f"md_header_{i}", 
                                          foreground=header_color,
                                          font=(font_family, font_size + size_offset, "bold"),
                                          lmargin1=30, lmargin2=30, rmargin=50,
                                          spacing1=8, spacing3=4)
            # 헤더 내 볼드
            self.chat_display.tag_configure(f"md_header_{i}_bold", 
                                          foreground=header_color,
                                          font=(font_family, font_size + size_offset, "bold"),
                                          lmargin1=30, lmargin2=30, rmargin=50)
        
        # 인라인 스타일
        self.chat_display.tag_configure("md_bold", 
                                      foreground=self.config.THEME["fg_primary"],
                                      font=(font_family, font_size, "bold"),
                                      lmargin1=30, lmargin2=30, rmargin=50)
        
        self.chat_display.tag_configure("md_italic", 
                                      foreground=self.config.THEME["fg_secondary"],
                                      font=(font_family, font_size, "italic"),
                                      lmargin1=30, lmargin2=30, rmargin=50)
        
        self.chat_display.tag_configure("md_code_inline", 
                                      foreground="#DC2626",
                                      background="#F3F4F6",
                                      font=("Consolas", font_size),
                                      lmargin1=30, lmargin2=30, rmargin=50)
        
        # 블록 스타일
        self.chat_display.tag_configure("md_quote", 
                                      foreground="#6B7280",
                                      font=(font_family, font_size, "italic"),
                                      lmargin1=40, lmargin2=40, rmargin=60,
                                      background="#F9FAFB")
        
        self.chat_display.tag_configure("md_list", 
                                      foreground=self.config.THEME["fg_secondary"],
                                      font=(font_family, font_size),
                                      lmargin1=40, lmargin2=40, rmargin=60)
        
        self.chat_display.tag_configure("md_list_bold", 
                                      foreground=self.config.THEME["fg_primary"],
                                      font=(font_family, font_size, "bold"),
                                      lmargin1=40, lmargin2=40, rmargin=60)
        
        self.chat_display.tag_configure("md_hr", 
                                      foreground="#D1D5DB",
                                      font=(font_family, font_size),
                                      lmargin1=30, lmargin2=30, rmargin=50,
                                      justify=tk.CENTER)
        
        # 코드 블록
        self.chat_display.tag_configure("md_code_block", 
                                      foreground="#F9FAFB",
                                      background="#1F2937",
                                      font=("Consolas", font_size - 1),
                                      lmargin1=35, lmargin2=35, rmargin=55)
    
    def display_multiple_images_in_chat(self, image_previews: list):
        """채팅창에 다중 이미지 표시"""
        if not image_previews:
            return
        
        # 이미지 그리드 컨테이너 생성
        images_frame = tk.Frame(self.chat_display, bg=self.config.THEME["bg_secondary"])
        
        # 이미지를 2x2 그리드로 배치
        for i, preview in enumerate(image_previews[:4]):  # 최대 4개만 표시
            if preview:
                row = i // 2
                col = i % 2
                
                # 개별 이미지 프레임
                img_frame = tk.Frame(images_frame, bg=self.config.THEME["bg_secondary"], 
                                   relief=tk.SOLID, bd=1)
                img_frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
                
                # 이미지 라벨
                img_label = tk.Label(img_frame, image=preview, bg=self.config.THEME["bg_secondary"])
                img_label.pack(padx=4, pady=4)
                
                # 이미지 번호
                num_label = tk.Label(img_frame, text=f"{i+1}", 
                                   bg=self.config.THEME["bg_secondary"],
                                   fg=self.config.THEME["fg_accent"],
                                   font=("맑은 고딕", 8, "bold"))
                num_label.pack()
                
                # 이미지 참조 유지
                self.image_references.append(preview)
        
        # 그리드 가중치 설정
        images_frame.grid_columnconfigure(0, weight=1)
        images_frame.grid_columnconfigure(1, weight=1)
        
        # 채팅창에 프레임 삽입
        self.chat_display.window_create(tk.END, window=images_frame)
        self.chat_display.insert(tk.END, "\n")
        
        # 이미지 개수 정보
        count = len(image_previews)
        if count > 4:
            self.chat_display.insert(tk.END, f"📸 이미지 {count}개 (처음 4개만 표시)\n", "image_indicator")
        else:
            self.chat_display.insert(tk.END, f"📸 이미지 {count}개\n", "image_indicator")
