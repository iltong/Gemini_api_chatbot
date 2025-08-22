"""
설정 대화상자 UI 컴포넌트
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional

from config.settings import AppConfig, GenerationParams, FontSettings

class ToolTip:
    """툴팁 클래스"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)
    
    def on_enter(self, event=None):
        """마우스가 위젯에 들어올 때"""
        self.show_tooltip(event)
    
    def on_leave(self, event=None):
        """마우스가 위젯을 떠날 때"""
        self.hide_tooltip()
    
    def on_motion(self, event=None):
        """마우스가 움직일 때 툴팁 위치 업데이트"""
        if self.tooltip_window:
            self.update_tooltip_position(event)
    
    def show_tooltip(self, event=None):
        """툴팁 표시"""
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.configure(bg="#2d3748", relief="solid", borderwidth=1)
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#2d3748",
            foreground="#e2e8f0",
            font=("맑은 고딕", 9),
            wraplength=400,
            padx=8,
            pady=6
        )
        label.pack()
        
        self.tooltip_window.geometry(f"+{x}+{y}")
        
        # 툴팁이 화면 밖으로 나가지 않도록 조정
        self.tooltip_window.update_idletasks()
        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()
        screen_width = self.tooltip_window.winfo_screenwidth()
        screen_height = self.tooltip_window.winfo_screenheight()
        
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 10
        if y + tooltip_height > screen_height:
            y = y - tooltip_height - 30
        
        self.tooltip_window.geometry(f"+{x}+{y}")
    
    def update_tooltip_position(self, event=None):
        """툴팁 위치 업데이트"""
        if not self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window.geometry(f"+{x}+{y}")
    
    def hide_tooltip(self):
        """툴팁 숨김"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class SettingsDialog:
    """설정 대화상자 클래스"""
    
    def __init__(self, parent: tk.Tk, config: AppConfig, generation_params: GenerationParams,
                 system_prompt: str, font_settings: FontSettings, 
                 on_save_callback: Callable[[GenerationParams, str, FontSettings], None]):
        self.parent = parent
        self.config = config
        self.generation_params = generation_params
        self.system_prompt = system_prompt
        self.font_settings = font_settings
        self.on_save_callback = on_save_callback
        
        self.param_vars: Dict[str, tk.Variable] = {}
        self.font_vars: Dict[str, tk.Variable] = {}
        self.system_prompt_text: Optional[tk.Text] = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """설정 대화상자 생성"""
        self.settings_window = tk.Toplevel(self.parent)
        self.settings_window.title("고급 설정")
        self.settings_window.geometry("600x750")
        self.settings_window.configure(bg=self.config.THEME["bg_primary"])
        self.settings_window.transient(self.parent)
        self.settings_window.grab_set()
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(self.settings_window, bg=self.config.THEME["bg_primary"])
        scrollbar = ttk.Scrollbar(self.settings_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.config.THEME["bg_primary"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.create_parameter_section(scrollable_frame)
        self.create_font_section(scrollable_frame)
        self.create_system_prompt_section(scrollable_frame)
        self.create_button_section(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_parameter_section(self, parent: tk.Widget):
        """생성 파라미터 섹션 생성"""
        param_frame = tk.LabelFrame(parent, text="생성 파라미터", 
                                   bg=self.config.THEME["bg_primary"], 
                                   fg=self.config.THEME["fg_primary"],
                                   font=("맑은 고딕", 10, "bold"))
        param_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 파라미터 입력 필드들
        for param in self.config.PARAM_RANGES.keys():
            min_val, max_val, param_type = self.config.PARAM_RANGES[param]
            label_text = self.config.PARAM_DESCRIPTIONS[param]
            
            frame = tk.Frame(param_frame, bg=self.config.THEME["bg_primary"])
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 라벨 생성 및 툴팁 추가
            label = tk.Label(frame, text=f"{label_text}:", 
                    bg=self.config.THEME["bg_primary"], 
                    fg=self.config.THEME["fg_primary"],
                    font=("맑은 고딕", 9), width=15, anchor="w")
            label.pack(side=tk.LEFT)
            
            # 툴팁 추가 (config에 툴팁 설명이 있는 경우)
            if hasattr(self.config, 'PARAM_TOOLTIPS') and param in self.config.PARAM_TOOLTIPS:
                ToolTip(label, self.config.PARAM_TOOLTIPS[param])
            
            if param_type == "int":
                var = tk.IntVar(value=getattr(self.generation_params, param))
            else:
                var = tk.DoubleVar(value=getattr(self.generation_params, param))
            
            self.param_vars[param] = var
            
            entry = tk.Entry(frame, textvariable=var, 
                           bg=self.config.THEME["bg_input"], 
                           fg=self.config.THEME["fg_primary"],
                           font=("맑은 고딕", 9), width=10)
            entry.pack(side=tk.LEFT, padx=5)
            
            tk.Label(frame, text=f"({min_val}-{max_val})", 
                    bg=self.config.THEME["bg_primary"], 
                    fg=self.config.THEME["fg_timestamp"],
                    font=("맑은 고딕", 8)).pack(side=tk.LEFT, padx=5)
    
    def create_font_section(self, parent: tk.Widget):
        """폰트 설정 섹션 생성"""
        font_frame = tk.LabelFrame(parent, text="폰트 설정", 
                                  bg=self.config.THEME["bg_primary"], 
                                  fg=self.config.THEME["fg_primary"],
                                  font=("맑은 고딕", 10, "bold"))
        font_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 폰트 설정들
        font_configs = [
            ("채팅 폰트", "chat_font_family", "chat_font_size"),
            ("입력 폰트", "input_font_family", "input_font_size"),
            ("버튼 폰트", "button_font_family", "button_font_size"),
            ("제목 폰트", "title_font_family", "title_font_size")
        ]
        
        for label_text, family_attr, size_attr in font_configs:
            frame = tk.Frame(font_frame, bg=self.config.THEME["bg_primary"])
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 라벨
            tk.Label(frame, text=f"{label_text}:", 
                    bg=self.config.THEME["bg_primary"], 
                    fg=self.config.THEME["fg_primary"],
                    font=("맑은 고딕", 9), width=10, anchor="w").pack(side=tk.LEFT)
            
            # 폰트 패밀리 선택
            family_var = tk.StringVar(value=getattr(self.font_settings, family_attr))
            self.font_vars[family_attr] = family_var
            
            family_combo = ttk.Combobox(frame, textvariable=family_var,
                                      values=self.config.AVAILABLE_FONTS,
                                      state="readonly", width=12,
                                      font=("맑은 고딕", 8))
            family_combo.pack(side=tk.LEFT, padx=5)
            
            # 폰트 크기 입력
            size_var = tk.IntVar(value=getattr(self.font_settings, size_attr))
            self.font_vars[size_attr] = size_var
            
            size_entry = tk.Entry(frame, textvariable=size_var, width=5,
                                bg=self.config.THEME["bg_input"], 
                                fg=self.config.THEME["fg_primary"],
                                font=("맑은 고딕", 9))
            size_entry.pack(side=tk.LEFT, padx=5)
            
            tk.Label(frame, text="pt", 
                    bg=self.config.THEME["bg_primary"], 
                    fg=self.config.THEME["fg_timestamp"],
                    font=("맑은 고딕", 8)).pack(side=tk.LEFT, padx=2)
    
    def create_system_prompt_section(self, parent: tk.Widget):
        """시스템 프롬프트 섹션 생성"""
        prompt_frame = tk.LabelFrame(parent, text="시스템 프롬프트", 
                                   bg=self.config.THEME["bg_primary"], 
                                   fg=self.config.THEME["fg_primary"],
                                   font=("맑은 고딕", 10, "bold"))
        prompt_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.system_prompt_text = tk.Text(prompt_frame, height=8, wrap=tk.WORD,
                                        bg=self.config.THEME["bg_input"], 
                                        fg=self.config.THEME["fg_primary"], 
                                        font=("맑은 고딕", 9))
        self.system_prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.system_prompt_text.insert(1.0, self.system_prompt)
        
        # 프리셋 버튼들
        preset_frame = tk.Frame(prompt_frame, bg=self.config.THEME["bg_primary"])
        preset_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for name, prompt in self.config.PROMPT_PRESETS.items():
            btn = tk.Button(preset_frame, text=name, 
                          command=lambda p=prompt: self.set_preset_prompt(p),
                          bg=self.config.THEME["bg_secondary"], 
                          fg=self.config.THEME["fg_primary"], 
                          font=("맑은 고딕", 8))
            btn.pack(side=tk.LEFT, padx=2)
    
    def create_button_section(self, parent: tk.Widget):
        """버튼 섹션 생성"""
        button_frame = tk.Frame(parent, bg=self.config.THEME["bg_primary"])
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(button_frame, text="저장", command=self.save_settings,
                 bg="#4CAF50", fg="#ffffff", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="취소", command=self.settings_window.destroy,
                 bg="#F44336", fg="#ffffff", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="기본값 복원", command=self.reset_defaults,
                 bg="#FF9800", fg="#ffffff", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT, padx=5)
    
    def set_preset_prompt(self, prompt: str):
        """프리셋 프롬프트 설정"""
        self.system_prompt_text.delete(1.0, tk.END)
        self.system_prompt_text.insert(1.0, prompt)
    
    def reset_defaults(self):
        """기본값 복원"""
        # 파라미터 기본값 복원
        defaults = GenerationParams()
        for param in self.param_vars.keys():
            default_val = getattr(defaults, param)
            self.param_vars[param].set(default_val)
        
        # 폰트 기본값 복원
        font_defaults = FontSettings()
        for font_attr in self.font_vars.keys():
            default_val = getattr(font_defaults, font_attr)
            self.font_vars[font_attr].set(default_val)
        
        # 시스템 프롬프트 초기화
        self.system_prompt_text.delete(1.0, tk.END)
    
    def save_settings(self):
        """설정 저장"""
        try:
            # 파라미터 유효성 검사 및 저장
            new_params = GenerationParams()
            
            for param, var in self.param_vars.items():
                value = var.get()
                min_val, max_val, _ = self.config.PARAM_RANGES[param]
                
                # 범위 검사
                if not (min_val <= value <= max_val):
                    messagebox.showerror("오류", f"{self.config.PARAM_DESCRIPTIONS[param]} 값이 유효 범위({min_val}-{max_val})를 벗어났습니다.")
                    return
                
                setattr(new_params, param, value)
            
            # 폰트 설정 저장
            new_font_settings = FontSettings()
            for font_attr, var in self.font_vars.items():
                value = var.get()
                
                # 폰트 크기 범위 검사
                if font_attr.endswith("_size"):
                    if not (8 <= value <= 72):
                        messagebox.showerror("오류", f"폰트 크기는 8~72pt 범위여야 합니다. (현재: {value}pt)")
                        return
                
                setattr(new_font_settings, font_attr, value)
            
            # 시스템 프롬프트 저장
            new_prompt = self.system_prompt_text.get(1.0, tk.END).strip()
            
            # 콜백 호출
            self.on_save_callback(new_params, new_prompt, new_font_settings)
            
            messagebox.showinfo("설정 저장", "설정이 저장되었습니다.")
            self.settings_window.destroy()
            
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")