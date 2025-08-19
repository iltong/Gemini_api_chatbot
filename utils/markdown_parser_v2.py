"""
최적화된 마크다운 파서 v2
토큰 기반 파싱으로 일관된 렌더링 보장
"""

import re
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """토큰 타입 정의"""
    TEXT = "text"
    BOLD = "bold" 
    ITALIC = "italic"
    CODE_INLINE = "code_inline"
    CODE_BLOCK = "code_block"
    HEADER = "header"
    LIST_ITEM = "list_item"
    NUMBERED_LIST = "numbered_list"
    QUOTE = "quote"
    LINE_BREAK = "line_break"
    HORIZONTAL_RULE = "horizontal_rule"


@dataclass
class Token:
    """마크다운 토큰"""
    type: TokenType
    content: str
    level: int = 0  # 헤더 레벨, 리스트 들여쓰기 등
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MarkdownTokenizer:
    """마크다운 텍스트를 토큰으로 변환"""
    
    # 패턴 우선순위 (순서 중요)
    PATTERNS = [
        # 코드 블록 (가장 높은 우선순위)
        (r'^```(\w*)\n(.*?)\n```$', TokenType.CODE_BLOCK, True),
        # 헤더
        (r'^(#{1,6})\s+(.+)$', TokenType.HEADER, False),
        # 수평선
        (r'^(\*{3,}|-{3,}|_{3,})\s*$', TokenType.HORIZONTAL_RULE, False),
        # 인용구
        (r'^>\s*(.+)$', TokenType.QUOTE, False),
        # 리스트 (번호 있는)
        (r'^(\s*)\d+\.\s+(.+)$', TokenType.NUMBERED_LIST, False),
        # 리스트 (번호 없는)
        (r'^(\s*)[-*+]\s+(.+)$', TokenType.LIST_ITEM, False),
    ]
    
    # 인라인 패턴 (순서 중요)
    INLINE_PATTERNS = [
        (r'\*\*\*(.+?)\*\*\*', TokenType.BOLD),  # 굵은 기울임은 굵게로 처리
        (r'\*\*(.+?)\*\*', TokenType.BOLD),
        (r'(?<!\*)\*(.+?)\*(?!\*)', TokenType.ITALIC),
        (r'`(.+?)`', TokenType.CODE_INLINE),
    ]
    
    def tokenize(self, text: str) -> List[Token]:
        """텍스트를 토큰 목록으로 변환"""
        tokens = []
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 빈 줄 처리
            if not line.strip():
                tokens.append(Token(TokenType.LINE_BREAK, "\n"))
                i += 1
                continue
            
            # 코드 블록 처리 (여러 줄)
            if line.strip().startswith('```'):
                code_token, consumed_lines = self._parse_code_block(lines, i)
                if code_token:
                    tokens.append(code_token)
                    i += consumed_lines
                    continue
            
            # 블록 레벨 요소 처리
            block_token = self._parse_block_element(line)
            if block_token:
                # 블록 내 인라인 요소 처리
                inline_tokens = self._parse_inline_elements(block_token.content)
                if inline_tokens:
                    # 블록 토큰에 인라인 토큰들을 메타데이터로 저장
                    block_token.metadata['inline_tokens'] = inline_tokens
                tokens.append(block_token)
            else:
                # 일반 텍스트 라인의 인라인 요소 처리
                inline_tokens = self._parse_inline_elements(line)
                if inline_tokens:
                    for token in inline_tokens:
                        tokens.append(token)
                else:
                    tokens.append(Token(TokenType.TEXT, line))
            
            tokens.append(Token(TokenType.LINE_BREAK, "\n"))
            i += 1
        
        return tokens
    
    def _parse_code_block(self, lines: List[str], start_idx: int) -> Tuple[Optional[Token], int]:
        """코드 블록 파싱"""
        if not lines[start_idx].strip().startswith('```'):
            return None, 0
        
        language = lines[start_idx].strip()[3:].strip()
        content_lines = []
        i = start_idx + 1
        
        while i < len(lines):
            if lines[i].strip() == '```':
                code_content = '\n'.join(content_lines)
                return Token(
                    TokenType.CODE_BLOCK, 
                    code_content,
                    metadata={'language': language}
                ), i - start_idx + 1
            content_lines.append(lines[i])
            i += 1
        
        # 닫는 ``` 없는 경우 - 일반 텍스트로 처리
        return None, 0
    
    def _parse_block_element(self, line: str) -> Optional[Token]:
        """블록 레벨 요소 파싱"""
        for pattern, token_type, is_multiline in self.PATTERNS:
            if is_multiline:
                continue  # 멀티라인은 별도 처리
            
            match = re.match(pattern, line)
            if match:
                if token_type == TokenType.HEADER:
                    level = len(match.group(1))
                    content = match.group(2)
                    return Token(token_type, content, level=level)
                
                elif token_type == TokenType.LIST_ITEM:
                    indent = len(match.group(1))
                    content = match.group(2)
                    return Token(token_type, content, level=indent)
                
                elif token_type == TokenType.NUMBERED_LIST:
                    indent = len(match.group(1))
                    content = match.group(2)
                    # 원본 라인에서 번호 추출
                    number_match = re.search(r'(\d+)\.', line)
                    number = number_match.group(1) if number_match else "1"
                    return Token(token_type, content, level=indent, metadata={'number': number})
                
                elif token_type == TokenType.QUOTE:
                    content = match.group(1)
                    return Token(token_type, content)
                
                elif token_type == TokenType.HORIZONTAL_RULE:
                    return Token(token_type, "")
        
        return None
    
    def _parse_inline_elements(self, text: str) -> List[Token]:
        """인라인 요소 파싱"""
        tokens = []
        current_pos = 0
        
        while current_pos < len(text):
            earliest_match = None
            earliest_pos = len(text)
            earliest_type = None
            
            # 가장 앞에 있는 인라인 패턴 찾기
            for pattern, token_type in self.INLINE_PATTERNS:
                match = re.search(pattern, text[current_pos:])
                if match:
                    match_start = current_pos + match.start()
                    if match_start < earliest_pos:
                        earliest_pos = match_start
                        earliest_match = match
                        earliest_type = token_type
            
            if earliest_match:
                # 매치 전까지의 텍스트
                if earliest_pos > current_pos:
                    plain_text = text[current_pos:earliest_pos]
                    tokens.append(Token(TokenType.TEXT, plain_text))
                
                # 매치된 요소
                content = earliest_match.group(1)
                tokens.append(Token(earliest_type, content))
                
                current_pos = current_pos + earliest_match.end()
            else:
                # 남은 텍스트
                remaining = text[current_pos:]
                if remaining:
                    tokens.append(Token(TokenType.TEXT, remaining))
                break
        
        return tokens


