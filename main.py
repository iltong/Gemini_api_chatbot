"""
Gemini Chat Studio - 메인 실행 파일
모듈화된 구조로 개선된 Gemini 챗봇 애플리케이션
"""

import sys
import os
from tkinter import messagebox

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from core.chat_application import ChatApplication
except ImportError as e:
    messagebox.showerror("모듈 오류", f"필요한 모듈을 불러올 수 없습니다: {e}\n\n필요한 패키지를 설치해주세요:\npip install google-generativeai python-dotenv pillow")
    sys.exit(1)

def main():
    """메인 함수"""
    try:
        # 애플리케이션 생성 및 실행
        app = ChatApplication()
        app.run()
        
    except KeyboardInterrupt:
        print("\n애플리케이션이 사용자에 의해 중단되었습니다.")
        
    except Exception as e:
        messagebox.showerror("오류", f"프로그램 실행 중 오류가 발생했습니다:\n{str(e)}")
        
    finally:
        print("Gemini Chat Studio 종료")

if __name__ == "__main__":
    main()