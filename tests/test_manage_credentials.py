import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT_PATH = Path("plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py")


@pytest.fixture()
def manage_credentials_module(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("manage_credentials", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    chutes_dir = tmp_path / ".chutes"
    monkeypatch.setattr(module, "CHUTES_DIR", chutes_dir)
    monkeypatch.setattr(module, "CONFIG_FILE", chutes_dir / "config")
    monkeypatch.setattr(module, "ENCRYPTED_FILE", chutes_dir / ".keychain")
    monkeypatch.setattr(module, "GITIGNORE_FILE", chutes_dir / ".gitignore")

    return module


def test_ensure_chutes_dir_creates_secure_directory_and_gitignore(manage_credentials_module):
    module = manage_credentials_module

    module.ensure_chutes_dir()

    assert module.CHUTES_DIR.exists()
    assert oct(module.CHUTES_DIR.stat().st_mode & 0o777) == "0o700"
    assert module.GITIGNORE_FILE.exists()
    assert module.GITIGNORE_FILE.read_text() == "*\n"


def test_cmd_get_prefers_environment_override_for_secret_field(manage_credentials_module, monkeypatch, capsys):
    module = manage_credentials_module
    monkeypatch.setenv("CHUTES_API_KEY", "cpk_env_override")

    module.cmd_get(SimpleNamespace(profile=None, field="api_key"))

    captured = capsys.readouterr()
    assert captured.out.strip() == "cpk_env_override"
    assert captured.err == ""


def test_cmd_check_reports_gitignore_status(manage_credentials_module, capsys):
    module = manage_credentials_module
    module.ensure_chutes_dir()

    module.cmd_check(SimpleNamespace())

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["gitignore_exists"] is True
    assert payload["gitignore_secure"] is True


def test_cmd_set_profile_persists_metadata_and_secrets(manage_credentials_module, monkeypatch, capsys):
    module = manage_credentials_module
    stored = {}

    monkeypatch.setattr(module, "detect_backend", lambda: "encrypted_file")
    monkeypatch.setattr(module, "read_secrets", lambda backend, profile: stored.get(profile))

    def fake_write_secrets(backend, profile, secrets):
        stored[profile] = dict(secrets)

    monkeypatch.setattr(module, "write_secrets", fake_write_secrets)

    module.cmd_set_profile(
        SimpleNamespace(
            profile="default",
            username="alice",
            user_id="1234",
            api_key="cpk_secret",
            fingerprint=None,
            client_id=None,
            client_secret=None,
        )
    )

    captured = capsys.readouterr()
    cp = module.load_config()
    assert stored["default"] == {"api_key": "cpk_secret"}
    assert cp.get("default", "username") == "alice"
    assert cp.get("default", "user_id") == "1234"
    assert cp.get("default", "backend") == "encrypted_file"
    assert "Profile 'default' saved" in captured.err


def test_cmd_set_profile_merges_existing_secret_fields(manage_credentials_module, monkeypatch, capsys):
    module = manage_credentials_module
    stored = {"default": {"fingerprint": "fp_existing"}}

    monkeypatch.setattr(module, "detect_backend", lambda: "encrypted_file")
    monkeypatch.setattr(module, "read_secrets", lambda backend, profile: stored.get(profile))

    def fake_write_secrets(backend, profile, secrets):
        stored[profile] = dict(secrets)

    monkeypatch.setattr(module, "write_secrets", fake_write_secrets)

    module.cmd_set_profile(
        SimpleNamespace(
            profile="default",
            username=None,
            user_id=None,
            api_key="cpk_secret",
            fingerprint=None,
            client_id=None,
            client_secret=None,
        )
    )

    capsys.readouterr()
    assert stored["default"] == {
        "fingerprint": "fp_existing",
        "api_key": "cpk_secret",
    }


def test_cmd_set_updates_metadata_and_secret_fields(manage_credentials_module, monkeypatch, capsys):
    module = manage_credentials_module
    stored = {}

    monkeypatch.setattr(module, "detect_backend", lambda: "encrypted_file")
    monkeypatch.setattr(module, "read_secrets", lambda backend, profile: stored.get(profile))
    monkeypatch.setattr(module, "write_secrets", lambda backend, profile, secrets: stored.__setitem__(profile, dict(secrets)))

    module.cmd_set(SimpleNamespace(profile="default", field="username", value="alice"))
    module.cmd_set(SimpleNamespace(profile="default", field="api_key", value="cpk_secret"))

    captured = capsys.readouterr()
    cp = module.load_config()
    assert cp.get("default", "username") == "alice"
    assert cp.get("default", "backend") == "encrypted_file"
    assert stored["default"] == {"api_key": "cpk_secret"}
    assert "Updated 'api_key' in profile 'default'" in captured.err


def test_cmd_delete_removes_profile_and_secrets(manage_credentials_module, monkeypatch, capsys):
    module = manage_credentials_module
    deleted = []

    monkeypatch.setattr(module, "detect_backend", lambda: "encrypted_file")
    monkeypatch.setattr(module, "read_secrets", lambda backend, profile: None)
    monkeypatch.setattr(module, "write_secrets", lambda backend, profile, secrets: None)
    monkeypatch.setattr(module, "delete_secrets", lambda backend, profile: deleted.append((backend, profile)))

    module.cmd_set_profile(
        SimpleNamespace(
            profile="default",
            username="alice",
            user_id="1234",
            api_key="cpk_secret",
            fingerprint=None,
            client_id=None,
            client_secret=None,
        )
    )
    capsys.readouterr()

    module.cmd_delete(SimpleNamespace(profile="default"))

    captured = capsys.readouterr()
    cp = module.load_config()
    assert cp.has_section("default") is False
    assert deleted == [("encrypted_file", "default")]
    assert "Profile 'default' deleted." in captured.err


def test_cmd_check_reports_encrypted_store_status(manage_credentials_module, capsys):
    module = manage_credentials_module
    module.ensure_chutes_dir()
    module.ENCRYPTED_FILE.write_text("placeholder")
    module.ENCRYPTED_FILE.chmod(0o600)

    module.cmd_check(SimpleNamespace())

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["encrypted_file_exists"] is True
    assert payload["encrypted_file_secure"] is True
