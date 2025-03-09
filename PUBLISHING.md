# PyPI 패키지 게시 가이드

이 문서는 `teddynote-parser-client` 패키지를 PyPI에 게시하는 방법을 설명합니다.

## 사전 준비

1. [PyPI](https://pypi.org/) 계정이 필요합니다.
2. [TestPyPI](https://test.pypi.org/) 계정도 있으면 좋습니다(테스트 업로드용).
3. `build`와 `twine` 패키지가 설치되어 있어야 합니다:

```bash
pip install --upgrade pip build twine
```

4. PyPI 인증 정보를 설정합니다. 다음 파일을 만들어 주세요: `~/.pypirc`

```
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = your_username
password = your_password

[testpypi]
repository = https://test.pypi.org/legacy/
username = your_username
password = your_password
```

대신 `twine`을 실행할 때 `--username`과 `--password` 옵션을 사용하거나 업로드 시 자격 증명을 입력할 수도 있습니다.

## 패키지 빌드 및 게시

### 자동 스크립트 사용

제공된 스크립트를 사용하여 패키지 빌드 및 배포를 자동화할 수 있습니다:

```bash
./scripts/publish.sh
```

### 수동 게시

1. 기존 빌드 정리:

```bash
rm -rf build/ dist/ *.egg-info/
```

2. 패키지 빌드:

```bash
python -m build
```

3. 패키지 확인:

```bash
twine check dist/*
```

4. TestPyPI에 업로드 (선택 사항):

```bash
twine upload --repository testpypi dist/*
```

5. 실제 PyPI에 업로드:

```bash
twine upload dist/*
```

## 버전 업데이트

새 버전을 배포하기 전에 다음 파일에서 버전 번호를 업데이트하세요:

- `teddynote_parser_client/__init__.py`의 `__version__` 변수
- `pyproject.toml`의 `version` 필드

## 확인

패키지가 성공적으로 게시되었는지 확인하려면:

1. TestPyPI에서 설치:

```bash
pip install --index-url https://test.pypi.org/simple/ teddynote-parser-client
```

2. 실제 PyPI에서 설치:

```bash
pip install teddynote-parser-client
```

패키지를 설치한 후 다음을 실행하여 작동하는지 확인하세요:

```python
from teddynote_parser_client import TeddyNoteParserClient
print(TeddyNoteParserClient.__doc__)
``` 