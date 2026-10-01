"""Offline package validation and deterministic candidate/release ZIP builds.

Release mode checks live endpoints and binds operator evidence. It never deploys,
accepts legal terms, submits a plugin, or independently certifies that evidence.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from jsonschema import Draft202012Validator

SCHEMAS = {
    "plugin.json": ("plugin.schema.json", "bd0cfd6388f7d5c5c1b4c5edd70df030276345df115274686a0e6d52a92366ed"),
    "mcp.json": ("mcp.schema.json", "2d4b2b9d1c95e75a356152534d2071f18094c1ee9be2eec238c91a1e1f9bd115"),
}
SKILLS = ("query-twin", "update-twin")
TOOLS = {
    "connect_business_account": (["service", "domain", "role_title"], {}, False),
    "ingest_data": (["service", "query", "max_items"], {"max_items": 1000}, False),
    "query_twin": (["question", "max_results", "max_tokens"], {"max_results": 10, "max_tokens": 512}, True),
    "list_twins_status": ([], {}, True),
}
RELEASE_CHECKS = ("verified_publisher", "hosted_legal_adoption", "oauth_end_to_end", "source_revalidation",
                  "deletion_and_retention", "third_party_authorization", "reviewer_access")
MAX_BYTES = 5 * 1024 * 1024


class PackageError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), f"Missing regular file: {path.name}")
    require(path.stat().st_size <= MAX_BYTES, f"JSON file too large: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(isinstance(value, dict), f"Expected JSON object: {path.name}")
    return value


def package_path(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative.startswith("./"), "Package paths must start with ./")
    parts = relative[2:].split("/")
    require(parts and all(part not in {"", ".", ".."} for part in parts), f"Unsafe package path: {relative}")
    require(not any(character in relative for character in ("\\", "\x00", "\r", "\n")), "Unsafe package path characters")
    current = root
    for part in parts:
        current = current / part
        require(not current.is_symlink(), f"Symlinks are not packaged: {relative}")
    require(current.resolve().is_relative_to(root) and current.is_file(), f"Missing or escaping package file: {relative}")
    return current


def https_url(value: str, label: str, *, public: bool = False) -> str:
    require(isinstance(value, str) and len(value) <= 2048, f"{label} must be a URL")
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password,
            f"{label} must use HTTPS without credentials")
    require(not parsed.fragment and not any(character.isspace() for character in value), f"Invalid {label}")
    if public:
        host = parsed.hostname.lower()
        require(not parsed.query and parsed.port in {None, 443}, f"{label} must be public HTTPS without a query")
        require(not any(marker in host for marker in ("replace_with", "localhost", "example.com", "example.org", "example.net")),
                f"{label} contains a placeholder or test host")
        require(not host.endswith((".local", ".localhost", ".test", ".example", ".invalid", ".internal")), f"{label} has a non-public host")
        require("." in host and all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", part) for part in host.split(".")),
                f"{label} requires a real public hostname")
        try:
            addresses = {result[4][0] for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        except socket.gaierror:
            raise PackageError(f"{label} hostname does not resolve") from None
        require(bool(addresses) and all(ipaddress.ip_address(address).is_global for address in addresses),
                f"{label} must resolve only to public addresses")
    return value


def validate_schemas(root: Path, plugin: dict, mcp: dict) -> None:
    for name, value in (("plugin.json", plugin), ("mcp.json", mcp)):
        filename, sha = SCHEMAS[name]
        path = package_path(root, f"./schemas/official/{filename}")
        require(digest(path.read_bytes()) == sha, f"Official schema snapshot changed: {filename}")
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: str(error.path))
        if errors:
            error = errors[0]
            location = ".".join(map(str, error.path)) or "root"
            raise PackageError(f"{name} schema failure at {location}: {error.message}")


def one_line(value: object, label: str, limit: int) -> str:
    require(isinstance(value, str) and 0 < len(value) <= limit and "\n" not in value and "\r" not in value,
            f"{label} must be one line with 1–{limit} characters")
    return value


def validate_icon(path: Path) -> None:
    require(path.stat().st_size <= MAX_BYTES and path.suffix.lower() == ".svg", "This package needs its SVG icon, at most 5 MiB")
    raw = path.read_bytes()
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "SVG external entities are not allowed")
    svg = ET.fromstring(raw)
    require(svg.tag == "{http://www.w3.org/2000/svg}svg", "Invalid SVG root")
    box = svg.attrib.get("viewBox", "").replace(",", " ").split()
    if len(box) == 4:
        _, _, width, height = map(float, box)
    else:
        width, height = float(svg.attrib.get("width", "0")), float(svg.attrib.get("height", "0"))
    require(width == height and width >= 48, "Icon must be square and at least 48 by 48")
    for element in svg.iter():
        require(element.tag.rsplit("}", 1)[-1].lower() not in {"script", "foreignobject"}, "SVG contains executable content")
        for key, value in element.attrib.items():
            require(not key.lower().startswith("on"), "SVG event handlers are not allowed")
            if key.rsplit("}", 1)[-1].lower() == "href":
                require(value.startswith("#"), "SVG must not fetch external assets")


def validate_skills(root: Path) -> dict[str, bytes]:
    directory = root / "skills"
    require(directory.is_dir() and not directory.is_symlink(), "Missing regular skills directory")
    require(sorted(path.name for path in directory.iterdir()) == sorted(SKILLS), "Package needs exactly Query Twin and Update Twin skills")
    result = {}
    for name in SKILLS:
        relative = f"./skills/{name}/SKILL.md"
        path = package_path(root, relative)
        require(sorted(child.name for child in path.parent.iterdir()) == ["SKILL.md"], f"Unexpected files in skill: {name}")
        raw = path.read_bytes()
        require(len(raw) <= MAX_BYTES, f"Skill too large: {name}")
        lines = raw.decode("utf-8").splitlines()
        require(lines and lines[0] == "---" and "---" in lines[1:], f"Missing or unclosed frontmatter: {name}")
        end = lines.index("---", 1)
        header = {}
        # These skills deliberately use only plain, single-line YAML scalars.
        for line in lines[1:end]:
            require(":" in line and not line.startswith(" "), f"Unsupported skill frontmatter: {name}")
            key, value = line.split(":", 1)
            require(key not in header, f"Duplicate skill frontmatter: {name}")
            header[key] = value.strip()
        require(set(header) == {"name", "description"} and header["name"] == name, f"Invalid skill identity: {name}")
        one_line(header["description"], f"{name} description", 1024)
        require(bool("\n".join(lines[end + 1:]).strip()), f"Empty skill instructions: {name}")
        result[relative[2:]] = raw
    return result


def validate_source_tools(root: Path) -> None:
    tree = ast.parse(package_path(root, "./server.py").read_text(encoding="utf-8"))
    functions = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        is_tool = any(isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
                      and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "mcp"
                      and decorator.func.attr == "tool" for decorator in node.decorator_list)
        if is_tool:
            require(node.name not in functions, "Duplicate MCP tool declaration")
            functions[node.name] = node
    require(set(functions) == set(TOOLS), "Source must declare exactly the original four MCP tools")
    for name, (arguments, defaults, _) in TOOLS.items():
        node = functions[name]
        require(not node.args.posonlyargs and not node.args.kwonlyargs and not node.args.vararg and not node.args.kwarg,
                f"MCP tool signature changed: {name}")
        names = [argument.arg for argument in node.args.args]
        require(names == arguments, f"MCP tool arguments changed: {name}")
        actual = dict(zip(names[len(names) - len(node.args.defaults):], map(ast.literal_eval, node.args.defaults)))
        require(actual == defaults, f"MCP tool defaults changed: {name}")


def validate_metadata(root: Path, plugin: dict, mcp: dict) -> dict[str, bytes]:
    require(plugin["name"] == "wisdomtwin", "Stable plugin name must be wisdomtwin")
    require(re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?", plugin.get("version", "")), "Release metadata needs a semantic version")
    one_line(plugin.get("description"), "description", 4000)
    extension = plugin.get("extensions", {}).get("com.openai", {})
    require(set(extension) <= {"interface", "onboardingSkill", "review", "publication"}, "Unexpected OpenAI extension fields")
    interface = extension.get("interface", {})
    allowed = {"displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities", "websiteURL",
               "supportURL", "privacyPolicyURL", "termsOfServiceURL", "defaultPrompt", "brandColor", "brandColorDark",
               "composerIcon", "composerIconDark", "logo", "logoDark"}
    require(isinstance(interface, dict) and set(interface) <= allowed, "Unexpected listing fields; this package has no custom UI")
    for key, maximum in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000), ("developerName", 80), ("category", 120)):
        one_line(interface.get(key), key, maximum)
    author = plugin.get("author", {})
    require(author.get("name") == interface["developerName"], "Author and listing publisher must match")
    one_line(author["name"], "author.name", 120)
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        require(len(interface.get(key, "")) <= 1024, f"{key} exceeds 1024 characters")
        https_url(interface.get(key, ""), key)
    for key in ("homepage", "repository"):
        if key in plugin:
            https_url(plugin[key], key)
    if "url" in author:
        https_url(author["url"], "author.url")
    capabilities = interface.get("capabilities", [])
    require(isinstance(capabilities, list) and len(capabilities) <= 20, "Invalid capabilities")
    for capability in capabilities:
        one_line(capability, "capability", 120)
    prompts = interface.get("defaultPrompt", [])
    prompts = [prompts] if isinstance(prompts, str) else prompts
    require(isinstance(prompts, list) and len(prompts) <= 3 and all(isinstance(prompt, str) for prompt in prompts), "Invalid defaultPrompt")
    require(len(set(prompts)) == len(prompts), "Starter prompts must be unique")
    for prompt in prompts:
        one_line(prompt, "starter prompt", 128)
        require("@" not in prompt, "Starter prompts must omit app mentions")
    for key in ("brandColor", "brandColorDark"):
        if key in interface:
            require(bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", interface[key])), f"Invalid {key}")
    result = validate_skills(root)
    for key in ("composerIcon", "composerIconDark", "logo", "logoDark"):
        path = package_path(root, interface.get(key, ""))
        require(interface[key].startswith("./assets/"), "Visual assets must be inside ./assets/")
        validate_icon(path)
        result[interface[key][2:]] = path.read_bytes()
    require(extension.get("onboardingSkill") == "./skills/query-twin/SKILL.md", "Onboarding must reference packaged Query Twin skill")
    package_path(root, extension["onboardingSkill"])
    review = extension.get("review", {})
    require(set(review) <= {"test_cases", "demo_recording_url", "commerce", "commerce_description"}, "Unexpected review fields")
    cases = review.get("test_cases", {})
    require(set(cases) == {"positive", "negative"}, "Review cases need positive and negative groups")
    for group, count in (("positive", 5), ("negative", 3)):
        require(isinstance(cases[group], list) and len(cases[group]) == count, f"Review requires {count} {group} cases")
        for case in cases[group]:
            require(isinstance(case, dict) and set(case) <= {"description", "prompt", "tools_triggered", "expected_behavior"}, "Unexpected review case fields")
            for key in ("description", "prompt", "expected_behavior"):
                one_line(case.get(key), f"review {key}", 4000)
            if group == "positive":
                require(case.get("tools_triggered") in TOOLS, "Positive case must name an original tool")
    require(review.get("commerce") is False, "This package cannot conduct commerce")
    one_line(review.get("commerce_description"), "commerce_description", 4000)
    listing_text = " ".join([plugin["description"], interface["shortDescription"], interface["longDescription"], review["commerce_description"]])
    require(not re.search(r"(?:\$\s*\d|\bUSD\b|\bcheckout\b|\bfree trial\b|\b20 per month\b)", listing_text, re.I), "Listing must not advertise pricing or transactions")
    require(set(mcp["mcpServers"]) == {"wisdomtwin"}, "Package must declare one server named wisdomtwin")
    entry = mcp["mcpServers"]["wisdomtwin"]
    require(entry.get("type") == "streamable-http" and set(entry) == {"type", "url"}, "Use one remote MCP URL without bundled credentials")
    url = https_url(entry.get("url", ""), "MCP endpoint")
    require(urlsplit(url).path == "/mcp" and not urlsplit(url).query, "MCP endpoint must end exactly in /mcp")
    manifest = load_json(package_path(root, "./manifest.json"))
    require(manifest.get("developer_organization") == interface["developerName"], "Internal manifest publisher must match plugin.json")
    require(manifest.get("privacy_policy_url") == interface["privacyPolicyURL"], "Internal manifest privacy URL must match")
    require([tool.get("name") for tool in manifest.get("tools", [])] == list(TOOLS), "Internal manifest must list original four tools")
    validate_source_tools(root)
    result.update({"plugin.json": json_bytes(plugin), "mcp.json": json_bytes(mcp)})
    expected = {"plugin.json", "mcp.json", "assets/logo.svg", *(f"skills/{name}/SKILL.md" for name in SKILLS)}
    require(set(result) == expected, "Package files differ from explicit allowlist")
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, target):
        raise PackageError("Live checks require exact URLs; resolve redirects in source metadata first")


def public_request(url: str, *, payload: dict | None = None, token: str = "") -> tuple[int, dict, bytes]:
    https_url(url, "Live verification URL", public=True)
    headers = {"Accept": "application/json, text/event-stream" if payload else "text/html, application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    raw = None if payload is None else json_bytes(payload)
    if raw is not None:
        headers["Content-Type"] = "application/json"
    try:
        response = build_opener(NoRedirect()).open(Request(url, data=raw, headers=headers), timeout=15)
    except HTTPError as error:
        response = error
    except URLError:
        raise PackageError("Live HTTPS verification failed; inspect operator network or deployment") from None
    with response:
        body = response.read(MAX_BYTES + 1)
        require(len(body) <= MAX_BYTES, "Live verification response exceeds limit")
        return response.status, dict(response.headers), body


def rpc_object(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text, object_pairs_hook=unique_object)
    messages = [json.loads(line[5:].strip(), object_pairs_hook=unique_object) for line in text.splitlines() if line.startswith("data:")]
    matching = [message for message in messages if message.get("id") == 1]
    require(len(matching) == 1, "Expected one tools/list result")
    return matching[0]


def validate_live_tools(raw: bytes) -> None:
    tools = rpc_object(raw).get("result", {}).get("tools", [])
    require(isinstance(tools, list) and len(tools) == 4 and {tool.get("name") for tool in tools} == set(TOOLS), "Live server must expose exactly original four tools")
    for tool in tools:
        arguments, defaults, read_only = TOOLS[tool["name"]]
        schema = tool.get("inputSchema", {})
        properties = schema.get("properties", {})
        require(set(properties) == set(arguments), f"Live arguments changed: {tool['name']}")
        require(set(schema.get("required", [])) == set(arguments) - set(defaults), f"Live required arguments changed: {tool['name']}")
        for name, value in defaults.items():
            require(properties[name].get("default") == value, f"Live default changed: {tool['name']}.{name}")
        if "service" in properties:
            require(set(properties["service"].get("enum", [])) == {"slack", "gmail", "drive"}, "Live connector enum changed")
        hints = tool.get("annotations", {})
        require(hints.get("readOnlyHint") is read_only and hints.get("destructiveHint") is False and hints.get("openWorldHint") is False,
                f"Live annotations changed: {tool['name']}")
        schemes = tool.get("_meta", {}).get("securitySchemes", tool.get("securitySchemes", []))
        require(any(scheme.get("type") == "oauth2" and "twin:read" in scheme.get("scopes", []) for scheme in schemes),
                f"Live tool must declare role-authenticated access: {tool['name']}")


def validate_release(root: Path, plugin: dict, mcp: dict, files: dict[str, bytes]) -> None:
    interface = plugin["extensions"]["com.openai"]["interface"]
    mcp_url = mcp["mcpServers"]["wisdomtwin"]["url"]
    https_url(mcp_url, "Production MCP endpoint", public=True)
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        https_url(interface[key], key, public=True)
    filename = os.environ.get("PACKAGE_RELEASE_EVIDENCE", "")
    require(bool(filename), "Production build needs PACKAGE_RELEASE_EVIDENCE with real operator records; use --candidate for offline review")
    evidence_path = Path(filename).resolve()
    evidence = load_json(evidence_path)
    for key, expected in (("mcp_url", mcp_url), ("publisher", interface["developerName"]),
                          ("privacy_url", interface["privacyPolicyURL"]), ("terms_url", interface["termsOfServiceURL"])):
        require(evidence.get(key) == expected, f"Release evidence does not match {key}")
    require(evidence.get("package_files_sha256") == {name: digest(raw) for name, raw in sorted(files.items())}, "Evidence must bind all staged package file hashes")
    checks = evidence.get("checks", {})
    for name in RELEASE_CHECKS:
        record = checks.get(name, {})
        require(record.get("result") == "passed" and isinstance(record.get("path"), str), f"Missing successful operator evidence: {name}")
        proof = (evidence_path.parent / record["path"]).resolve()
        require(proof != evidence_path and proof.is_file() and proof.stat().st_size > 0, f"Missing supporting record: {name}")
        require(digest(proof.read_bytes()) == record.get("sha256"), f"Supporting record hash mismatch: {name}")
    demo = plugin["extensions"]["com.openai"]["review"].get("demo_recording_url", "")
    https_url(demo, "Reviewer demo URL", public=True)
    status, _, raw = public_request(demo)
    require(status == 200 and bool(raw), "Reviewer demo URL must be accessible")
    pages = evidence.get("published_pages_sha256", {})
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        status, _, raw = public_request(interface[key])
        require(status == 200 and bool(raw), f"Public {key} is unavailable")
        require(pages.get(key) == digest(raw), f"Public {key} differs from reviewed response hash")
        if key in {"privacyPolicyURL", "termsOfServiceURL"}:
            require(b"draft" not in raw.lower() and b"not adopted" not in raw.lower(), f"Public {key} still identifies itself as a draft")
    origin = mcp_url.removesuffix("/mcp")
    status, _, raw = public_request(origin + "/health")
    require(status == 200 and json.loads(raw).get("status") == "ok", "Live service health check failed")
    rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    status, headers, _ = public_request(mcp_url, payload=rpc)
    challenge = next((value for key, value in headers.items() if key.lower() == "www-authenticate"), "")
    require(status == 401 and "resource_metadata=" in challenge, "MCP must reject anonymous access with a resource metadata challenge")
    match = re.search(r'resource_metadata="([^"]+)"', challenge)
    require(match is not None, "Auth challenge must identify protected resource metadata")
    status, _, raw = public_request(match[1])
    require(status == 200, "Protected resource metadata unavailable")
    protected = json.loads(raw)
    require(protected.get("resource") == mcp_url and protected.get("authorization_servers") == [origin], "MCP resource or issuer mismatch")
    status, _, raw = public_request(origin + "/.well-known/oauth-authorization-server")
    require(status == 200, "OAuth discovery unavailable")
    oauth = json.loads(raw)
    require(oauth.get("issuer") == origin and "S256" in oauth.get("code_challenge_methods_supported", [])
            and "authorization_code" in oauth.get("grant_types_supported", []) and "code" in oauth.get("response_types_supported", [])
            and "none" in oauth.get("token_endpoint_auth_methods_supported", []) and "twin:read" in oauth.get("scopes_supported", []),
            "OAuth discovery does not declare the required authorization flow")
    for key in ("authorization_endpoint", "token_endpoint"):
        url = https_url(oauth.get(key, ""), key, public=True)
        require(urlsplit(url).netloc == urlsplit(origin).netloc, f"Unexpected OAuth {key} host")
    token = os.environ.get("PACKAGE_MCP_ACCESS_TOKEN", "")
    require(bool(token), "Set PACKAGE_MCP_ACCESS_TOKEN for an authenticated read-only scan; never store it in evidence")
    status, _, raw = public_request(mcp_url, payload=rpc, token=token)
    require(status == 200, "Authenticated MCP tool scan failed")
    validate_live_tools(raw)


def write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), f"Refusing to replace a symlink: {path.name}")
    fd, temporary = tempfile.mkstemp(prefix=".wisdomtwin-package-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def build_zip(files: dict[str, bytes], destination: Path, *, candidate: bool) -> None:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_STORED) as archive:
        for name, raw in sorted(files.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_STORED
            archive.writestr(info, raw)
    raw = buffer.getvalue()
    with ZipFile(io.BytesIO(raw)) as archive:
        require(archive.testzip() is None and archive.namelist() == sorted(files), "Built archive integrity check failed")
    write_atomic(destination, raw)
    write_atomic(destination.with_suffix(destination.suffix + ".sha256"), f"{digest(raw)}  {destination.name}\n".encode())
    inventory = {"artifact": destination.name, "sha256": digest(raw), "candidate_not_for_submission": candidate,
                 "members_sha256": {name: digest(body) for name, body in sorted(files.items())},
                 "schema_snapshots_sha256": {name: sha for name, (_, sha) in SCHEMAS.items()},
                 "validation": "offline schemas, listing fields, paths, icon, two skills and four source tool signatures" if candidate
                 else "offline checks, live HTTPS/auth tool scan and matching operator evidence", "submission_status": "not submitted"}
    write_atomic(destination.with_suffix(destination.suffix + ".contents.json"), json_bytes(inventory))
    print(f"Wrote {destination}")
    print(f"SHA-256 {digest(raw)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Offline checks only; do not create a ZIP")
    mode.add_argument("--candidate", action="store_true", help="Build an offline candidate that is NOT FOR SUBMISSION")
    mode.add_argument("--release", action="store_true", help="Check live deployment and evidence then build a production ZIP (default)")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent, help=argparse.SUPPRESS)
    parser.add_argument("--output-dir", type=Path, help="Artifact directory; defaults to dist under package root")
    options = parser.parse_args()
    root = options.root.resolve()
    try:
        plugin = load_json(package_path(root, "./plugin.json"))
        mcp = load_json(package_path(root, "./mcp.json"))
        validate_schemas(root, plugin, mcp)
        files = validate_metadata(root, plugin, mcp)
        print("Offline package checks passed: official schemas, paths, icon, two skills and four tool signatures.")
        if options.check:
            print("Candidate check only. Deployment, publisher/legal adoption and provider authorization remain separate release requirements.")
            return 0
        if not options.candidate:
            if os.environ.get("MCP_SERVER_URL"):
                mcp["mcpServers"]["wisdomtwin"]["url"] = os.environ["MCP_SERVER_URL"]
                validate_schemas(root, plugin, mcp)
                files = validate_metadata(root, plugin, mcp)
            validate_release(root, plugin, mcp, files)
        output = options.output_dir or root / "dist"
        name = "wisdomtwin-candidate-NOT-FOR-SUBMISSION.zip" if options.candidate else "wisdomtwin-plugin.zip"
        build_zip(files, output / name, candidate=options.candidate)
        if options.candidate:
            print("NOT FOR SUBMISSION: source URLs, including placeholders, are preserved. Candidate mode performs no network calls.")
        return 0
    except (PackageError, ValueError, KeyError, TypeError, OSError, ET.ParseError) as error:
        print(f"Package blocked: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
