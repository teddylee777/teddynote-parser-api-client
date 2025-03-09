"""
TeddyNote Parser 클라이언트 명령줄 인터페이스 (CLI)

이 모듈은 TeddyNote Parser API 클라이언트를 명령줄에서 사용할 수 있는 인터페이스를 제공합니다.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from teddynote_parser_client.client import TeddyNoteParserClient


def setup_logger() -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger("teddynote_parser")
    logger.setLevel(logging.INFO)

    # 콘솔 핸들러 추가
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def health_check_command(
    client: TeddyNoteParserClient, args: argparse.Namespace
) -> None:
    """API 서버 건강 상태 확인 명령 처리"""
    try:
        result = client.health_check()
        print(f"API 서버 상태: {result}")
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


def parse_pdf_command(client: TeddyNoteParserClient, args: argparse.Namespace) -> None:
    """PDF 파일 파싱 명령 처리"""
    try:
        # PDF 파일 파싱 요청
        result = client.parse_pdf(
            pdf_path=args.pdf_path,
            language=args.language,
            include_image=args.include_image,
            batch_size=args.batch_size,
            test_page=args.test_page,
        )
        job_id = result["job_id"]
        print(f"파싱 작업 시작됨. 작업 ID: {job_id}")

        # 작업 완료 대기 (요청 시)
        if args.wait:
            print("작업 완료 대기 중...")
            job_status = client.wait_for_job_completion(
                job_id,
                check_interval=args.check_interval,
                max_attempts=args.max_attempts,
            )
            print(f"작업 완료. 상태: {job_status['status']}")

            # 결과 다운로드 (요청 시)
            if args.download:
                save_dir = args.save_dir or "parser_results"
                zip_path, extract_path = client.download_result(
                    job_id,
                    save_dir=save_dir,
                    extract=args.extract,
                    overwrite=args.overwrite,
                )
                print(f"결과 다운로드 완료: {zip_path}")
                if extract_path:
                    print(f"압축 해제 디렉토리: {extract_path}")
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


def status_command(client: TeddyNoteParserClient, args: argparse.Namespace) -> None:
    """작업 상태 확인 명령 처리"""
    try:
        job_status = client.get_job_status(args.job_id)
        print(f"작업 ID '{args.job_id}'의 상태: {job_status}")
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


def download_command(client: TeddyNoteParserClient, args: argparse.Namespace) -> None:
    """결과 다운로드 명령 처리"""
    try:
        save_dir = args.save_dir or "parser_results"
        zip_path, extract_path = client.download_result(
            args.job_id,
            save_dir=save_dir,
            extract=args.extract,
            overwrite=args.overwrite,
        )
        print(f"결과 다운로드 완료: {zip_path}")
        if extract_path:
            print(f"압축 해제 디렉토리: {extract_path}")
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


def list_jobs_command(client: TeddyNoteParserClient, args: argparse.Namespace) -> None:
    """작업 목록 조회 명령 처리"""
    try:
        jobs = client.list_all_jobs()
        print(f"총 {len(jobs)}개의 작업이 있습니다:")
        for job in jobs:
            print(
                f"작업 ID: {job.get('job_id', 'N/A')}, 상태: {job.get('status', 'N/A')}"
            )
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


def main() -> None:
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="TeddyNote Parser API 클라이언트 명령줄 도구"
    )

    # 공통 인자
    parser.add_argument(
        "--api-url",
        default=os.environ.get("TEDDYNOTE_API_URL", "http://localhost:9997"),
        help="API 서버 URL (기본값: 환경 변수 TEDDYNOTE_API_URL 또는 http://localhost:9997)",
    )
    parser.add_argument(
        "--upstage-api-key",
        default=os.environ.get("UPSTAGE_API_KEY"),
        help="UPSTAGE API 키 (기본값: 환경 변수 UPSTAGE_API_KEY)",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="OpenAI API 키 (기본값: 환경 변수 OPENAI_API_KEY)",
    )
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")

    # 하위 명령어 설정
    subparsers = parser.add_subparsers(dest="command", help="사용할 명령")

    # 건강 상태 확인 명령
    health_parser = subparsers.add_parser("health", help="API 서버 건강 상태 확인")

    # PDF 파싱 명령
    parse_parser = subparsers.add_parser("parse", help="PDF 파일 파싱")
    parse_parser.add_argument("pdf_path", help="파싱할 PDF 파일 경로")
    parse_parser.add_argument(
        "--language", default="Korean", help="문서 언어 (기본값: Korean)"
    )
    parse_parser.add_argument(
        "--include-image",
        action="store_true",
        default=True,
        help="파싱 결과에 이미지 포함 (기본값: True)",
    )
    parse_parser.add_argument(
        "--batch-size",
        type=int,
        default=30,
        help="처리할 PDF 페이지의 배치 크기 (기본값: 30)",
    )
    parse_parser.add_argument("--test-page", type=int, help="처리할 최대 페이지 수")
    parse_parser.add_argument("--wait", action="store_true", help="작업 완료까지 대기")
    parse_parser.add_argument(
        "--check-interval", type=int, default=2, help="상태 확인 간격(초) (기본값: 2초)"
    )
    parse_parser.add_argument(
        "--max-attempts", type=int, default=60, help="최대 시도 횟수 (기본값: 60회)"
    )
    parse_parser.add_argument(
        "--download", action="store_true", help="완료 후 결과 다운로드"
    )
    parse_parser.add_argument(
        "--save-dir", help="결과를 저장할 디렉토리 (기본값: parser_results)"
    )
    parse_parser.add_argument(
        "--extract", action="store_true", help="ZIP 파일 압축 해제"
    )
    parse_parser.add_argument(
        "--overwrite", action="store_true", help="기존 파일 덮어쓰기"
    )

    # 작업 상태 확인 명령
    status_parser = subparsers.add_parser("status", help="작업 상태 확인")
    status_parser.add_argument("job_id", help="확인할 작업 ID")

    # 결과 다운로드 명령
    download_parser = subparsers.add_parser("download", help="작업 결과 다운로드")
    download_parser.add_argument("job_id", help="다운로드할 작업 ID")
    download_parser.add_argument(
        "--save-dir", help="결과를 저장할 디렉토리 (기본값: parser_results)"
    )
    download_parser.add_argument(
        "--extract", action="store_true", help="ZIP 파일 압축 해제"
    )
    download_parser.add_argument(
        "--overwrite", action="store_true", help="기존 파일 덮어쓰기"
    )

    # 작업 목록 조회 명령
    jobs_parser = subparsers.add_parser("jobs", help="모든 작업 목록 조회")

    # 인자 파싱
    args = parser.parse_args()

    # 명령어가 제공되지 않은 경우 도움말 표시
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 로깅 설정
    logger = setup_logger()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # 클라이언트 초기화
    client = TeddyNoteParserClient(
        api_url=args.api_url,
        upstage_api_key=args.upstage_api_key,
        openai_api_key=args.openai_api_key,
        logger=logger,
    )

    # 명령어 처리
    commands = {
        "health": health_check_command,
        "parse": parse_pdf_command,
        "status": status_command,
        "download": download_command,
        "jobs": list_jobs_command,
    }

    commands[args.command](client, args)


if __name__ == "__main__":
    main()
