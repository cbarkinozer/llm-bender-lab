"""New reference shared snapshot boundary; checkout ownership transfers to snapshot."""
from pathlib import Path
import shutil
from repo_context.core import parse_github_url
from gitignore_parser import parse_gitignore

def snapshot(url, *, extensions, line_limit, token=None, clone):
    if not url.startswith('https://github.com/'): raise ValueError('HTTPS GitHub URL required')
    if line_limit<0: raise ValueError('Nonnegative line limit required')
    base,branch,subfolder=parse_github_url(url)
    root=Path(clone(base,branch=branch,token=token))
    try:
        selected=(root/(subfolder or '')).resolve()
        if not selected.is_relative_to(root.resolve()): raise ValueError('Unsafe subfolder')
        ignore=parse_gitignore(root/'.gitignore') if (root/'.gitignore').exists() else lambda p:False
        parts=[f'# Repository {base}\nBranch: {branch or "default"}']
        for file in sorted(selected.rglob('*')):
            rel=file.relative_to(root)
            if file.is_symlink() or not file.is_file() or file.name.startswith('.env') or any(
                part in ('.git','node_modules','.venv','__pycache__') for part in rel.parts) or ignore(file): continue
            if file.suffix not in extensions: continue
            try: text=file.read_text(encoding='utf-8')
            except UnicodeError: continue
            lines=text.splitlines(keepends=True)
            truncated=line_limit>0 and len(lines)>line_limit
            parts.append(str(rel)+'\n'+''.join(lines[:line_limit] if line_limit else lines)+
                         ('\n[truncated]' if truncated else ''))
        result='\n\n'.join(parts)
        return result.replace(token,'[redacted]') if token else result
    finally: shutil.rmtree(root)

def cli_snapshot(url, *, operation): return operation(url)
def ui_snapshot(url, *, operation): return operation(url)