class MarkdownStyleManager:
    """마크다운 스타일 관리"""
    
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.base_font = ("맑은 고딕", 13)
        self.styles_configured = False
    
    def configure_styles(self, theme_config=None):
        """모든 마크다운 스타일 설정"""
        if self.styles_configured:
            return
        
        font_family, font_size = self.base_font
        
        # 기본 스타일
        self.text_widget.tag_configure("md_text", 
                                     font=(font_family, font_size))
        
        # 헤더 스타일
        for i in range(1, 7):
            size_offset = max(6 - i, 0)
            # 모든 헤더를 하늘색으로
            header_color = "#87CEEB"
            
            self.text_widget.tag_configure(f"md_header_{i}", 
                                         font=(font_family, font_size + size_offset, "bold"),
                                         foreground=header_color)
        
        # 인라인 스타일  
        self.text_widget.tag_configure("md_bold", 
                                     font=(font_family, font_size, "bold"))
        self.text_widget.tag_configure("md_italic", 
                                     font=(font_family, font_size, "italic"))
        self.text_widget.tag_configure("md_code_inline", 
                                     font=("Consolas", font_size),
                                     background="#F3F4F6",
                                     foreground="#DC2626")
        
        # 블록 스타일
        self.text_widget.tag_configure("md_quote", 
                                     foreground="#6B7280",
                                     font=(font_family, font_size, "italic"),
                                     lmargin1=20, lmargin2=20,
                                     background="#F9FAFB")
        
        self.text_widget.tag_configure("md_list", 
                                     font=(font_family, font_size),
                                     lmargin1=20, lmargin2=20)
        
        self.text_widget.tag_configure("md_list_bold", 
                                     font=(font_family, font_size, "bold"),
                                     lmargin1=20, lmargin2=20)
        
        self.text_widget.tag_configure("md_hr", 
                                     foreground="#D1D5DB")
        
        # 코드 블록 스타일
        self.text_widget.tag_configure("md_code_block", 
                                     font=("Consolas", font_size - 1),
                                     background="#1F2937",
                                     foreground="#F9FAFB")
        
        self.styles_configured = True
    
    def update_font(self, font_tuple):
        """폰트 업데이트"""
        self.base_font = font_tuple
        self.styles_configured = False
        self.configure_styles()


