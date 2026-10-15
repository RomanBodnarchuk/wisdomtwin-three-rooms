"""Offline package boundary tests using synthetic mutations and actual ZIPs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import socket
import sys
from zipfile import ZIP_STORED, ZipFile

import pytest

import package_validator as validator


ROOT = Path(__file__).resolve().parents[1]
ZIP_MEMBERS = {
    "plugin.json",
    "mcp.json",
    "assets/logo.svg",
    "skills/query-twin/SKILL.md",
    "skills/update-twin/SKILL.md",
}


@pytest.fixture(autouse=True)
def no_package_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Package tests must not perform outbound calls")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(validator, "build_opener", forbidden)


@pytest.fixture
def package_tree(tmp_path):
    root = tmp_path / "package"
    root.mkdir()
    for filename in ("plugin.json", "mcp.json", "manifest.json", "server.py"):
        shutil.copyfile(ROOT / filename, root / filename)
    for directory in ("assets", "skills", "schemas"):
        shutil.copytree(ROOT / directory, root / directory)
    return root


@pytest.fixture
def documents(package_tree):
    return validator.load_json(package_tree / "plugin.json"), validator.load_json(package_tree / "mcp.json")


def validated_files(root, plugin, mcp):
    validator.validate_schemas(root, plugin, mcp)
    return validator.validate_metadata(root, plugin, mcp)


def test_rejects_unknown_portable_root_key(package_tree, documents):
    plugin, mcp = documents
    plugin["unexpected"] = "synthetic mutation"
    with pytest.raises(validator.PackageError, match="plugin.json schema failure"):
        validator.validate_schemas(package_tree, plugin, mcp)


def test_rejects_unknown_mcp_server_key(package_tree, documents):
    plugin, mcp = documents
    mcp["mcpServers"]["wisdomtwin"]["unexpected"] = "synthetic mutation"
    with pytest.raises(validator.PackageError, match="mcp.json schema failure"):
        validator.validate_schemas(package_tree, plugin, mcp)


def test_rejects_asset_path_traversal(package_tree, documents):
    plugin, mcp = documents
    plugin["extensions"]["com.openai"]["interface"]["logo"] = "./../outside.svg"
    with pytest.raises(validator.PackageError, match="Unsafe package path"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_publisher_mismatch(package_tree, documents):
    plugin, mcp = documents
    plugin["author"]["name"] = "Synthetic wrong publisher"
    with pytest.raises(validator.PackageError, match="publisher must match"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_bundled_mcp_credential_headers(package_tree, documents):
    plugin, mcp = documents
    mcp["mcpServers"]["wisdomtwin"]["headers"] = {"Authorization": "Bearer SYNTHETIC_ONLY"}
    # The portable schema permits headers; this package deliberately excludes them.
    validator.validate_schemas(package_tree, plugin, mcp)
    with pytest.raises(validator.PackageError, match="without bundled credentials"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_pricing_promotion(package_tree, documents):
    plugin, mcp = documents
    plugin["description"] = "Subscribe for USD 20"
    with pytest.raises(validator.PackageError, match="advertise pricing"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_missing_reviewer_scenario(package_tree, documents):
    plugin, mcp = documents
    plugin["extensions"]["com.openai"]["review"]["test_cases"]["positive"].pop()
    with pytest.raises(validator.PackageError, match="5 positive cases"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_malformed_skill_frontmatter(package_tree, documents):
    plugin, mcp = documents
    (package_tree / "skills" / "update-twin" / "SKILL.md").write_text("# Synthetic missing frontmatter\n")
    with pytest.raises(validator.PackageError, match="frontmatter"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_extra_skill(package_tree, documents):
    plugin, mcp = documents
    (package_tree / "skills" / "unexpected").mkdir()
    with pytest.raises(validator.PackageError, match="exactly Query Twin and Update Twin"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_symlink_asset(package_tree, documents, tmp_path):
    plugin, mcp = documents
    asset = package_tree / "assets" / "logo.svg"
    outside = tmp_path / "outside-logo.svg"
    outside.write_bytes(asset.read_bytes())
    asset.unlink()
    asset.symlink_to(outside)
    with pytest.raises(validator.PackageError, match="Symlinks are not packaged"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_schema_snapshot_tampering(package_tree, documents):
    plugin, mcp = documents
    snapshot = package_tree / "schemas" / "official" / "plugin.schema.json"
    snapshot.write_bytes(snapshot.read_bytes() + b" ")
    with pytest.raises(validator.PackageError, match="schema snapshot changed"):
        validator.validate_schemas(package_tree, plugin, mcp)


def test_rejects_fifth_mcp_tool(package_tree, documents):
    plugin, mcp = documents
    source = package_tree / "server.py"
    source.write_text(source.read_text() + "\n@mcp.tool()\ndef synthetic_extra_tool() -> dict:\n    return {}\n")
    with pytest.raises(validator.PackageError, match="exactly the original four MCP tools"):
        validator.validate_metadata(package_tree, plugin, mcp)


def test_rejects_duplicate_json_keys(package_tree):
    source = package_tree / "synthetic-duplicate.json"
    source.write_text('{"name":"first","name":"second"}')
    with pytest.raises(validator.PackageError, match="Duplicate JSON key"):
        validator.load_json(source)


def test_excludes_unrelated_sensitive_and_fixture_files(package_tree, documents, tmp_path):
    plugin, mcp = documents
    marker = b"SYNTHETIC_SECRET_MARKER_NEVER_REAL"
    (package_tree / ".env").write_bytes(marker)
    (package_tree / "fixtures").mkdir()
    (package_tree / "fixtures" / "synthetic-secret.json").write_bytes(marker)
    (package_tree / "reviewer-credentials.txt").write_bytes(marker)
    files = validated_files(package_tree, plugin, mcp)
    destination = tmp_path / "excluded.zip"
    validator.build_zip(files, destination, candidate=True)
    with ZipFile(destination) as archive:
        assert set(archive.namelist()) == ZIP_MEMBERS
        assert all(marker not in archive.read(name) for name in archive.namelist())
    assert marker not in destination.read_bytes()


def test_offline_candidate_is_deterministic_with_verified_layout(package_tree, documents, tmp_path):
    plugin, mcp = documents
    original_mcp = copy.deepcopy(mcp)
    files = validated_files(package_tree, plugin, mcp)
    destinations = [tmp_path / "first" / "candidate.zip", tmp_path / "second" / "candidate.zip"]
    for destination in destinations:
        validator.build_zip(files, destination, candidate=True)
    assert destinations[0].read_bytes() == destinations[1].read_bytes()
    assert mcp == original_mcp
    expected_digest = validator.digest(destinations[0].read_bytes())
    for destination in destinations:
        assert destination.with_suffix(".zip.sha256").read_text() == f"{expected_digest}  candidate.zip\n"
        inventory = json.loads(destination.with_suffix(".zip.contents.json").read_text())
        assert inventory["sha256"] == expected_digest
        assert inventory["candidate_not_for_submission"] is True
        assert inventory["submission_status"] == "not submitted"
        with ZipFile(destination) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == sorted(ZIP_MEMBERS)
            assert inventory["members_sha256"] == {name: validator.digest(archive.read(name)) for name in archive.namelist()}
            assert json.loads(archive.read("mcp.json")) == original_mcp
            assert b"REPLACE_WITH_RAILWAY_PUBLIC_URL" in archive.read("mcp.json")
            for entry in archive.infolist():
                assert entry.date_time == (1980, 1, 1, 0, 0, 0)
                assert entry.external_attr >> 16 == 0o100644
                assert entry.compress_type == ZIP_STORED


def test_production_refuses_placeholder_before_network_or_output(package_tree, tmp_path, monkeypatch, capsys):
    destination = tmp_path / "release-output"
    monkeypatch.delenv("MCP_SERVER_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["package_validator.py", "--release", "--root", str(package_tree),
                                     "--output-dir", str(destination)])
    assert validator.main() == 1
    assert "placeholder or test host" in capsys.readouterr().err
    assert not destination.exists()
