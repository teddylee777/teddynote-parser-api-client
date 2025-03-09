"""
TeddyNote Parser 클라이언트 테스트 모듈
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from teddynote_parser_client.client import TeddyNoteParserClient


class TestTeddyNoteParserClient(unittest.TestCase):
    """TeddyNoteParserClient 클래스에 대한 단위 테스트"""

    def setUp(self):
        """테스트 설정"""
        # 테스트용 클라이언트 인스턴스 생성
        self.client = TeddyNoteParserClient(
            api_url="http://test-api-url:9997",
            upstage_api_key="test-upstage-api-key",
            openai_api_key="test-openai-api-key",
        )

    @patch("teddynote_parser_client.client.requests.get")
    def test_health_check(self, mock_get):
        """health_check 메소드 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "timestamp": "2023-01-01T00:00:00Z",
        }
        mock_get.return_value = mock_response

        # 메소드 호출
        result = self.client.health_check()

        # 결과 검증
        self.assertEqual(result["status"], "ok")
        mock_get.assert_called_once_with(
            "http://test-api-url:9997/health", timeout=self.client.timeout
        )

    @patch("teddynote_parser_client.client.requests.post")
    def test_parse_pdf(self, mock_post):
        """parse_pdf 메소드 테스트"""
        # Mock 파일 생성
        test_file = Path("test_file.pdf")
        with open(test_file, "w") as f:
            f.write("test content")

        try:
            # Mock 응답 설정
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "job_id": "test-job-id",
                "status": "processing",
            }
            mock_post.return_value = mock_response

            # 메소드 호출
            result = self.client.parse_pdf(test_file)

            # 결과 검증
            self.assertEqual(result["job_id"], "test-job-id")
            self.assertEqual(result["status"], "processing")

            # 요청이 올바른 인자로 호출되었는지 검증
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], "http://test-api-url:9997/parse")
            self.assertIn("headers", kwargs)
            self.assertIn("files", kwargs)
            self.assertIn("data", kwargs)
            self.assertIn("timeout", kwargs)

        finally:
            # 테스트 파일 삭제
            if test_file.exists():
                test_file.unlink()

    @patch("teddynote_parser_client.client.requests.get")
    def test_get_job_status(self, mock_get):
        """get_job_status 메소드 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "test-job-id",
            "status": "completed",
        }
        mock_get.return_value = mock_response

        # 메소드 호출
        result = self.client.get_job_status("test-job-id")

        # 결과 검증
        self.assertEqual(result["job_id"], "test-job-id")
        self.assertEqual(result["status"], "completed")
        mock_get.assert_called_once_with(
            "http://test-api-url:9997/status/test-job-id", timeout=self.client.timeout
        )


if __name__ == "__main__":
    unittest.main()
