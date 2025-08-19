@echo off
chcp 65001 > nul
title Gemini AI Chat Assistant v6

echo ========================================
echo   Gemini AI Chat Assistant v6 (모듈화)
echo ========================================

:: 빠른 시작 모드 확인 (두 번째 실행부터)
if exist "venv\Scripts\python.exe" if exist ".setup_complete" (
    echo [FAST START] 환경 설정 완료, 빠른 시작 모드
    goto :run_app
)

echo.

:: Python 설치 확인
echo [INFO] Python 환경 확인 중...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았거나 PATH에 등록되지 않았습니다.
    echo Python 3.7 이상을 설치하고 PATH에 등록해주세요.
    echo.
    pause
    exit /b 1
)

:: 가상환경 확인 및 생성
if not exist "venv" (
    echo [SETUP] 가상환경을 생성합니다...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo [SETUP] 가상환경 생성 완료
) else (
    echo [INFO] 기존 가상환경 발견
)

:: 가상환경 유효성 확인
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] 가상환경이 손상되었습니다. 재생성합니다...
    rmdir /s /q venv 2>nul
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] 가상환경 재생성 실패
        pause
        exit /b 1
    )
)

:: 필수 패키지 설치 상태 확인
echo [INFO] 패키지 설치 상태 확인 중...
set "packages_installed=true"

:: 필수 패키지 체크
venv\Scripts\python.exe -c "import google.generativeai" > nul 2>&1
if errorlevel 1 set "packages_installed=false"

venv\Scripts\python.exe -c "import dotenv" > nul 2>&1
if errorlevel 1 set "packages_installed=false"

venv\Scripts\python.exe -c "import PIL" > nul 2>&1
if errorlevel 1 set "packages_installed=false"

:: 필수 패키지 설치 (필요한 경우에만)
if "%packages_installed%"=="false" (
    echo [SETUP] 필수 패키지를 설치합니다...
    venv\Scripts\pip.exe install --upgrade pip > nul 2>&1
    venv\Scripts\pip.exe install google-generativeai python-dotenv pillow
    if errorlevel 1 (
        echo [ERROR] 필수 패키지 설치 실패
        pause
        exit /b 1
    )
    echo [SETUP] 필수 패키지 설치 완료
) else (
    echo [INFO] 모든 필수 패키지가 이미 설치되어 있습니다
)

:: 선택적 패키지 확인 및 설치
echo [INFO] 선택적 패키지 확인 중...
venv\Scripts\python.exe -c "import tkinterdnd2" > nul 2>&1
if errorlevel 1 (
    echo [SETUP] 드래그 앤 드롭 패키지 설치 시도...
    venv\Scripts\pip.exe install tkinterdnd2 > nul 2>&1
)

venv\Scripts\python.exe -c "import windnd" > nul 2>&1
if errorlevel 1 (
    echo [SETUP] Windows 드래그 앤 드롭 패키지 설치 시도...
    venv\Scripts\pip.exe install windnd > nul 2>&1
)

:: 설정 완료 마커 생성
echo setup_complete > .setup_complete
echo [INFO] 초기 설정 완료

:run_app
echo.
:: API 키 확인
if not exist ".env" (
    echo [WARNING] .env 파일이 없습니다.
    echo 프로그램 실행 시 API 키를 입력해야 합니다.
    echo.
)

:: 애플리케이션 실행
echo [START] Gemini AI Chat Assistant 실행 중...
echo.
venv\Scripts\python.exe main.py

:: 종료 처리
echo.
echo 프로그램이 종료되었습니다.
pause