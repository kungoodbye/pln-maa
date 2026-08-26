import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME = ROOT / ".create-maa-project" / "runtime" / "mfaa" / "win-x64"


def is_mfaavalonia_running() -> bool:
    if os.name != "nt":
        return False

    result = subprocess.run(
        [
            "tasklist.exe",
            "/FI",
            "IMAGENAME eq MFAAvalonia.exe",
            "/FO",
            "CSV",
            "/NH",
        ],
        capture_output=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return b"mfaavalonia.exe" in result.stdout.lower()


def configure_adb_screencap(runtime: Path, instance: str = "default") -> Path:
    if is_mfaavalonia_running():
        raise RuntimeError(
            "MFAAvalonia is running. Close it before changing the instance config."
        )

    config_path = runtime / "config" / "instances" / f"{instance}.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"MFA instance config not found: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    config["AdbControlScreenCapType"] = "Encode"

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=config_path.parent,
            prefix=f".{config_path.name}.",
            suffix=".tmp",
            delete=False,
            newline="\n",
        ) as temp_file:
            json.dump(config, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_path = Path(temp_file.name)
        os.replace(temp_path, config_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    return config_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Force MFAAvalonia to use the compatible ADB PNG screencap mode."
    )
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--instance", default="default")
    args = parser.parse_args()

    configure_adb_screencap(args.runtime.resolve(), args.instance)
    print("Configured AdbControlScreenCapType=Encode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
