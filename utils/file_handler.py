"""
파일 처리 유틸리티
"""

import os
from typing import Optional, Tuple, Dict, List

# chardet가 없는 경우를 대비한 fallback
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

class FileHandler:
    """파일 처리 클래스"""
    
    # 지원되는 파일 확장자와 설명
    SUPPORTED_EXTENSIONS = {
        # 코드 파일
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'Objective-C',
        '.sh': 'Shell Script',
        '.bat': 'Batch',
        '.ps1': 'PowerShell',
        
        # 마크업 및 데이터
        '.xml': 'XML',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Config',
        '.conf': 'Config',
        
        # 문서
        '.txt': '텍스트',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
        
        # 웹 관련
        '.vue': 'Vue',
        '.svelte': 'Svelte',
        '.ejs': 'EJS',
        '.pug': 'Pug',
        
        # 기타
        '.sql': 'SQL',
        '.dockerfile': 'Dockerfile',
        '.gitignore': 'Git Ignore',
        '.env': 'Environment',
        '.log': '로그'
    }
    
    # 최대 파일 크기 (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    def __init__(self):
        self.selected_file_path: Optional[str] = None
        self.selected_file_content: Optional[str] = None
        self.selected_file_encoding: Optional[str] = None
        self.selected_file_size: int = 0
    
    def load_file(self, file_path: str) -> Tuple[bool, str]:
        """
        파일 로드
        Returns: (성공 여부, 오류 메시지)
        """
        try:
            # 파일 존재 확인
            if not os.path.exists(file_path):
                return False, "파일을 찾을 수 없습니다."
            
            # 파일 크기 확인
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                return False, f"파일이 너무 큽니다. (최대 {self.MAX_FILE_SIZE // (1024*1024)}MB)"
            
            # 확장자 확인
            _, ext = os.path.splitext(file_path.lower())
            if ext not in self.SUPPORTED_EXTENSIONS:
                return False, f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
            
            # 파일 읽기 (인코딩 자동 감지)
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # 인코딩 감지
            if HAS_CHARDET:
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result['encoding'] or 'utf-8'
            else:
                # chardet가 없는 경우 일반적인 인코딩들을 순서대로 시도
                encoding = 'utf-8'
            
            # 텍스트로 디코딩
            content = None
            for enc in [encoding, 'utf-8', 'cp949', 'euc-kr', 'latin1']:
                try:
                    content = raw_data.decode(enc)
                    encoding = enc
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if content is None:
                # 마지막 시도: 오류를 무시하고 UTF-8로 디코딩
                try:
                    content = raw_data.decode('utf-8', errors='ignore')
                    encoding = 'utf-8'
                except:
                    return False, "파일 인코딩을 읽을 수 없습니다."
            
            # 정보 저장
            self.selected_file_path = file_path
            self.selected_file_content = content
            self.selected_file_encoding = encoding
            self.selected_file_size = file_size
            
            return True, ""
            
        except Exception as e:
            return False, f"파일을 불러올 수 없습니다: {str(e)}"
    
    def get_file_info(self) -> Optional[str]:
        """파일 정보 반환"""
        if not self.selected_file_path:
            return None
        
        filename = os.path.basename(self.selected_file_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        # 파일 크기를 읽기 쉬운 형태로 변환
        size_str = self._format_file_size(self.selected_file_size)
        
        # 확장자 설명
        _, ext = os.path.splitext(self.selected_file_path.lower())
        file_type = self.SUPPORTED_EXTENSIONS.get(ext, "파일")
        
        return f"파일 첨부: {filename} ({file_type}, {size_str})"
    
    def get_short_filename(self) -> Optional[str]:
        """짧은 파일명 반환"""
        if not self.selected_file_path:
            return None
        
        filename = os.path.basename(self.selected_file_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        return filename
    
    def get_file_content(self) -> Optional[str]:
        """파일 내용 반환"""
        return self.selected_file_content
    
    def get_file_preview(self, max_lines: int = 20) -> Optional[str]:
        """파일 미리보기 반환 (처음 몇 줄)"""
        if not self.selected_file_content:
            return None
        
        lines = self.selected_file_content.split('\n')
        if len(lines) <= max_lines:
            return self.selected_file_content
        
        preview_lines = lines[:max_lines]
        remaining_lines = len(lines) - max_lines
        
        preview = '\n'.join(preview_lines)
        preview += f"\n\n... (+ {remaining_lines}줄 더)"
        
        return preview
    
    def clear_file(self):
        """선택된 파일 초기화"""
        self.selected_file_path = None
        self.selected_file_content = None
        self.selected_file_encoding = None
        self.selected_file_size = 0
    
    def has_file(self) -> bool:
        """파일이 선택되어 있는지 확인"""
        return self.selected_file_content is not None
    
    def get_file_for_api(self) -> Optional[str]:
        """API 호출용 파일 내용 반환"""
        if not self.selected_file_content or not self.selected_file_path:
            return None
        
        filename = os.path.basename(self.selected_file_path)
        _, ext = os.path.splitext(self.selected_file_path.lower())
        file_type = self.SUPPORTED_EXTENSIONS.get(ext, "파일")
        
        # 파일 정보와 함께 내용 반환
        api_content = f"파일명: {filename}\n"
        api_content += f"파일 타입: {file_type}\n"
        api_content += f"인코딩: {self.selected_file_encoding}\n"
        api_content += f"크기: {self._format_file_size(self.selected_file_size)}\n\n"
        api_content += "파일 내용:\n"
        api_content += "```\n"
        api_content += self.selected_file_content
        api_content += "\n```"
        
        return api_content
    
    def is_supported_file(self, file_path: str) -> bool:
        """지원되는 파일인지 확인"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_supported_extensions_list(self) -> List[str]:
        """지원되는 확장자 목록 반환"""
        return list(self.SUPPORTED_EXTENSIONS.keys())
    
    def _format_file_size(self, size_bytes: int) -> str:
        """파일 크기를 읽기 쉬운 형태로 변환"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"