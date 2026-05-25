"""Tests para scripts/gh_upload_images.py."""
import sys, json, subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_upload_images import upload_image


def test_upload_image_creates_payload_and_calls_api(tmp_path):
    """Debe llamar a gh api con el payload correcto."""
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)

    with patch.object(subprocess, "run") as mock_run:
        # Mock: check si existe (falla → no existe)
        check_result = subprocess.CompletedProcess([], 1, stdout="", stderr="")
        # Mock: upload exitoso
        upload_result = subprocess.CompletedProcess(
            [], 0,
            stdout="https://github.com/test/repo/blob/main/.issue-assets/1/test.png?raw=true",
            stderr="",
        )
        mock_run.side_effect = [check_result, upload_result]

        url = upload_image("test/repo", 1, str(img))

        assert url is not None
        assert "?raw=true" in url
        # Verificar que se llamó con --method PUT
        put_call = mock_run.call_args_list[1]
        args = put_call[0][0]
        assert "--method" in args
        assert "PUT" in args
        assert "--input" in args


def test_upload_skip_if_exists(tmp_path):
    """Si la imagen ya existe en el repo, debe saltarla."""
    img = tmp_path / "exists.png"
    img.write_bytes(b"dummy")

    with patch.object(subprocess, "run") as mock_run:
        # Mock: check exitoso (ya existe)
        check_result = subprocess.CompletedProcess(
            [], 0,
            stdout="https://github.com/test/repo/blob/main/.issue-assets/1/exists.png?raw=true",
            stderr="",
        )
        mock_run.return_value = check_result

        url = upload_image("test/repo", 1, str(img))

        assert url is not None
        assert "exists.png?raw=true" in url
        # Solo debe haber una llamada (el check, no el upload)
        assert mock_run.call_count == 1


def test_upload_file_not_found(tmp_path):
    """Imagen inexistente debe retornar None."""
    url = upload_image("test/repo", 1, "/no/existe.png")
    assert url is None


def test_upload_retry_on_failure(tmp_path):
    """Debe reintentar si falla."""
    img = tmp_path / "retry.png"
    img.write_bytes(b"test")

    with patch.object(subprocess, "run") as mock_run:
        check_result = subprocess.CompletedProcess([], 1, stdout="", stderr="")
        fail_result = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="rate limit exceeded"
        )
        success_result = subprocess.CompletedProcess(
            [], 0,
            stdout="https://github.com/test/repo/blob/main/.issue-assets/1/retry.png?token=abc",
            stderr="",
        )
        # check + 2 fails + 1 success = 4 llamadas
        mock_run.side_effect = [
            check_result, fail_result, fail_result, success_result
        ]

        url = upload_image("test/repo", 1, str(img), max_retries=3)
        assert url is not None
        assert "?raw=true" in url
