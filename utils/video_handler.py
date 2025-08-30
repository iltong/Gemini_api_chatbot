"""
동영상 처리 유틸리티
"""

import os
import cv2
import tempfile
from PIL import Image, ImageTk
from typing import Optional, Tuple, Dict, Any, List

class VideoHandler:
    """동영상 처리 클래스"""
    
    # 지원되는 동영상 확장자
    SUPPORTED_VIDEO_EXTENSIONS = {
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp'
    }
    
    # 동영상 타입별 설명
    VIDEO_DESCRIPTIONS = {
        '.mp4': 'MP4 Video',
        '.avi': 'AVI Video',
        '.mov': 'QuickTime Movie',
        '.wmv': 'Windows Media Video',
        '.flv': 'Flash Video',
        '.webm': 'WebM Video',
        '.mkv': 'Matroska Video',
        '.m4v': 'iTunes Video',
        '.3gp': '3GPP Video'
    }
    
    def __init__(self, max_file_size_mb: int = 2048):
        """
        VideoHandler 초기화
        
        Args:
            max_file_size_mb: 최대 파일 크기 (MB)
        """
        self.max_file_size_mb = max_file_size_mb
        self.selected_video_path: Optional[str] = None
        self.video_info: Optional[Dict[str, Any]] = None
        self.thumbnail_image: Optional[Image.Image] = None
        self.thumbnail_photo: Optional[ImageTk.PhotoImage] = None
    
    def is_supported_video(self, file_path: str) -> bool:
        """동영상 파일인지 확인"""
        if not os.path.exists(file_path):
            return False
        
        file_ext = os.path.splitext(file_path.lower())[1]
        return file_ext in self.SUPPORTED_VIDEO_EXTENSIONS
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """동영상 메타데이터 추출"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {}
            
            # 기본 정보 추출
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 파일 크기
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            
            cap.release()
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration_seconds': duration,
                'duration_formatted': self._format_duration(duration),
                'file_size_bytes': file_size,
                'file_size_mb': file_size_mb,
                'resolution': f"{width}x{height}",
                'filename': os.path.basename(video_path)
            }
            
        except Exception as e:
            print(f"동영상 정보 추출 실패: {e}")
            return {}
    
    def _format_duration(self, seconds: float) -> str:
        """시간을 MM:SS 형식으로 포맷"""
        if seconds <= 0:
            return "00:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def generate_thumbnail(self, video_path: str, size: Tuple[int, int] = (80, 80)) -> Optional[Image.Image]:
        """동영상 첫 번째 프레임에서 썸네일 생성"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return None
            
            # 첫 번째 프레임 읽기
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            # BGR to RGB 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # PIL Image로 변환
            pil_image = Image.fromarray(frame_rgb)
            
            # 썸네일 크기로 리사이즈
            pil_image.thumbnail(size, Image.Resampling.LANCZOS)
            
            return pil_image
            
        except Exception as e:
            print(f"썸네일 생성 실패: {e}")
            return None
    
    def load_video(self, file_path: str) -> Tuple[bool, str]:
        """
        동영상 로드 및 검증
        Returns: (성공 여부, 오류 메시지)
        """
        try:
            # 파일 존재 확인
            if not os.path.exists(file_path):
                return False, "파일이 존재하지 않습니다."
            
            # 지원 형식 확인
            if not self.is_supported_video(file_path):
                return False, f"지원하지 않는 동영상 형식입니다.\n지원 형식: {', '.join(self.SUPPORTED_VIDEO_EXTENSIONS)}"
            
            # 파일 크기 확인
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                return False, f"파일 크기가 너무 큽니다. (최대: {self.max_file_size_mb}MB, 현재: {file_size_mb:.1f}MB)"
            
            # 동영상 정보 추출
            video_info = self.get_video_info(file_path)
            if not video_info:
                return False, "동영상 파일을 읽을 수 없습니다."
            
            # 썸네일 생성
            thumbnail = self.generate_thumbnail(file_path)
            if not thumbnail:
                return False, "동영상 썸네일을 생성할 수 없습니다."
            
            # 성공시 정보 저장
            self.selected_video_path = file_path
            self.video_info = video_info
            self.thumbnail_image = thumbnail
            self.thumbnail_photo = ImageTk.PhotoImage(thumbnail)
            
            return True, ""
            
        except Exception as e:
            return False, f"동영상 로드 중 오류 발생: {str(e)}"
    
    def has_video(self) -> bool:
        """동영상이 로드되어 있는지 확인"""
        return self.selected_video_path is not None and os.path.exists(self.selected_video_path)
    
    def get_video_display_info(self) -> str:
        """UI 표시용 동영상 정보 반환"""
        if not self.video_info:
            return "동영상 정보 없음"
        
        duration = self.video_info.get('duration_formatted', '00:00')
        resolution = self.video_info.get('resolution', '알수없음')
        size_mb = self.video_info.get('file_size_mb', 0)
        filename = self.video_info.get('filename', '알수없음')
        
        return f"🎬 {filename}\n⏱️ {duration} | 📐 {resolution} | 📦 {size_mb:.1f}MB"
    
    def get_video_for_api(self) -> Optional[str]:
        """API 전송용 동영상 파일 경로 반환"""
        return self.selected_video_path if self.has_video() else None
    
    def clear_video(self):
        """선택된 동영상 정보 초기화"""
        self.selected_video_path = None
        self.video_info = None
        self.thumbnail_image = None
        self.thumbnail_photo = None
    
    def get_short_filename(self, max_length: int = 20) -> str:
        """짧은 파일명 반환"""
        if not self.video_info:
            return "동영상"
        
        filename = self.video_info.get('filename', 'video')
        if len(filename) <= max_length:
            return filename
        
        # 확장자 분리
        name, ext = os.path.splitext(filename)
        
        # 이름 부분을 축약
        max_name_length = max_length - len(ext) - 3  # "..." 고려
        if len(name) > max_name_length:
            name = name[:max_name_length] + "..."
        
        return name + ext
    
    def get_supported_extensions_list(self) -> List[str]:
        """지원되는 확장자 목록 반환"""
        return sorted(list(self.SUPPORTED_VIDEO_EXTENSIONS))