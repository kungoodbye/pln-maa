import argparse
import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SRC = ROOT / ".create-maa-project" / "runtime" / "mfaa" / "win-x64"
DIST_DIR = ROOT / "dist"


def kill_mfa_if_running():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "MFAAvalonia.exe"], capture_output=True, check=False)
        time.sleep(0.5)
    except Exception:
        pass


def safe_rmtree(path: Path):
    if not path.exists():
        return
    for item in path.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        except Exception:
            pass


def build_package(mode: str = "arena", version: str = "v0.1.0"):
    print(f"=== 开始打包 《飘流幻境新世界自动化》 [模式: {mode}, 版本: {version}] ===")
    
    if not RUNTIME_SRC.is_dir():
        raise FileNotFoundError(f"未找到运行时基础目录: {RUNTIME_SRC}")

    kill_mfa_if_running()
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    pkg_name = f"pln-auto-{mode}-{version}-win-x64"
    build_dir = DIST_DIR / pkg_name
    
    safe_rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] 复制基础运行环境至: {build_dir}")
    # 1. 复制核心文件
    core_files = [
        "MFAAvalonia.exe",
        "MFAAvalonia.dll",
        "MFAAvalonia.deps.json",
        "MFAAvalonia.runtimeconfig.json",
        "appsettings.json",
        "libloader.dll",
        "DependencySetup_依赖库安装_win.bat"
    ]
    for f in core_files:
        src_file = RUNTIME_SRC / f
        if src_file.is_file():
            shutil.copy2(src_file, build_dir / f)

    # 2. 复制核心依赖目录
    core_dirs = ["runtimes", "libs", "plugins", "agent"]
    for d in core_dirs:
        src_d = RUNTIME_SRC / d
        if src_d.is_dir():
            shutil.copytree(src_d, build_dir / d, dirs_exist_ok=True)

    print("[2/5] 注入最新开发资源与任务配置...")
    # 3. 复制最新 resource
    resource_src = ROOT / "assets" / "resource"
    shutil.copytree(resource_src, build_dir / "resource", dirs_exist_ok=True)

    # 4. 生成 interface.json
    with open(ROOT / "assets" / "interface.json", "r", encoding="utf-8") as f:
        interface_data = json.load(f)

    if mode == "arena":
        # 仅保留玩家对战任务
        interface_data["task"] = [
            t for t in interface_data.get("task", []) if t.get("name") == "玩家对战"
        ]
        if interface_data["task"]:
            interface_data["task"][0]["default_check"] = True
    elif mode == "full":
        # 全功能版
        for t in interface_data.get("task", []):
            if t.get("name") == "玩家对战":
                t["default_check"] = True

    interface_data["version"] = version

    with open(build_dir / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface_data, f, ensure_ascii=False, indent=4)

    print("[3/5] 生成开箱即用默认配置...")
    # 5. 写入纯净通用的 config/instances/default.json
    config_dir = build_dir / "config"
    instances_dir = config_dir / "instances"
    instances_dir.mkdir(parents=True, exist_ok=True)

    default_instance = {
        "CurrentControllerName": "雷电模拟器（ADB）",
        "Resource": "默认",
        "CurrentTasks": [
            "玩家对战<|||>Arena.EnsureUI"
        ],
        "TaskItems": interface_data.get("task", []),
        "InstanceName": "默认配置",
        "CurrentController": 1,
        "AdbControlScreenCapType": "Encode"
    }

    with open(instances_dir / "default.json", "w", encoding="utf-8") as f:
        json.dump(default_instance, f, ensure_ascii=False, indent=2)

    with open(config_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump({"CurrentInstance": "default"}, f, ensure_ascii=False, indent=2)

    print("[4/5] 添加新手使用说明文档...")
    readme_text = f"""=====================================================
  飘流幻境新世界自动化小助手 ({mode} 版 - {version})
=====================================================

【使用前准备】：
1. 启动 雷电模拟器（支持雷电 9 / 雷电 14 等各版本）。
2. 将模拟器分辨率设为横屏：1280 × 720 (DPI 320)。
3. 打开《飘流幻境新世界》游戏，并进入对应功能界面（如“玩家对战”界面）。

【启动与运行】：
1. 双击运行文件夹内的 [MFAAvalonia.exe]。
2. 控制器选择 [雷电模拟器 14（ADB）] 或 [雷电模拟器（ADB）]，点击连接。
3. 任务列表中勾选您需要执行的任务（已默认勾选）。
4. 点击 [开始任务] 即可全自动运行！

【提示】：
- 本工具采用 100% 纯图片模板识别与 ADB 后台触控，不抢占鼠标，无惧位置微移。
- 如果提示缺少运行环境，请先双击运行 [DependencySetup_依赖库安装_win.bat]。
=====================================================
"""
    with open(build_dir / "使用说明.txt", "w", encoding="utf-8") as f:
        f.write(readme_text)

    print("[5/5] 打包生成 ZIP 压缩文件...")
    zip_output_path = DIST_DIR / f"{pkg_name}.zip"
    with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                rel_dir = os.path.relpath(root, build_dir)
                if rel_dir.startswith("debug") or rel_dir.startswith("logs") or rel_dir.startswith("temp"):
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(DIST_DIR)
                zipf.write(file_path, arcname)

    zip_size_mb = zip_output_path.stat().st_size / (1024 * 1024)
    print(f"\n 打包完成！")
    print(f"免安装目录: {build_dir}")
    print(f"分发压缩包: {zip_output_path} ({zip_size_mb:.2f} MB)")
    return zip_output_path, build_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package PLN-Auto standalone release.")
    parser.add_argument("--mode", choices=["arena", "full"], default="arena", help="Packaging mode: arena (standalone arena) or full (all tasks)")
    parser.add_argument("--version", default="v0.1.0", help="Release version string")
    args = parser.parse_args()

    build_package(mode=args.mode, version=args.version)
