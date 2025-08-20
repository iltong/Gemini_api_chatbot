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
    """파일 처리 클래스 (다중 파일 지원)"""
    
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
    
    def __init__(self, max_files: int = 4):
        # 기존 단일 파일 지원 (하위 호환성)
        self.selected_file_path: Optional[str] = None
        self.selected_file_content: Optional[str] = None
        self.selected_file_encoding: Optional[str] = None
        self.selected_file_size: int = 0
        
        # 다중 파일 지원
        self.max_files = max_files
        self.files: List[Dict[str, Any]] = []  # 파일 정보 딕셔너리 리스트
        self.current_mode = "multiple"  # 기본적으로 다중 모드 사용
    
    def set_mode(self, mode: str):
        """파일 처리 모드 설정"""
        if mode in ["single", "multiple"]:
            self.current_mode = mode
            if mode == "single":
                self.clear_multiple_files()
            else:
                self.clear_file()
    
    def load_file(self, file_path: str) -> Tuple[bool, str]:
        """
        파일 로드 (현재 모드에 따라 단일 또는 다중 처리)
        Returns: (성공 여부, 오류 메시지)
        """
        if self.current_mode == "multiple":
            return self.add_file(file_path)
        else:
            return self.load_single_file(file_path)
    
    def load_single_file(self, file_path: str) -> Tuple[bool, str]:
        """
        단일 파일 로드 (기존 방식)
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
    
    def add_file(self, file_path: str) -> Tuple[bool, str]:
        """
        다중 파일에 새 파일 추가
        Returns: (성공 여부, 오류 메시지)
        """
        # 최대 파일 수 체크
        if len(self.files) >= self.max_files:
            return False, f"최대 {self.max_files}개까지만 추가할 수 있습니다."
        
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
                try:
                    content = raw_data.decode('utf-8', errors='ignore')
                    encoding = 'utf-8'
                except:
                    return False, "파일 인코딩을 읽을 수 없습니다."
            
            # 파일 정보 저장
            file_info = {
                'path': file_path,
                'content': content,
                'encoding': encoding,
                'size': file_size,
                'filename': os.path.basename(file_path)
            }
            
            self.files.append(file_info)
            return True, f"파일이 추가되었습니다. ({len(self.files)}/{self.max_files})"
            
        except Exception as e:
            return False, f"파일을 불러올 수 없습니다: {str(e)}"
    
    def remove_file_by_index(self, index: int) -> bool:
        """인덱스로 파일 제거"""
        if 0 <= index < len(self.files):
            self.files.pop(index)
            return True
        return False
    
    def get_file_count(self) -> int:
        """현재 로드된 파일 수 반환"""
        if self.current_mode == "multiple":
            return len(self.files)
        else:
            return 1 if self.has_file() else 0
    
    def get_file_info(self) -> Optional[str]:
        """파일 정보 반환"""
        if self.current_mode == "multiple":
            return self.get_multiple_file_info()
        else:
            return self.get_single_file_info()
    
    def get_single_file_info(self) -> Optional[str]:
        """단일 파일 정보 반환 (기존 방식)"""
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
    
    def get_multiple_file_info(self) -> Optional[str]:
        """다중 파일 정보 반환"""
        if not self.files:
            return None
        
        count = len(self.files)
        if count == 1:
            filename = self.files[0]['filename']
            if len(filename) > 25:
                filename = filename[:22] + "..."
            return f"파일 첨부: {filename}"
        else:
            return f"파일 {count}개 첨부"
    
    def get_file_info_by_index(self, index: int) -> Optional[str]:
        """인덱스별 파일 정보 반환"""
        if self.current_mode == "multiple" and 0 <= index < len(self.files):
            filename = self.files[index]['filename']
            if len(filename) > 25:
                filename = filename[:22] + "..."
            _, ext = os.path.splitext(self.files[index]['path'].lower())
            file_type = self.SUPPORTED_EXTENSIONS.get(ext, "파일")
            return f"파일 {index+1}: {filename} ({file_type})"
        return None
    
    def get_short_filename(self, index: int = 0) -> Optional[str]:
        """짧은 파일명 반환"""
        if self.current_mode == "multiple":
            if 0 <= index < len(self.files):
                filename = self.files[index]['filename']
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                return filename
        else:
            if not self.selected_file_path:
                return None
            filename = os.path.basename(self.selected_file_path)
            if len(filename) > 30:
                filename = filename[:27] + "..."
            return filename
        return None
    
    def get_file_content(self, index: int = 0) -> Optional[str]:
        """파일 내용 반환"""
        if self.current_mode == "multiple":
            if 0 <= index < len(self.files):
                return self.files[index]['content']
        else:
            return self.selected_file_content
        return None
    
    def get_file_preview(self, max_lines: int = 20, index: int = 0) -> Optional[str]:
        """파일 미리보기 반환 (처음 몇 줄)"""
        content = self.get_file_content(index)
        if not content:
            return None
        
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
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
    
    def clear_multiple_files(self):
        """다중 파일 모두 초기화"""
        self.files.clear()
    
    def clear_all_files(self):
        """모든 파일 초기화 (단일/다중 모두)"""
        self.clear_file()
        self.clear_multiple_files()
    
    def has_file(self) -> bool:
        """파일이 선택되어 있는지 확인"""
        if self.current_mode == "multiple":
            return len(self.files) > 0
        else:
            return self.selected_file_content is not None
    
    def get_file_for_api(self) -> Optional[str]:
        """API 호출용 단일 파일 내용 반환 (하위 호환성)"""
        if self.current_mode == "multiple" and self.files:
            return self.get_file_for_api_by_index(0)
        elif self.selected_file_content and self.selected_file_path:
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
        return None
    
    def get_file_for_api_by_index(self, index: int) -> Optional[str]:
        """API 호출용 특정 인덱스 파일 내용 반환"""
        if not (0 <= index < len(self.files)):
            return None
        
        file_info = self.files[index]
        filename = file_info['filename']
        _, ext = os.path.splitext(file_info['path'].lower())
        file_type = self.SUPPORTED_EXTENSIONS.get(ext, "파일")
        
        # 파일 정보와 함께 내용 반환
        api_content = f"파일명: {filename}\n"
        api_content += f"파일 타입: {file_type}\n"
        api_content += f"인코딩: {file_info['encoding']}\n"
        api_content += f"크기: {self._format_file_size(file_info['size'])}\n\n"
        api_content += "파일 내용:\n"
        api_content += "```\n"
        api_content += file_info['content']
        api_content += "\n```"
        
        return api_content
    
    def get_all_files_for_api(self) -> List[str]:
        """API 호출용 모든 파일 내용 반환"""
        if self.current_mode == "multiple":
            return [self.get_file_for_api_by_index(i) for i in range(len(self.files)) if self.get_file_for_api_by_index(i)]
        elif self.get_file_for_api():
            return [self.get_file_for_api()]
        else:
            return []
    
    def get_file_paths(self) -> List[str]:
        """모든 파일 경로 반환"""
        if self.current_mode == "multiple":
            return [file_info['path'] for file_info in self.files]
        elif self.selected_file_path:
            return [self.selected_file_path]
        else:
            return []
    
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