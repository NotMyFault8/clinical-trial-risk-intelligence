"""Pin the installed dependency closure; omit unrelated installed packages."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import tomllib

root=Path(__file__).resolve().parents[1]
project=tomllib.loads((root/'pyproject.toml').read_text())['project']
def closure(requirements):
    found={};pending=list(requirements)
    while pending:
        req=Requirement(pending.pop())
        if req.marker and not req.marker.evaluate({'extra':''}):continue
        key=canonicalize_name(req.name)
        if key in found:continue
        d=distribution(req.name);found[key]=d.version
        pending.extend(d.requires or [])
    return '\n'.join(f'{k}=={v}' for k,v in sorted(found.items()))+'\n'
core=project['dependencies']+project['optional-dependencies']['test']
(root/'requirements-core.lock').write_text(closure(core))
(root/'requirements-macos.lock').write_text(closure(core+project['optional-dependencies']['text']+project['optional-dependencies']['local-llm']))
