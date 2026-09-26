import argparse, subprocess, sys
from pathlib import Path
from license_tool import verify_file, PUBLIC

def main():
    ap=argparse.ArgumentParser(description='Licensed launcher for your own Windows executables.')
    ap.add_argument('exe'); ap.add_argument('--license',required=True); ap.add_argument('--public',default=str(PUBLIC)); ap.add_argument('--app'); ap.add_argument('args',nargs='*')
    a=ap.parse_args(); exe=Path(a.exe).resolve()
    if not exe.is_file() or exe.suffix.lower()!='.exe': raise SystemExit('Target must be an existing .exe file.')
    app=a.app or exe.stem
    ok,msg,payload=verify_file(a.license,a.public,app)
    if not ok: raise SystemExit(f'License refused: {msg}')
    print(f"License OK — {payload['plan']} — {payload['license_id']}")
    try: sys.exit(subprocess.call([str(exe),*a.args],cwd=str(exe.parent)))
    except OSError as e: raise SystemExit(f'Could not launch executable: {e}')
if __name__=='__main__': main()
