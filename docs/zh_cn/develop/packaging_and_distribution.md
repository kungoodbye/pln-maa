# 项目打包与绿色分发维护指南

## 1. 概述

本项目基于 MaaFramework / MFAAvalonia 体系构建，除了支持本地开发调试外，还提供了**本地一键生成免安装绿色发布包**的能力，方便直接分发给没有 Python / 开发环境的普通玩家使用。

---

## 2. 本地打包工具：`tools/package.py`

### 2.1 工具特性
1. **纯净构建**：自动从 `.create-maa-project/runtime/mfaa/win-x64/` 提取运行时环境，并自动剥离开发调试产生的 `debug/`、`logs/`、`temp/`、`backup/` 临时文件；
2. **最新资源注入**：自动将开发区最新的 `assets/resource/` 和 `assets/interface.json` 注入到发布包中；
3. **开箱即用预设**：自动为普通玩家生成兼容的 `config/instances/default.json`（预置雷电模拟器 ADB 自动连接与无损 `Encode` 截图兼容模式）；
4. **多形态分发**：支持打包“玩家对战专属版”与“全功能整合版”。

---

## 3. 打包命令与使用方法

在项目根目录下执行以下命令：

```bash
# 1. 打包【玩家对战专属独立版】（推荐分发给只需要对战的玩家，界面最精炼）
python tools/package.py --mode arena --version v0.1.0

# 2. 打包【全功能整合版】（包含玩家对战、连续炼金、回收小鸡腿）
python tools/package.py --mode full --version v0.1.0
```

### 打包输出产物
打包完成后，产物输出在根目录的 `dist/` 目录下（已配置 `.gitignore` 保护）：
- `dist/pln-auto-arena-v0.1.0-win-x64.zip`（单文件绿色压缩包，约 112 MB，便于直接发送）
- `dist/pln-auto-arena-v0.1.0-win-x64/`（解压后的免安装文件夹）

---

## 4. 普通玩家使用说明

普通玩家拿到压缩包后，只需三步：
1. **解压 ZIP 压缩包** 到任意英文/非中文路径；
2. 启动雷电模拟器（雷电 9 / 雷电 14 均可），分辨率设为横屏 `1280 × 720 (DPI 320)`，打开游戏进入对应功能界面；
3. 双击运行 **`MFAAvalonia.exe`**，点击 **“开始任务”** 即可直接全自动运行。
