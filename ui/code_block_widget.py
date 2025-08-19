"""
접기/펼기 가능한 코드 블록 위젯
"""

import tkinter as tk
from tkinter import scrolledtext
import re

class CodeBlockWidget(tk.Frame):
    """접기/펼기 가능한 코드 블록 위젯"""
    
    def __init__(self, parent, code_content: str, language: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.code_content = code_content.strip()
        self.language = language
        self.is_collapsed = True  # 기본값: 접혀있음
        
        # 코드 라인들
        self.code_lines = [line for line in self.code_content.split('\n') if line.strip()]
        
        self.setup_ui()
        
        # 3줄 이하면 접기 기능 비활성화
        if len(self.code_lines) <= 3:
            self.toggle_btn.configure(state='disabled', text="📄 짧음")
            self.is_collapsed = False
            self.show_full_code()
        else:
            self.show_preview()
    
    def setup_ui(self):
        """UI 구성"""
        self.configure(bg="#2b2b2b", relief=tk.SOLID, bd=1)
        
        # 헤더 프레임
        self.header_frame = tk.Frame(self, bg="#2b2b2b")
        self.header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 토글 버튼
        self.toggle_btn = tk.Button(
            self.header_frame,
            text="📂 펼치기",
            bg="#4a4a4a", fg="#ffffff",
            font=("맑은 고딕", 9),
            relief=tk.FLAT, bd=0,
            cursor="hand2",
            command=self.toggle_code
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        # 언어 라벨
        lang_display = f" {self.language} " if self.language else " 코드 "
        self.lang_label = tk.Label(
            self.header_frame,
            text=lang_display,
            bg="#2b2b2b", fg="#ffffff",
            font=("맑은 고딕", 10)
        )
        self.lang_label.pack(side=tk.LEFT, padx=5)
        
        # 미리보기 라벨 (접힌 상태에서만 표시)
        self.preview_label = tk.Label(
            self.header_frame,
            text="",
            bg="#2b2b2b", fg="#888888",
            font=("맑은 고딕", 8)
        )
        
        # 복사 버튼
        self.copy_btn = tk.Button(
            self.header_frame,
            text="📋 복사",
            bg="#4a4a4a", fg="#ffffff",
            font=("맑은 고딕", 9),
            relief=tk.FLAT, bd=0,
            cursor="hand2",
            command=self.copy_code
        )
        self.copy_btn.pack(side=tk.RIGHT, padx=5)
        
        # 코드 표시 영역
        self.code_frame = tk.Frame(self, bg="#1e1e1e")
        
        # 코드 텍스트 위젯
        self.code_text = tk.Text(
            self.code_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#1e1e1e", fg="#d4d4d4",
            relief=tk.FLAT, bd=0,
            padx=10, pady=10,
            state=tk.DISABLED,
            selectbackground="#094771"
        )
        
        # 스크롤바
        self.scrollbar = tk.Scrollbar(self.code_frame, orient=tk.VERTICAL, command=self.code_text.yview)
        self.code_text.configure(yscrollcommand=self.scrollbar.set)
        
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_preview(self):
        """접힌 상태: 미리보기만 표시"""
        # 코드 영역 숨기기
        self.code_frame.pack_forget()
        
        # 미리보기 텍스트 생성
        preview_lines = self.code_lines[:3]
        preview_text = " | ".join(
            line.strip()[:25] + ("..." if len(line.strip()) > 25 else "")
            for line in preview_lines if line.strip()
        )
        
        remaining = len(self.code_lines) - 3
        self.preview_label.configure(text=f"{preview_text} (+{remaining}줄)")
        self.preview_label.pack(side=tk.LEFT, padx=10)
        
        self.toggle_btn.configure(text="📂 펼치기")
        self.is_collapsed = True
    
    def show_full_code(self):
        """펼친 상태: 전체 코드 표시"""
        # 미리보기 라벨 숨기기
        self.preview_label.pack_forget()
        
        # 코드 영역 표시
        self.code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 코드 내용 삽입
        self.code_text.configure(state=tk.NORMAL)
        self.code_text.delete('1.0', tk.END)
        self.code_text.insert('1.0', self.code_content)
        self.code_text.configure(state=tk.DISABLED)
        
        # 높이 조정 (최대 15줄)
        line_count = min(len(self.code_lines), 15)
        self.code_text.configure(height=line_count)
        
        self.toggle_btn.configure(text="📁 접기")
        self.is_collapsed = False
    
    def toggle_code(self):
        """코드 접기/펼치기 토글"""
        if self.is_collapsed:
            self.show_full_code()
        else:
            self.show_preview()
    
    def copy_code(self):
        """코드 복사"""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.code_content)
            
            # 복사 완료 피드백
            original_text = self.copy_btn.cget("text")
            self.copy_btn.configure(text="✅ 복사됨")
            self.after(2000, lambda: self.copy_btn.configure(text=original_text))
            
        except Exception as e:
            print(f"복사 오류: {e}")

class AdvancedMarkdownRenderer:
    """코드 블록 위젯을 사용하는 고급 마크다운 렌더러"""
    
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.base_font = ("맑은 고딕", 13)
        self.code_widgets = []  # 생성된 코드 위젯들 추적
    
    def render_markdown(self, text: str):
        """마크다운 렌더링 (코드 블록 위젯 포함)"""
        # 기존 코드 위젯들 정리
        for widget in self.code_widgets:
            try:
                widget.destroy()
            except:
                pass
        self.code_widgets.clear()
        
        # 코드 블록과 일반 텍스트 분리
        parts = self.split_content_with_code_blocks(text)
        
        for part in parts:
            if part['type'] == 'code':
                self.insert_code_widget(part['content'], part['language'])
            else:
                self.render_normal_text(part['content'])
    
    def split_content_with_code_blocks(self, text: str):
        """텍스트를 코드 블록과 일반 텍스트로 분리"""
        parts = []
        lines = text.split('\n')
        current_text = []
        in_code_block = False
        current_code = []
        current_language = ""
        
        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:
                    # 코드 블록 시작
                    if current_text:
                        parts.append({
                            'type': 'text',
                            'content': '\n'.join(current_text)
                        })
                        current_text = []
                    
                    in_code_block = True
                    current_language = line.strip()[3:].strip()
                    current_code = []
                else:
                    # 코드 블록 종료
                    in_code_block = False
                    if current_code:
                        parts.append({
                            'type': 'code',
                            'content': '\n'.join(current_code),
                            'language': current_language
                        })
                    current_code = []
                    current_language = ""
            elif in_code_block:
                current_code.append(line)
            else:
                current_text.append(line)
        
        # 남은 내용 처리
        if current_text:
            parts.append({
                'type': 'text',
                'content': '\n'.join(current_text)
            })
        
        if in_code_block and current_code:
            parts.append({
                'type': 'code',
                'content': '\n'.join(current_code),
                'language': current_language
            })
        
        return parts
    
    def insert_code_widget(self, code_content: str, language: str):
        """코드 블록 위젯 삽입"""
        if not code_content.strip():
            return
        
        # 코드 위젯 생성
        code_widget = CodeBlockWidget(
            self.text_widget,
            code_content,
            language,
            bg="#2b2b2b"
        )
        
        # 텍스트 위젯에 삽입
        self.text_widget.window_create(tk.END, window=code_widget)
        self.text_widget.insert(tk.END, "\n\n")
        
        # 위젯 추적
        self.code_widgets.append(code_widget)
    
    def render_normal_text(self, text: str):
        """일반 텍스트 렌더링 (기존 마크다운 기능)"""
        if not text.strip():
            return
        
        # 간단한 마크다운 처리
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                self.text_widget.insert(tk.END, "\n")
                continue
            
            # 헤더 처리
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('# ').strip()
                prefix = "■ " if level == 1 else "▲ " if level == 2 else "● "
                self.text_widget.insert(tk.END, prefix + header_text + "\n", "header")
            # 리스트 처리
            elif line.strip().startswith(('- ', '* ', '+ ')):
                list_text = line.strip()[2:]
                self.text_widget.insert(tk.END, f"• {list_text}\n", "list")
            else:
                # 인라인 마크다운 처리
                self.render_inline_markdown(line + '\n')
    
    def render_inline_markdown(self, text: str):
        """인라인 마크다운 처리"""
        # 간단한 볼드/이탤릭 처리
        current_pos = 0
        while current_pos < len(text):
            # **볼드** 처리
            bold_match = re.search(r'\*\*(.*?)\*\*', text[current_pos:])
            if bold_match:
                start = current_pos + bold_match.start()
                end = current_pos + bold_match.end()
                
                # 매치 전 텍스트
                if start > current_pos:
                    self.text_widget.insert(tk.END, text[current_pos:start])
                
                # 볼드 텍스트
                self.text_widget.insert(tk.END, bold_match.group(1), "bold")
                current_pos = end
            else:
                # 남은 텍스트
                self.text_widget.insert(tk.END, text[current_pos:])
                break
    
    def update_font(self, font_tuple):
        """폰트 업데이트"""
        self.base_font = font_tuple
        self.setup_styles()
    
    def setup_styles(self):
        """스타일 설정"""
        font_family, font_size = self.base_font
        
        self.text_widget.tag_configure("header", 
                                      font=(font_family, font_size + 2, "bold"),
                                      foreground="#4A90E2")
        self.text_widget.tag_configure("list", 
                                      font=(font_family, font_size),
                                      lmargin1=20, lmargin2=20)
        self.text_widget.tag_configure("bold", 
                                      font=(font_family, font_size, "bold"))