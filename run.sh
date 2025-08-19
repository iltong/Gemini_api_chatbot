#!/bin/bash

# 색깔 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Gemini AI Chat Assistant v6 (모듈화)${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Python 설치 확인
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}[ERROR] Python이 설치되지 않았습니다.${NC}"
    echo -e "${RED}Python 3.7 이상을 설치해주세요.${NC}"
    echo
    exit 1
fi

# Python 명령어 결정
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

echo -e "${GREEN}[INFO] Python 설치 확인 완료${NC}"

# Python 버전 확인
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[INFO] Python 버전: $PYTHON_VERSION${NC}"

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INFO] 가상환경을 생성합니다...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}[INFO] 가상환경 생성 완료${NC}"
else
    echo -e "${GREEN}[INFO] 기존 가상환경 발견${NC}"
fi
echo

# 가상환경 활성화 확인
if [ ! -f "venv/bin/python" ] && [ ! -f "venv/Scripts/python.exe" ]; then
    echo -e "${RED}[ERROR] 가상환경이 올바르게 생성되지 않았습니다.${NC}"
    echo -e "${YELLOW}가상환경을 다시 생성합니다...${NC}"
    rm -rf venv 2>/dev/null
    $PYTHON_CMD -m venv venv
fi

# 가상환경 Python 경로 설정
if [ -f "venv/bin/python" ]; then
    VENV_PYTHON="venv/bin/python"
    VENV_PIP="venv/bin/pip"
else
    VENV_PYTHON="venv/Scripts/python.exe"
    VENV_PIP="venv/Scripts/pip.exe"
fi

# 필요한 패키지 설치 확인 (가상환경 내에서)
echo -e "${YELLOW}[INFO] 가상환경에서 필요한 패키지를 확인하고 설치합니다...${NC}"
$VENV_PIP install google-generativeai python-dotenv pillow > /dev/null 2>&1

# 선택적 패키지 설치 시도 (가상환경 내에서)
echo -e "${YELLOW}[INFO] 선택적 패키지 설치 시도 중...${NC}"
$VENV_PIP install tkinterdnd2 > /dev/null 2>&1

echo -e "${GREEN}[INFO] 패키지 설치 완료${NC}"
echo

# API 키 확인
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING] .env 파일이 없습니다.${NC}"
    echo -e "${YELLOW}프로그램 실행 시 API 키를 입력해야 합니다.${NC}"
    echo
fi

# 실행 권한 확인 및 설정
if [ ! -x "$0" ]; then
    echo -e "${YELLOW}[INFO] 실행 권한을 설정합니다...${NC}"
    chmod +x "$0"
fi

# 애플리케이션 실행 (가상환경의 Python 사용)
echo -e "${GREEN}[INFO] 가상환경에서 Gemini AI Chat Assistant 실행 중...${NC}"
echo

$VENV_PYTHON main.py

# 종료 코드 확인
exit_code=$?
echo
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}프로그램이 정상적으로 종료되었습니다.${NC}"
else
    echo -e "${RED}프로그램이 오류와 함께 종료되었습니다. (코드: $exit_code)${NC}"
fi

echo -e "${BLUE}실행을 완료하려면 Enter 키를 누르세요...${NC}"
read -r