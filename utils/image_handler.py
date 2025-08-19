"""
이미지 처리 유틸리티 (다중 이미지 지원)
"""

from PIL import Image, ImageTk
import os
from typing import Optional, Tuple, List, Dict, Any

class ImageHandler:
    """이미지 처리 클래스 (다중 이미지 지원)"""
    
    def __init__(self, max_images: int = 4):
        # 기존 단일 이미지 지원 (하위 호환성)
        self.selected_image: Optional[Image.Image] = None
        self.selected_image_path: Optional[str] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
        
        # 다중 이미지 지원
        self.max_images = max_images
        self.images: List[Dict[str, Any]] = []  # 이미지 정보 딕셔너리 리스트
        self.current_mode = "single"  # "single" 또는 "multiple"
    
    def set_mode(self, mode: str):
        """이미지 처리 모드 설정"""
        if mode in ["single", "multiple"]:
            self.current_mode = mode
            if mode == "single":
                self.clear_multiple_images()
            else:
                self.clear_image()
    
    def load_image(self, file_path: str) -> Tuple[bool, str]:
        """
        이미지 로드 (현재 모드에 따라 단일 또는 다중 처리)
        Returns: (성공 여부, 오류 메시지)
        """
        if self.current_mode == "multiple":
            return self.add_image(file_path)
        else:
            return self.load_single_image(file_path)
    
    def load_single_image(self, file_path: str) -> Tuple[bool, str]:
        """
        단일 이미지 로드 (기존 방식)
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
    
    def add_image(self, file_path: str) -> Tuple[bool, str]:
        """
        다중 이미지에 새 이미지 추가
        Returns: (성공 여부, 오류 메시지)
        """
        # 최대 이미지 수 체크
        if len(self.images) >= self.max_images:
            return False, f"최대 {self.max_images}개까지만 추가할 수 있습니다."
        
        try:
            # 이미지 로드
            image = Image.open(file_path)
            
            # 이미지 정보 저장
            image_info = {
                'path': file_path,
                'image': Image.open(file_path),
                'preview_photo': None,
                'chat_photo': None,
                'filename': os.path.basename(file_path)
            }
            
            self.images.append(image_info)
            return True, f"이미지가 추가되었습니다. ({len(self.images)}/{self.max_images})"
            
        except Exception as e:
            return False, f"이미지를 불러올 수 없습니다: {str(e)}"
    
    def remove_image_by_index(self, index: int) -> bool:
        """인덱스로 이미지 제거"""
        if 0 <= index < len(self.images):
            self.images.pop(index)
            return True
        return False
    
    def get_image_count(self) -> int:
        """현재 로드된 이미지 수 반환"""
        if self.current_mode == "multiple":
            return len(self.images)
        else:
            return 1 if self.has_image() else 0
    
    def create_preview(self, max_size: Tuple[int, int] = (200, 150), index: int = 0) -> Optional[ImageTk.PhotoImage]:
        """미리보기용 이미지 생성"""
        if self.current_mode == "multiple":
            return self.create_multiple_preview(index, max_size)
        else:
            return self.create_single_preview(max_size)
    
    def create_single_preview(self, max_size: Tuple[int, int] = (200, 150)) -> Optional[ImageTk.PhotoImage]:
        """단일 이미지 미리보기 생성 (기존 방식)"""
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
    
    def create_multiple_preview(self, index: int, max_size: Tuple[int, int] = (200, 150)) -> Optional[ImageTk.PhotoImage]:
        """다중 이미지 중 특정 인덱스의 미리보기 생성"""
        if index < 0 or index >= len(self.images):
            return None
        
        try:
            image_info = self.images[index]
            
            # 이미 생성된 미리보기가 있으면 반환
            if image_info['preview_photo']:
                return image_info['preview_photo']
            
            # 미리보기용 크기 조정
            preview_image = image_info['image'].copy()
            preview_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Tkinter용 이미지 변환
            preview_photo = ImageTk.PhotoImage(preview_image)
            self.images[index]['preview_photo'] = preview_photo
            return preview_photo
            
        except Exception as e:
            print(f"다중 이미지 미리보기 생성 오류: {e}")
            return None
    
    def create_chat_preview(self, max_size: Tuple[int, int] = (450, 300), index: int = 0) -> Optional[ImageTk.PhotoImage]:
        """채팅창용 이미지 생성"""
        if self.current_mode == "multiple":
            return self.create_multiple_chat_preview(index, max_size)
        else:
            return self.create_single_chat_preview(max_size)
    
    def create_single_chat_preview(self, max_size: Tuple[int, int] = (450, 300)) -> Optional[ImageTk.PhotoImage]:
        """단일 이미지 채팅창 미리보기 생성 (기존 방식)"""
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
    
    def create_multiple_chat_preview(self, index: int, max_size: Tuple[int, int] = (450, 300)) -> Optional[ImageTk.PhotoImage]:
        """다중 이미지 중 특정 인덱스의 채팅창 미리보기 생성"""
        if index < 0 or index >= len(self.images):
            return None
        
        try:
            image_info = self.images[index]
            
            # 이미 생성된 채팅 미리보기가 있으면 반환
            if image_info['chat_photo']:
                return image_info['chat_photo']
            
            # 채팅창용 크기 조정
            chat_image = image_info['image'].copy()
            chat_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Tkinter용 이미지 변환
            chat_photo = ImageTk.PhotoImage(chat_image)
            self.images[index]['chat_photo'] = chat_photo
            return chat_photo
            
        except Exception as e:
            print(f"다중 이미지 채팅 미리보기 생성 오류: {e}")
            return None
    
    def get_all_chat_previews(self, max_size: Tuple[int, int] = (300, 200)) -> List[ImageTk.PhotoImage]:
        """모든 다중 이미지의 채팅 미리보기 리스트 생성"""
        previews = []
        for i in range(len(self.images)):
            preview = self.create_multiple_chat_preview(i, max_size)
            if preview:
                previews.append(preview)
        return previews
    
    def get_image_info(self) -> Optional[str]:
        """이미지 정보 반환"""
        if self.current_mode == "multiple":
            return self.get_multiple_image_info()
        else:
            return self.get_single_image_info()
    
    def get_single_image_info(self) -> Optional[str]:
        """단일 이미지 정보 반환 (기존 방식)"""
        if not self.selected_image_path:
            return None
        
        filename = os.path.basename(self.selected_image_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        return f"이미지 첨부: {filename}"
    
    def get_multiple_image_info(self) -> Optional[str]:
        """다중 이미지 정보 반환"""
        if not self.images:
            return None
        
        count = len(self.images)
        if count == 1:
            filename = self.images[0]['filename']
            if len(filename) > 25:
                filename = filename[:22] + "..."
            return f"이미지 첨부: {filename}"
        else:
            return f"이미지 {count}개 첨부"
    
    def get_image_info_by_index(self, index: int) -> Optional[str]:
        """인덱스별 이미지 정보 반환"""
        if self.current_mode == "multiple" and 0 <= index < len(self.images):
            filename = self.images[index]['filename']
            if len(filename) > 25:
                filename = filename[:22] + "..."
            return f"이미지 {index+1}: {filename}"
        return None
    
    def get_short_filename(self, index: int = 0) -> Optional[str]:
        """짧은 파일명 반환"""
        if self.current_mode == "multiple":
            if 0 <= index < len(self.images):
                filename = self.images[index]['filename']
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                return filename
        else:
            if not self.selected_image_path:
                return None
            filename = os.path.basename(self.selected_image_path)
            if len(filename) > 30:
                filename = filename[:27] + "..."
            return filename
        return None
    
    def clear_image(self):
        """선택된 이미지 초기화"""
        self.selected_image = None
        self.selected_image_path = None
        self.preview_photo = None
    
    def clear_multiple_images(self):
        """다중 이미지 모두 초기화"""
        self.images.clear()
    
    def clear_all_images(self):
        """모든 이미지 초기화 (단일/다중 모두)"""
        self.clear_image()
        self.clear_multiple_images()
    
    def has_image(self) -> bool:
        """이미지가 선택되어 있는지 확인"""
        if self.current_mode == "multiple":
            return len(self.images) > 0
        else:
            return self.selected_image is not None
    
    def get_image_for_api(self) -> Optional[Image.Image]:
        """API 호출용 단일 이미지 반환 (하위 호환성)"""
        if self.current_mode == "multiple" and self.images:
            return self.images[0]['image']  # 첫 번째 이미지 반환
        else:
            return self.selected_image
    
    def get_images_for_api(self) -> List[Image.Image]:
        """API 호출용 모든 이미지 반환"""
        if self.current_mode == "multiple":
            return [img_info['image'] for img_info in self.images]
        elif self.selected_image:
            return [self.selected_image]
        else:
            return []
    
    def get_image_paths(self) -> List[str]:
        """모든 이미지 경로 반환"""
        if self.current_mode == "multiple":
            return [img_info['path'] for img_info in self.images]
        elif self.selected_image_path:
            return [self.selected_image_path]
        else:
            return []