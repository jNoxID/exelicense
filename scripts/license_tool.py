import argparse, base64, hashlib, importlib, json, os, platform, secrets, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    serialization = importlib.import_module('cryptography.hazmat.primitives').serialization
    Ed25519PrivateKey = importlib.import_module(
        'cryptography.hazmat.primitives.asymmetric.ed25519'
    ).Ed25519PrivateKey
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: install it with 'python -m pip install cryptography'"
    ) from exc

ROOT = Path(__file__).resolve().parent
KEYS = ROOT / 'keys'; LICENSES = ROOT / 'licenses'
PRIVATE = KEYS / 'private.pem'; PUBLIC = KEYS / 'public.pem'

def utcnow(): return datetime.now(timezone.utc)
def iso(dt): return dt.replace(microsecond=0).isoformat().replace('+00:00','Z')
def canonical(d): return json.dumps(d, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def device_id():
    raw = '|'.join([platform.system(), platform.release(), platform.machine(), platform.node(), str(uuid.getnode())])
    return hashlib.sha256(raw.encode()).hexdigest()

def init_keys():
    KEYS.mkdir(exist_ok=True); LICENSES.mkdir(exist_ok=True)
    if PRIVATE.exists() or PUBLIC.exists(): raise SystemExit('Keys already exist; refusing to overwrite.')
    private = Ed25519PrivateKey.generate(); public = private.public_key()
    PRIVATE.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    PUBLIC.write_bytes(public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    print(f'Created {PRIVATE}\nCreated {PUBLIC}\nKeep private.pem secret.')

def load_private():
    if not PRIVATE.exists(): raise SystemExit('Run: python license_tool.py init')
    return serialization.load_pem_private_key(PRIVATE.read_bytes(), password=None)

def load_public(path=PUBLIC):
    if not Path(path).exists(): raise SystemExit(f'Public key not found: {path}')
    return serialization.load_pem_public_key(Path(path).read_bytes())

def create(args):
    LICENSES.mkdir(exist_ok=True)
    now=utcnow(); payload={
      'version':1,'license_id':'LIC-'+secrets.token_hex(5).upper(),'application':args.app,
      'plan':args.plan,'issued_at':iso(now),'expires_at':iso(now+timedelta(days=args.days)),
      'device_id':args.device,'features':args.feature or ([] if args.plan=='free' else ['premium'])}
    sig=base64.b64encode(load_private().sign(canonical(payload))).decode()
    doc={'payload':payload,'signature':sig}
    out=Path(args.output) if args.output else LICENSES/f"{payload['license_id']}.json"
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf-8')
    print(out); print(json.dumps(payload,indent=2,ensure_ascii=False))

def verify_file(path, public=PUBLIC, expected_app=None):
    try:
        doc=json.loads(Path(path).read_text(encoding='utf-8')); payload=doc['payload']; sig=base64.b64decode(doc['signature'],validate=True)
        load_public(public).verify(sig, canonical(payload))
        exp=datetime.fromisoformat(payload['expires_at'].replace('Z','+00:00'))
        if utcnow() >= exp: return False,'expired',payload
        if payload.get('device_id') not in ('*',device_id()): return False,'wrong device',payload
        if expected_app and payload.get('application') not in ('*',expected_app): return False,'wrong application',payload
        return True,'valid',payload
    except Exception as e: return False,f'invalid license: {e}',None

def cmd_verify(args):
    ok,msg,p=verify_file(args.license,args.public,args.app); print(('VALID: ' if ok else 'INVALID: ')+msg)
    if p: print(json.dumps(p,indent=2,ensure_ascii=False))
    raise SystemExit(0 if ok else 1)

def main():
    ap=argparse.ArgumentParser(description='Ed25519 license tool for software you own.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init')
    sub.add_parser('device-id')
    c=sub.add_parser('create'); c.add_argument('--plan',choices=['free','pro'],default='pro'); c.add_argument('--days',type=int,default=365); c.add_argument('--device',required=True,help='Device ID or *'); c.add_argument('--app',default='*'); c.add_argument('--feature',action='append'); c.add_argument('--output')
    v=sub.add_parser('verify'); v.add_argument('license'); v.add_argument('--public',default=str(PUBLIC)); v.add_argument('--app')
    a=ap.parse_args()
    if a.cmd=='init': init_keys()
    elif a.cmd=='device-id': print(device_id())
    elif a.cmd=='create': create(a)
    elif a.cmd=='verify': cmd_verify(a)
if __name__=='__main__': main()
