"""
TeddyNote Parser API 클라이언트 모듈

이 모듈은 TeddyNote Parser API와 상호작용하기 위한 클라이언트 클래스를 정의합니다.
"""

import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
import logging
import zipfile
from datetime import datetime


class TeddyNoteParserClient:
    """
    TeddyNote Parser API 클라이언트 클래스

    이 클래스는 TeddyNote Parser API와 상호작용하는 메소드를 제공합니다:
    - 헬스 체크
    - PDF 파일 파싱 요청
    - 작업 상태 확인
    - 결과 다운로드
    """

    def __init__(
        self,
        api_url: str = "http://localhost:9997",
        upstage_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        language: str = "Korean",
        include_image: bool = True,
        batch_size: int = 30,
        test_page: Optional[int] = None,
        timeout: int = 60,
        logger: Optional[logging.Logger] = None,
    ):
        """
        TeddyNote Parser API 클라이언트 초기화

        Args:
            api_url: API 서버 URL (기본값: http://localhost:9997)
            upstage_api_key: UPSTAGE API 키 (환경 변수에서 가져올 수 있음)
            openai_api_key: OpenAI API 키 (환경 변수에서 가져올 수 있음)
            language: 문서 언어 (기본값: Korean)
            include_image: 파싱 결과에 이미지 포함 여부 (기본값: True)
            batch_size: 처리할 PDF 페이지의 배치 크기 (기본값: 30)
            test_page: 처리할 최대 페이지 수 (처음부터 지정한 페이지까지만 처리, 기본값: None - 모든 페이지 처리)
            timeout: API 요청 제한시간 (초 단위, 기본값: 60초)
            logger: 로깅에 사용할 로거 인스턴스 (기본값: None)
        """
        # API 서버 URL 설정
        self.api_url = api_url.rstrip("/")

        # API 엔드포인트 설정
        self.health_endpoint = f"{self.api_url}/health"
        self.parse_endpoint = f"{self.api_url}/parse"
        self.status_endpoint = f"{self.api_url}/status"
        self.download_endpoint = f"{self.api_url}/download"
        self.jobs_endpoint = f"{self.api_url}/jobs"

        # API 키 설정
        self.upstage_api_key = upstage_api_key or os.environ.get("UPSTAGE_API_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")

        # 파싱 옵션 설정
        self.language = language
        self.include_image = include_image
        self.batch_size = batch_size
        self.test_page = test_page

        # 요청 제한시간 설정
        self.timeout = timeout

        # 로거 설정
        self.logger = logger or logging.getLogger(__name__)

        # API 키가 제공되었는지 확인
        if not self.upstage_api_key:
            self.logger.warning("UPSTAGE API 키가 설정되지 않았습니다.")

        if not self.openai_api_key:
            self.logger.warning("OpenAI API 키가 설정되지 않았습니다.")

    def health_check(self) -> Dict[str, Any]:
        """
        API 서버 건강 상태 확인

        Returns:
            Dict[str, Any]: 서버 상태 정보 (상태 및 타임스탬프)

        Raises:
            requests.RequestException: API 요청 중 오류 발생
        """
        try:
            response = requests.get(self.health_endpoint, timeout=self.timeout)
            response.raise_for_status()
            self.logger.info("API 서버가 정상적으로 응답했습니다.")
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"API 서버 건강 상태 확인 실패: {e}")
            raise

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        language: Optional[str] = None,
        include_image: Optional[bool] = None,
        batch_size: Optional[int] = None,
        test_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        PDF 파일을 업로드하고 파싱 작업 요청

        Args:
            pdf_path: 파싱할 PDF 파일 경로
            language: 문서 언어 (기본값: 인스턴스 초기화 시 설정값)
            include_image: 파싱 결과에 이미지 포함 여부 (기본값: 인스턴스 초기화 시 설정값)
            batch_size: 처리할 PDF 페이지의 배치 크기 (기본값: 인스턴스 초기화 시 설정값)
            test_page: 처리할 최대 페이지 수 (처음부터 지정한 페이지까지만 처리, 기본값: 인스턴스 초기화 시 설정값)

        Returns:
            Dict[str, Any]: 작업 ID와 작업 상태를 포함한 응답

        Raises:
            FileNotFoundError: PDF 파일을 찾을 수 없을 때
            ValueError: API 키가 설정되지 않았을 때
            requests.RequestException: API 요청 중 오류 발생
        """
        # 파일 경로를 Path 객체로 변환
        pdf_path = Path(pdf_path)

        # 파일 존재 여부 확인
        if not pdf_path.exists():
            error_msg = f"파일을 찾을 수 없습니다: {pdf_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # API 키 확인
        if not self.upstage_api_key or not self.openai_api_key:
            error_msg = "UPSTAGE API 키와 OpenAI API 키가 필요합니다."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 요청 파라미터 설정
        lang = language if language is not None else self.language
        img = include_image if include_image is not None else self.include_image
        batch = batch_size if batch_size is not None else self.batch_size
        test = test_page if test_page is not None else self.test_page

        # 디버깅 정보 출력
        self.logger.debug(
            f"파싱 요청 파라미터 초기값: language={language}, include_image={include_image}, batch_size={batch_size}, test_page={test_page}"
        )
        self.logger.debug(
            f"파싱 요청 파라미터 결정값: language={lang}, include_image={img}, batch_size={batch}, test_page={test}"
        )

        # API 요청 준비
        headers = {
            "X-UPSTAGE-API-KEY": self.upstage_api_key,
            "X-OPENAI-API-KEY": self.openai_api_key,
        }

        # 파일 및 폼 데이터 준비 (FormData 형식)
        files = {"file": (pdf_path.name, open(pdf_path, "rb"), "application/pdf")}

        # FormData에 포함될 추가 필드
        data = {
            "language": str(lang),
            "include_image": str(img).lower(),
            "batch_size": str(batch),
        }

        # test_page가 None이 아닌 경우에만 추가
        if test is not None:
            data["test_page"] = str(test)
            self.logger.debug(f"test_page={test} 파라미터가 API 요청에 추가되었습니다.")
        else:
            self.logger.debug(
                "test_page 파라미터가 None이므로 API 요청에 포함되지 않습니다."
            )

        self.logger.debug(f"API 요청에 사용될 데이터: {data}")
        self.logger.debug(f"API 요청에 사용될 파일: {pdf_path.name}")

        try:
            # API 요청 수행
            self.logger.info(f"파일 '{pdf_path.name}'에 대한 파싱 작업 요청 중...")
            self.logger.info(
                f"파싱 옵션: 언어={lang}, 이미지 포함={img}, 배치 크기={batch}, 처리 페이지 수={test}"
            )

            response = requests.post(
                self.parse_endpoint,
                headers=headers,
                files=files,
                data=data,  # FormData로 전송
                timeout=self.timeout,
            )

            if response.status_code != 200:
                self.logger.error(
                    f"API 요청 실패. 상태 코드: {response.status_code}, 응답: {response.text}"
                )
                response.raise_for_status()

            # 응답 처리
            result = response.json()
            self.logger.info(f"파싱 작업이 시작되었습니다. 작업 ID: {result['job_id']}")
            return result
        except requests.RequestException as e:
            self.logger.error(f"파싱 작업 요청 실패: {e}")
            raise
        finally:
            # 파일 핸들 닫기
            files["file"][1].close()

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        작업 ID를 사용하여 작업 상태 확인

        Args:
            job_id: 확인할 작업 ID

        Returns:
            Dict[str, Any]: 작업 상태 정보

        Raises:
            requests.RequestException: API 요청 중 오류 발생
        """
        try:
            response = requests.get(
                f"{self.status_endpoint}/{job_id}", timeout=self.timeout
            )
            response.raise_for_status()

            job_status = response.json()
            status = job_status.get("status", "unknown")
            self.logger.info(f"작업 ID '{job_id}'의 현재 상태: {status}")

            return job_status
        except requests.RequestException as e:
            self.logger.error(f"작업 상태 확인 실패: {e}")
            raise

    def wait_for_job_completion(
        self, job_id: str, check_interval: int = 2, max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        작업이 완료될 때까지 대기

        Args:
            job_id: 대기할 작업 ID
            check_interval: 상태 확인 간격(초) (기본값: 2초)
            max_attempts: 최대 시도 횟수 (기본값: 60회, 총 최대 대기 시간: 120초)

        Returns:
            Dict[str, Any]: 작업 상태 정보

        Raises:
            TimeoutError: 최대 시도 횟수 초과
            requests.RequestException: API 요청 중 오류 발생
        """
        self.logger.info(f"작업 ID '{job_id}'의 완료 대기 중...")
        self.logger.info(
            f"상태 확인 간격: {check_interval}초, 최대 시도 횟수: {max_attempts}회"
        )

        for attempt in range(max_attempts):
            job_status = self.get_job_status(job_id)
            status = job_status.get("status", "unknown")

            if status in ["completed", "failed"]:
                self.logger.info(
                    f"작업 ID '{job_id}'가 {status} 상태로 완료되었습니다."
                )
                return job_status

            self.logger.debug(
                f"[{attempt + 1}/{max_attempts}] 작업 ID '{job_id}'의 현재 상태: {status}. {check_interval}초 후 다시 확인합니다."
            )
            time.sleep(check_interval)

        error_msg = f"작업 ID '{job_id}'의 완료 대기 시간이 초과되었습니다. 최대 {max_attempts * check_interval}초 경과."
        self.logger.error(error_msg)
        raise TimeoutError(error_msg)

    def download_result(
        self,
        job_id: str,
        save_dir: Union[str, Path] = "parser_results",
        extract: bool = False,
        overwrite: bool = False,
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        작업 결과를 다운로드하고 선택적으로 압축 해제

        Args:
            job_id: 다운로드할 작업 ID
            save_dir: 결과를 저장할 디렉토리 (기본값: "parser_results")
            extract: 다운로드한 ZIP 파일의 압축 해제 여부 (기본값: False)
            overwrite: 이미 존재하는 파일 덮어쓰기 여부 (기본값: False)

        Returns:
            Tuple[Optional[Path], Optional[Path]]: (ZIP 파일 경로, 압축 해제 디렉토리 경로) 튜플.
            압축 해제를 요청하지 않은 경우 두 번째 값은 None.

        Raises:
            ValueError: 작업 ID가 완료 상태가 아닐 때
            FileExistsError: 파일이 이미 존재하고 overwrite=False일 때
            requests.RequestException: API 요청 중 오류 발생
        """
        # 작업 상태 확인
        job_status = self.get_job_status(job_id)
        status = job_status.get("status", "unknown")

        # 작업이 완료되지 않은 경우
        if status != "completed":
            error_msg = f"작업 ID '{job_id}'가 완료되지 않았습니다. 현재 상태: {status}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 저장 디렉토리 생성
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # ZIP 파일 저장 경로
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        zip_filename = f"{job_id}_{timestamp}.zip"
        zip_path = save_dir / zip_filename

        # 파일이 이미 존재하고 덮어쓰기를 허용하지 않는 경우
        if zip_path.exists() and not overwrite:
            error_msg = f"파일이 이미 존재합니다: {zip_path}. overwrite=True로 설정하여 덮어쓰기를 허용하세요."
            self.logger.error(error_msg)
            raise FileExistsError(error_msg)

        # 다운로드 URL
        download_url = f"{self.download_endpoint}/{job_id}"

        try:
            # 파일 다운로드
            self.logger.info(f"작업 ID '{job_id}'의 결과 다운로드 중...")
            response = requests.get(download_url, timeout=self.timeout)
            response.raise_for_status()

            # 파일 저장
            with open(zip_path, "wb") as f:
                f.write(response.content)
            self.logger.info(f"결과가 성공적으로 다운로드되었습니다: {zip_path}")

            # 선택적 압축 해제
            extract_path = None
            if extract:
                extract_dir = save_dir / job_id
                extract_path = self._extract_zip(zip_path, extract_dir)
                self.logger.info(
                    f"ZIP 파일의 압축이 성공적으로 해제되었습니다: {extract_path}"
                )

            return zip_path, extract_path

        except requests.RequestException as e:
            self.logger.error(f"결과 다운로드 실패: {e}")
            raise

    def _extract_zip(self, zip_path: Path, extract_path: Path) -> Path:
        """
        ZIP 파일 압축 해제

        Args:
            zip_path: 압축 해제할 ZIP 파일 경로
            extract_path: 압축 해제할 디렉토리 경로

        Returns:
            Path: 압축 해제된 디렉토리 경로

        Raises:
            zipfile.BadZipFile: ZIP 파일이 손상된 경우
            OSError: 파일 시스템 오류 발생 시
        """
        try:
            # 추출 디렉토리 생성
            extract_path.mkdir(parents=True, exist_ok=True)

            # ZIP 파일 압축 해제
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            self.logger.info(
                f"ZIP 파일 '{zip_path}'의 압축을 '{extract_path}'에 해제했습니다."
            )
            return extract_path

        except (zipfile.BadZipFile, OSError) as e:
            self.logger.error(f"ZIP 파일 압축 해제 실패: {e}")
            raise

    def list_all_jobs(self) -> List[Dict[str, Any]]:
        """
        모든 작업 목록 조회

        Returns:
            List[Dict[str, Any]]: 작업 목록 (작업 ID, 상태 및 기타 정보 포함)

        Raises:
            requests.RequestException: API 요청 중 오류 발생
        """
        try:
            self.logger.info("모든 작업 목록 조회 중...")
            response = requests.get(self.jobs_endpoint, timeout=self.timeout)
            response.raise_for_status()

            jobs = response.json()
            self.logger.info(f"총 {len(jobs)} 개의 작업이 조회되었습니다.")
            return jobs

        except requests.RequestException as e:
            self.logger.error(f"작업 목록 조회 실패: {e}")
            raise
