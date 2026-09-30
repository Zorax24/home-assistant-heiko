"""Local release gate for translations, metadata, privacy and archive contents."""
from __future__ import annotations
import argparse
import ast
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/heiko_w600"
EXCLUDED = {".git", ".venv", "dist", "__pycache__", ".pytest_cache", ".ruff_cache"}

def translation_keys(value, prefix=()):
    if isinstance(value, dict):
        return {path for key, child in value.items() for path in translation_keys(child, (*prefix,key))}
    return {prefix}

def check_bytes(name, data):
    if name.endswith(".png"):
        # The generated icon must not carry EXIF or textual metadata.
        assert all(chunk not in data for chunk in (b"eXIf",b"tEXt",b"iTXt",b"zTXt")), name
        return
    text = data.decode("utf-8-sig")
    # Print names only, never matched sensitive values.
    forbidden = [r"(?i)(?<![a-z])[A-Z]:[\\/]", r"(?i)/(?:home|Users)/[a-z][^\s/]*", r"(?i)BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY", r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}"]
    assert not any(re.search(pattern,text) for pattern in forbidden), "Private-data pattern in " + name
    allowed = [ipaddress.ip_network(net) for net in ("127.0.0.0/8","192.0.2.0/24","198.51.100.0/24","203.0.113.0/24")]
    for candidate in re.findall(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])",text):
        try: address=ipaddress.ip_address(candidate)
        except ValueError: continue
        assert candidate=="0.0.0.0" or any(address in network for network in allowed) or not address.is_private, "Private address in " + name
    if name.endswith(".py"): ast.parse(text,filename=name)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path)
    args=parser.parse_args()
    manifest=json.loads((COMPONENT/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"]=="heiko_w600" and manifest["config_flow"] and manifest["single_config_entry"]
    assert {"documentation","issue_tracker","codeowners","version","iot_class"} <= manifest.keys()
    import tomllib
    assert tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]==manifest["version"]
    catalog=json.loads((COMPONENT/"parameters.json").read_text(encoding="utf-8"))
    assert len(catalog)==128 and len({p['settingIndex'] for p in catalog})==128
    assert sum(p['writable'] for p in catalog)==125
    en=json.loads((COMPONENT/"translations/en.json").read_text(encoding="utf-8"))
    de=json.loads((COMPONENT/"translations/de.json").read_text(encoding="utf-8"))
    assert translation_keys(en)==translation_keys(de)
    for p in catalog:
        platform='sensor' if not p['writable'] else 'switch' if p['type']=='boolean' else 'select' if p['pageControl']=='select' else 'number'
        key=f"setting_{p['settingIndex']:03d}"
        for language in (en,de):
            entity=language['entity'][platform][key]
            assert entity['name'].strip()
            if platform=='select': assert set(entity['state'])=={f'option_{k}' for k in p['states']}
    files=[p for p in ROOT.rglob('*') if p.is_file() and not any(part in EXCLUDED for part in p.relative_to(ROOT).parts)]
    for path in files: check_bytes(path.relative_to(ROOT).as_posix(),path.read_bytes())
    # Relative links must exist; external links are checked separately at publication.
    for path in ROOT.rglob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                assert (path.parent/link.split('#')[0]).exists(), (path.name,link)
    if args.archive:
        with zipfile.ZipFile(args.archive) as archive:
            assert archive.testzip() is None
            expected={p.relative_to(ROOT).as_posix():p.read_bytes() for p in COMPONENT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
            assert set(archive.namelist())==set(expected)
            for name,data in expected.items():
                assert archive.read(name)==data
                check_bytes(name,archive.read(name))
        print('Archive content verified:',len(expected),'files; SHA256',hashlib.sha256(args.archive.read_bytes()).hexdigest())
    print('Source/privacy/translation/metadata gates passed:',len(files),'files')

if __name__=='__main__': main()
