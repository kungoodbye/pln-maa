import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ASSETS = ROOT / "assets"
DST_RUNTIME = ROOT / ".create-maa-project" / "runtime" / "mfaa" / "win-x64"

def sync_assets():
    src_res = SRC_ASSETS / "resource"
    dst_res = DST_RUNTIME / "resource"
    
    if src_res.exists():
        shutil.copytree(src_res, dst_res, dirs_exist_ok=True)
        print(f"Synced {src_res} -> {dst_res}")
    
    src_if = SRC_ASSETS / "interface.json"
    dst_if = DST_RUNTIME / "interface.json"
    if src_if.exists():
        shutil.copy2(src_if, dst_if)
        print(f"Synced {src_if} -> {dst_if}")

if __name__ == "__main__":
    sync_assets()
