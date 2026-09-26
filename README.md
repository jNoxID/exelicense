# EXE License Test Kit

A small Ed25519 licensing/launcher demo for Windows executables you own.

## 1. Install

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## 2. Generate signing keys

```powershell
py license_tool.py init
```

**Never distribute `keys/private.pem`.** The public key is safe to distribute.

## 3. Get the test computer ID

```powershell
py license_tool.py device-id
```

Copy the returned hash.

## 4. Create a license

For `MyApp.exe`:

```powershell
py license_tool.py create --plan pro --days 365 --device YOUR_DEVICE_ID --app MyApp
```

The JSON license is written to `licenses/`.

For an offline test license accepted on any computer, use `--device "*"` (testing only).

## 5. Verify

```powershell
py license_tool.py verify licenses\LIC-XXXXXXXXXX.json --app MyApp
```

## 6. Launch your EXE

```powershell
py launcher.py "C:\Path\MyApp.exe" --license "licenses\LIC-XXXXXXXXXX.json"
```

## Security note

This is a launcher-based demonstration. It does **not** modify or patch the target executable. Therefore, if the original EXE is distributed alongside the launcher, it can still be started directly. For production licensing, integrate license verification into software you control or keep indispensable licensed functionality server-side.