class MarkdownRenderer:
    """최적화된 마크다운 렌더러"""
    
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.tokenizer = MarkdownTokenizer()
        self.style_manager = MarkdownStyleManager(text_widget)
        self.code_blocks = []  # 코드 블록 위젯 관리
    
    def render_markdown(self, text: str):
        """마크다운 텍스트 렌더링"""
        # 스타일 설정
        self.style_manager.configure_styles()
        
        # 토큰화
        tokens = self.tokenizer.tokenize(text)
        
        # 렌더링
        for token in tokens:
            self._render_token(token)
    
    def _render_token(self, token: Token):
        """개별 토큰 렌더링"""
        if token.type == TokenType.TEXT:
            self.text_widget.insert(tk.END, token.content, "md_text")
        
        elif token.type == TokenType.BOLD:
            self.text_widget.insert(tk.END, token.content, "md_bold")
        
        elif token.type == TokenType.ITALIC:
            self.text_widget.insert(tk.END, token.content, "md_italic")
        
        elif token.type == TokenType.CODE_INLINE:
            self.text_widget.insert(tk.END, token.content, "md_code_inline")
        
        elif token.type == TokenType.HEADER:
            prefix = "■ " if token.level == 1 else "▲ " if token.level == 2 else "● "
            self.text_widget.insert(tk.END, prefix, f"md_header_{token.level}")
            self._render_inline_tokens(token.metadata.get('inline_tokens', []), f"md_header_{token.level}")
        
        elif token.type == TokenType.LIST_ITEM:
            indent = "  " * (token.level // 2)
            self.text_widget.insert(tk.END, f"{indent}• ", "md_list")
            self._render_inline_tokens(token.metadata.get('inline_tokens', []), "md_list")
        
        elif token.type == TokenType.NUMBERED_LIST:
            indent = "  " * (token.level // 2)
            # 토큰에서 추출한 실제 번호 사용
            number = token.metadata.get('number', '1') if token.metadata else '1'
            self.text_widget.insert(tk.END, f"{indent}{number}. ", "md_list")
            self._render_inline_tokens(token.metadata.get('inline_tokens', []), "md_list")
        
        elif token.type == TokenType.QUOTE:
            self.text_widget.insert(tk.END, "┃ ", "md_quote")
            self._render_inline_tokens(token.metadata.get('inline_tokens', []), "md_quote")
        
        elif token.type == TokenType.HORIZONTAL_RULE:
            self.text_widget.insert(tk.END, "─" * 50, "md_hr")
        
        elif token.type == TokenType.CODE_BLOCK:
            self._render_code_block(token)
        
        elif token.type == TokenType.LINE_BREAK:
            self.text_widget.insert(tk.END, token.content)
    
    def _render_inline_tokens(self, inline_tokens: List[Token], context_tag: str):
        """인라인 토큰들을 컨텍스트에 맞게 렌더링"""
        if not inline_tokens:
            return
        
        for token in inline_tokens:
            if token.type == TokenType.TEXT:
                self.text_widget.insert(tk.END, token.content, context_tag)
            elif token.type == TokenType.BOLD:
                # 컨텍스트별 볼드 스타일 선택
                if context_tag.startswith("md_header"):
                    self.text_widget.insert(tk.END, token.content, f"{context_tag}_bold")
                elif context_tag == "md_list":
                    self.text_widget.insert(tk.END, token.content, "md_list_bold")
                else:
                    self.text_widget.insert(tk.END, token.content, "md_bold")
            elif token.type == TokenType.ITALIC:
                self.text_widget.insert(tk.END, token.content, "md_italic")
            elif token.type == TokenType.CODE_INLINE:
                self.text_widget.insert(tk.END, token.content, "md_code_inline")
    
    def _render_code_block(self, token: Token):
        """접기/펼치기 가능한 코드 블록 렌더링"""
        language = token.metadata.get('language', '')
        line_count = len(token.content.strip().split('\n'))
        
        # 메인 컨테이너 프레임
        container_frame = tk.Frame(self.text_widget, bg="#f5f5f5", relief=tk.SOLID, bd=1)
        
        # 헤더 프레임 (클릭 가능)
        header_frame = tk.Frame(container_frame, bg="#2b2b2b", relief=tk.FLAT, cursor="hand2")
        header_frame.pack(fill=tk.X)
        
        # 토글 상태 추적 (먼저 정의)
        is_expanded = [False]  # 리스트로 클로저 변수 관리
        
        # 접기/펼치기 아이콘
        toggle_icon = tk.Label(header_frame, text="▶", 
                             bg="#2b2b2b", fg="#ffffff", 
                             font=("맑은 고딕", 10, "bold"),
                             cursor="hand2")
        toggle_icon.pack(side=tk.LEFT, padx=(8, 5))
        
        # 언어 라벨
        lang_display = f"{language}" if language else "코드"
        lang_label = tk.Label(header_frame, text=lang_display, 
                            bg="#2b2b2b", fg="#ffffff", 
                            font=("맑은 고딕", 10),
                            cursor="hand2")
        lang_label.pack(side=tk.LEFT, padx=5)
        
        # 줄 수 표시
        line_info = tk.Label(header_frame, text=f"({line_count} 줄)", 
                           bg="#2b2b2b", fg="#888888", 
                           font=("맑은 고딕", 9),
                           cursor="hand2")
        line_info.pack(side=tk.LEFT, padx=5)
        
        # 복사 버튼
        copy_btn = tk.Button(header_frame, text="📋 복사", 
                           bg="#4a4a4a", fg="#ffffff", 
                           font=("맑은 고딕", 9),
                           relief=tk.FLAT, bd=0,
                           cursor="hand2",
                           command=lambda: self._copy_to_clipboard(token.content))
        copy_btn.pack(side=tk.RIGHT, padx=8)
        
        # 코드 내용 프레임 (기본적으로 숨김)
        code_frame = tk.Frame(container_frame, bg="#f8f8f8")
        
        # 코드 텍스트 위젯 (읽기 전용, 선택 가능)
        max_height = min(line_count, 20)  # 최대 20줄
        code_text = tk.Text(code_frame, 
                          bg="#f8f8f8", fg="#333333",
                          font=("Consolas", 10),
                          wrap=tk.NONE,
                          relief=tk.FLAT,
                          bd=0,
                          padx=10, pady=8,
                          height=max_height,
                          state=tk.NORMAL,
                          selectbackground="#d0d0d0")
        
        # 코드 내용 삽입
        code_text.delete(1.0, tk.END)
        code_text.insert(1.0, token.content)
        code_text.config(state=tk.DISABLED)  # 편집 방지, 선택은 가능
        
        # 스크롤바
        scrollbar_y = tk.Scrollbar(code_frame, orient=tk.VERTICAL, command=code_text.yview)
        code_text.configure(yscrollcommand=scrollbar_y.set)
        
        # 위젯 배치
        code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        def toggle_code():
            """코드 블록 접기/펼치기"""
            if is_expanded[0]:
                # 접기
                code_frame.pack_forget()
                toggle_icon.config(text="▶")
                is_expanded[0] = False
            else:
                # 펼치기
                code_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))
                toggle_icon.config(text="▼")
                is_expanded[0] = True
        
        # 헤더 클릭 이벤트 바인딩
        def on_header_click(event):
            toggle_code()
        
        header_frame.bind("<Button-1>", on_header_click)
        toggle_icon.bind("<Button-1>", on_header_click)
        lang_label.bind("<Button-1>", on_header_click)
        line_info.bind("<Button-1>", on_header_click)
        
        # 컨테이너 삽입
        self.text_widget.window_create(tk.END, window=container_frame)
        self.text_widget.insert(tk.END, "\n\n")
        
        # 코드 블록 정보 저장
        self.code_blocks.append({
            'container_frame': container_frame,
            'header_frame': header_frame,
            'code_frame': code_frame,
            'code_text': code_text,
            'toggle_function': toggle_code,
            'content': token.content,
            'language': language,
            'is_expanded': is_expanded
        })
    
    def _copy_to_clipboard(self, content: str):
        """클립보드에 복사"""
        try:
            self.text_widget.clipboard_clear()
            self.text_widget.clipboard_append(content)
            self._show_copy_notification()
        except Exception as e:
            messagebox.showerror("복사 오류", f"클립보드 복사 중 오류가 발생했습니다: {str(e)}")
    
    def _show_copy_notification(self):
        """복사 완료 알림"""
        notification = tk.Toplevel()
        notification.withdraw()
        notification.overrideredirect(True)
        notification.configure(bg="#4CAF50")
        
        label = tk.Label(notification, text="📋 코드가 클립보드에 복사되었습니다!", 
                        bg="#4CAF50", fg="white", 
                        font=("맑은 고딕", 10, "bold"),
                        padx=20, pady=10)
        label.pack()
        
        notification.update_idletasks()
        parent_x = self.text_widget.winfo_rootx()
        parent_y = self.text_widget.winfo_rooty()
        parent_width = self.text_widget.winfo_width()
        
        x = parent_x + (parent_width // 2) - (notification.winfo_width() // 2)
        y = parent_y + 50
        
        notification.geometry(f"+{x}+{y}")
        notification.deiconify()
        notification.after(3000, notification.destroy)
    
    def update_font(self, font_tuple):
        """폰트 업데이트"""
        self.style_manager.update_font(font_tuple)
    
    def clear_code_blocks(self):
        """코드 블록 정리"""
        self.code_blocks.clear()


# 호환성을 위한 래퍼 (기존 인터페이스 유지)
def create_markdown_renderer(text_widget: tk.Text) -> MarkdownRenderer:
    """마크다운 렌더러 생성 (기존 인터페이스 호환)"""
    return MarkdownRenderer(text_widget)