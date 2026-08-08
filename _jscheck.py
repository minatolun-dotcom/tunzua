import re, subprocess, sys

html = open('index.html', encoding='utf-8').read()
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, flags=re.S)
print(f'extracted {len(scripts)} inline scripts')
ok = True
for i, s in enumerate(scripts):
    path = f'/tmp/vjs_{i}.js'
    open(path, 'w').write(s)
    r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
    status = 'ok' if r.returncode == 0 else 'FAIL'
    if r.returncode != 0:
        ok = False
    print(f'  script {i}: {status}' + (f' :: {r.stderr.strip()[:200]}' if r.returncode else ''))
sys.exit(0 if ok else 1)
