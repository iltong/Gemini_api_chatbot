"""
이미지 처리 유틸리티
"""

from PIL import Image, ImageTk
import os
from typing import Optional, Tuple

class ImageHandler:
    """이미지 처리 클래스"""
    
    def __init__(self):
        self.selected_image: Optional[Image.Image] = None
        self.selected_image_path: Optional[str] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
    
    def load_image(self, file_path: str) -> Tuple[bool, str]:
        """
        이미지 로드
        Returns: (성공 여부, 오류 메시지)
        """
        try:
            # 이미지 로드
            image = Image.open(file_path)
            
            # 원본 이미지 저장
            self.selected_image = Image.open(file_path)
            self.selected_image_path = file_path
            
            return True, ""
            
        except Exception as e:
            return False, f"이미지를 불러올 수 없습니다: {str(e)}"
    
    def create_preview(self, max_size: Tuple[int, int] = (200, 150)) -> Optional[ImageTk.PhotoImage]:
        """미리보기용 이미지 생성"""
        if not self.selected_image:
            return None
        
        try:
            # 미리보기용 크기 조정
            preview_image = self.selected_image.copy()
            preview_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Tkinter용 이미지 변환
            self.preview_photo = ImageTk.PhotoImage(preview_image)
            return self.preview_photo
            
        except Exception as e:
            print(f"미리보기 생성 오류: {e}")
            return None
    
    def create_chat_preview(self, max_size: Tuple[int, int] = (450, 300)) -> Optional[ImageTk.PhotoImage]:
        """채팅창용 이미지 생성"""
        if not self.selected_image:
            return None
        
        try:
            # 채팅창용 크기 조정 (450x300 크기로 증가)
            chat_image = self.selected_image.copy()
            chat_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Tkinter용 이미지 변환
            chat_photo = ImageTk.PhotoImage(chat_image)
            return chat_photo
            
        except Exception as e:
            print(f"채팅창 이미지 생성 오류: {e}")
            return None
    
    def get_image_info(self) -> Optional[str]:
        """이미지 정보 반환"""
        if not self.selected_image_path:
            return None
        
        filename = os.path.basename(self.selected_image_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        return f"이미지 첨부: {filename}"
    
    def get_short_filename(self) -> Optional[str]:
        """짧은 파일명 반환"""
        if not self.selected_image_path:
            return None
        
        filename = os.path.basename(self.selected_image_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        return filename
    
    def clear_image(self):
        """선택된 이미지 초기화"""
        self.selected_image = None
        self.selected_image_path = None
        self.preview_photo = None
    
    def has_image(self) -> bool:
        """이미지가 선택되어 있는지 확인"""
        return self.selected_image is not None
    
    def get_image_for_api(self) -> Optional[Image.Image]:
        """API 호출용 이미지 반환"""
        return self.selected_image