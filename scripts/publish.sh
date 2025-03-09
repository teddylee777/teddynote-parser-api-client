#!/bin/bash

# 스크립트가 있는 디렉토리의 상위 디렉토리로 이동 (프로젝트 루트)
cd "$(dirname "$0")/.."

# 필요한 패키지 설치
echo "필요한 패키지 설치 중..."
pip install --upgrade pip build twine

# 기존 빌드 제거
echo "기존 빌드 제거 중..."
rm -rf build/ dist/ *.egg-info/

# 패키지 빌드
echo "패키지 빌드 중..."
python -m build

# 패키지 내용 확인
echo "빌드된 패키지 내용 확인 중..."
twine check dist/*

# 테스트 PyPI 업로드 (선택 사항)
read -p "테스트 PyPI에 먼저 업로드하시겠습니까? (y/n): " test_upload
if [ "$test_upload" = "y" ]; then
    echo "테스트 PyPI에 업로드 중..."
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
    echo "테스트 PyPI에 업로드 완료!"
    echo "테스트 PyPI에서 패키지를 설치하려면: pip install --index-url https://test.pypi.org/simple/ teddynote-parser-client"
fi

# 실제 PyPI 업로드
read -p "실제 PyPI에 업로드하시겠습니까? (y/n): " live_upload
if [ "$live_upload" = "y" ]; then
    echo "PyPI에 업로드 중..."
    twine upload dist/*
    echo "PyPI에 업로드 완료!"
    echo "PyPI에서 패키지를 설치하려면: pip install teddynote-parser-client"
fi

echo "완료!" 