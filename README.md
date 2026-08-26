<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="https://cdn.jsdelivr.net/gh/MaaAssistantArknights/design@main/v1/icons/maa-logo_512x512.png" width="128" height="128" />
</p>

<div align="center">

# PLN-Auto (飘流幻境新世界自动化小助手)

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 与 [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia) 开发的《飘流幻境新世界》自动化辅助工具。

</div>

---

## ✨ 功能特性

- 🧪 **连续炼金**：自动补充小齿轮或柴薪作为主材，并使用馒头、草菇或普通石块作为副材连续合成；支持自动向上一屏搜索备用材料。
- 🍗 **回收小鸡腿**：自动打开资源回收桶，支持多屏向下滑动搜索并自动回收所有小鸡腿。
- ⚔️ **玩家对战**：自动检测活力值并在不足时花钻补齐至设定值，自动参与对战并开启 AI 托管，支持对战超时保护与无限循环。
- 🚀 **更多自动化功能持续开发中...**

---

## 🖥️ 环境要求与支持

| 客户端类型 | 当前状态 | 说明 |
| :--- | :--- | :--- |
| **Windows PC 端游** | ✅ 已支持 | 基于 Win32 后台窗口控制，推荐游戏窗口分辨率 720p（短边） |
| **雷电模拟器 9 (Android)** | 🧪 MVP 可用 | 基于 ADB 后台截图与触控，不占用 Windows 鼠标；与 PC 端共用现有任务脚本 |

- **操作系统**：Windows 10 / 11 (x64)
- **运行权限**：如遇到窗口捕获异常，请尝试以管理员身份运行

---

## 📥 下载与使用说明

1. 前往本仓库 [Releases 页面](https://github.com/kungoodbye/pln-maa/releases) 下载最新的发布包（如 `pln-auto-win-x86_64-vX.Y.Z.zip`）。
2. 解压下载的压缩包到任意非中文路径（避免权限冲突）。
3. 启动游戏客户端并进入对应功能界面：
   - 雷电模拟器 9：将分辨率设为横屏 `1280 × 720`，开启 ADB 调试并启动游戏。
   - Windows PC 端：保持游戏窗口短边为 720p。
4. 双击运行 `MFAAvalonia.exe`（或启动器程序）：
   - 雷电模拟器 9：选择 `雷电模拟器 9（ADB）`，再连接自动发现的雷电实例。
   - Windows PC 端：选择 `Win32` 并连接到《飘流幻境新世界》窗口。
   - 在任务列表中勾选您需要执行的任务。
   - 点击 **开始** 即可自动运行。

雷电 ADB 模式直接读取模拟器画面并注入 Android 触控，不会移动或锁定 Windows 鼠标。MVP 阶段请先验证窗口失焦和被其他窗口遮挡的场景；最小化后是否持续渲染还取决于雷电实例的后台运行设置。

若新版雷电缺少 `ldopengl64.dll` 并导致连接失败，请在 MFA 的连接设置中将 ADB 截图模式改为 `Encode`。该模式使用无损 ADB PNG 截图，可避开不兼容的雷电 `EmulatorExtras` 截图插件。

本地调试包也可以在关闭 MFAAvalonia 后运行 `python tools/configure_mfaa_adb.py` 写入该兼容设置；MFAAvalonia 运行期间不会自动重新加载外部修改的实例配置。

完整的能力判断、多开实例映射和后台验收步骤见 [雷电模拟器 9 全后台自动化 MVP 可行性调研](./docs/superpowers/specs/2026-08-26-ldplayer-background-automation-feasibility.md)。

---

## 🛠️ 本地开发与贡献

### 依赖准备
- Python 3.10+
- Node.js 20+（用于格式检查与 schema 校验）

### 运行测试
```bash
# 安装测试依赖
pip install -r tools/requirements.txt pytest

# 运行自动化测试
pytest tests/
```

更多开发规范请查阅 [开发指南](./docs/zh_cn/develop/how_to_develop.md) 与 [PR 规范](./docs/zh_cn/develop/pull_request_guidelines.md)。

---

## 💖 鸣谢与生态

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开源项目的支持：
- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)：新一代自动化黑盒测试框架
- [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)：跨平台通用 GUI 客户端

[![Contributors](https://contrib.rocks/image?repo=kungoodbye/pln-maa&max=1000)](https://github.com/kungoodbye/pln-maa/graphs/contributors)
