# 雷电模拟器 9 全后台自动化 MVP 可行性调研

## 结论

MVP 可行，首选路径是让现有 MaaFramework Pipeline 改用 **ADB 控制器**，而不是继续把雷电模拟器当作普通 Win32 窗口控制。

- **不抢 Windows 鼠标：可实现。** ADB 截图和输入发生在 Android 设备侧，不需要移动 Windows 光标，也不要求雷电窗口获得焦点。Android 官方文档把 `shell` 定义为向指定设备执行命令的通道，并提供设备侧 `screencap`；AOSP 的 `input` 命令通过 Android `InputManager` 注入点击和滑动事件。[Android ADB 文档](https://developer.android.com/tools/adb#issuingcommands) [AOSP Android 9 `Input.java`](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r61/cmds/input/src/com/android/commands/input/Input.java)
- **现有脚本结构可复用。** 当前 `alchemy.json` 和 `recycle.json` 只使用控制器无关的 `Click`、`Swipe`、`DoNothing`，识别侧是 OCR/模板匹配；没有 Win32 专属消息、滚轮或虚拟键操作。因此 MVP 不需要重写 Pipeline 状态机。
- **现有识别素材不能直接承诺 100% 命中。** 需要把雷电保持为实际截图 `1280x720`（或同为 16:9、短边 720 后由 MaaFramework 缩放），再回归模板、OCR、游戏安全区和滑动距离。Android 版若字体、DPI、系统栏或游戏 UI 与 PC 版存在像素差异，可能只需校准素材/ROI，但这仍属于验收项。
- **失焦、被其他窗口遮挡：已具备强证据；真正最小化：仍需专项验收。** ADB 本身不依赖 Windows 前台窗口，但雷电官方没有承诺“宿主窗口最小化后，游戏逻辑和渲染永不暂停”。最小化时即便 `screencap` 返回 PNG，也必须确认画面是持续更新的新鲜帧，而不是最后一帧缓存。

因此 MVP 的可验收定义应分两级：

1. 第一优先级：雷电窗口失焦或被遮挡时，所有现有任务可运行，Windows 鼠标不移动、前台窗口不改变。
2. 第二优先级：雷电窗口最小化时，连续截图仍更新、输入仍生效、游戏计时/动画不暂停。若第二级失败，先采用“窗口保持还原但放在后台/被遮挡”的运行方式，仍满足不抢鼠标。

## 仓库现状与最小改动面

改动前的 [`assets/interface.json`](../../../assets/interface.json) 只声明了 `Win32` 控制器：

- 截图：`FramePool`
- 鼠标：`Seize`
- 键盘：`PostMessageWithCursorPos`

其中 `Seize` 会抢占 Windows 鼠标。MaaFramework 官方控制方式表也明确将 `Seize` 标记为“抢占鼠标、不能后台”；`SendMessage`/`PostMessage` 虽不移动鼠标并支持后台，但兼容性只有“中”，且官方明确说明 Win32 程序不存在通用输入方式。[MaaFramework 控制方式说明](https://maafw.com/docs/2.4-ControlMethods/)

MVP 只需在 Project Interface 中增加一个 `Adb` 控制器，并保留原 Win32 控制器供 PC 版使用。概念配置如下：

```json
{
  "name": "雷电模拟器 9（ADB）",
  "type": "Adb",
  "display_short_side": 720
}
```

MaaFramework Project Interface V2 将 `Adb` 列为正式控制器类型，并说明 ADB 的 input/screencap 会自动检测和选择最优方式，无需在项目配置中手工固定实现。[Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2)

不建议为 MVP 自己实现截图、点击和滑动适配器；先复用 MaaFramework 的 ADB Controller，现有任务入口、JSON Pipeline、OCR、模板和错误截图机制均可保留。

## 雷电 ADB 与多开实例寻址

雷电官方提供两条可靠路径：

1. `ldconsole.exe adb --index N --command "..."`：命令行接口可用 `--index` 或实例名称指定目标，并把 ADB 命令送到该实例。[雷电命令行接口](https://www.ldplayer.net/blog/introduction-to-ldplayer-command-line-interface.html)
2. 直接使用雷电目录内的 `adb.exe -s <serial> ...`：雷电 9 官方教程要求先运行 `adb devices` 获取设备号；多开实例编号从 0 开始，对应 serial 从 `emulator-5554` 开始，每增加一个实例，设备号增加 2，即 `serial = emulator-(5554 + 2 * index)`。[雷电 9 ADB 教程](https://help.ldmnq.com/docs/LD9adbserver)

Android 官方要求：连接多个设备时必须通过 `adb devices` 获取 serial，再使用 `adb -s serial` 指定目标；不能依赖不带 `-s` 的隐式选择。[Android ADB：指定设备](https://developer.android.com/tools/adb#directingcommands)

MVP 实例选择规则应为：

- 启动前运行雷电自带 `adb.exe devices -l`，只接受状态为 `device` 的目标 serial。
- 单实例默认 `emulator-5554`；多开按雷电官方编号映射，但仍以本次 `adb devices` 的实际在线结果为准。
- 允许用户明确选择 serial；日志同时记录雷电 index 和 ADB serial。
- 不把 HWND 当作 ADB 实例身份。`ldconsole list2` 可以列出 index、标题、窗口句柄、启动状态和进程号，适合展示实例，但 ADB 命令最终仍应绑定 serial。[雷电命令行接口](https://www.ldplayer.net/blog/introduction-to-ldplayer-command-line-interface.html)

## 截图和输入能力

### ADB 基线

Android 官方 `screencap` 在设备侧抓取显示内容；`adb exec-out screencap -p` 可把无损 PNG 直接传到 Windows。[Android ADB：截图](https://developer.android.com/tools/adb#screencap)

Android 9 AOSP `input` 命令包含：

- `tap x y`
- `swipe x1 y1 x2 y2 [duration]`
- `keyevent`
- `text`

其实现通过 Android `InputManager.injectInputEvent` 注入事件，而不是调用 Windows 鼠标 API。[AOSP Android 9 `Input.java`](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r61/cmds/input/src/com/android/commands/input/Input.java)

这条基线速度一般，但兼容性最高，适合诊断与回退。它已覆盖当前 Pipeline 所需的点击和滑动。

### MaaFramework 自动选择

MaaFramework 官方列出的 ADB 输入优先级是：

`EmulatorExtras > MaaTouch > MinitouchAndAdbKey > AdbShell`

其中 LDPlayer 9 不在 ADB Input 的 `EmulatorExtras` 支持列表内，所以雷电上的合理预期是 MaaTouch、minitouch 或最终回退到 `AdbShell`；按键在 minitouch 方案中仍走 ADB shell。官方将 `AdbShell` 标为慢但高兼容，MaaTouch/minitouch 标为快但中等兼容。[MaaFramework 控制方式说明](https://maafw.com/docs/2.4-ControlMethods/)

ADB 截图方面，MaaFramework 会尝试多种无损方式，并明确把 LDPlayer 9 列入 `EmulatorExtras` 支持范围。`MinicapDirect`/`MinicapStream` 使用有损 JPG，官方警告会显著降低模板匹配效果，因此本项目不应为追求速度强制选择 minicap。[MaaFramework 控制方式说明](https://maafw.com/docs/2.4-ControlMethods/)

当前开发环境的雷电版本不包含 MaaFramework 5.11.1 所需的 `ldopengl64.dll`，自动发现会把截图方式锁定为 `EmulatorExtras` 后连接失败。MFAAvalonia 2.12.2 的兼容设置是将 `AdbControlScreenCapType` 设为 `Encode`；这会使用无损的 `adb exec-out screencap -p` 路径，并保留输入方式自动探测。

### minitouch / MaaTouch / 控制服务边界

- minitouch 在 Android 设备内运行并通过 socket 接收多点触控协议，Windows 侧通常用 `adb forward` 连接，所以同样不移动宿主鼠标。[DeviceFarmer minitouch](https://github.com/DeviceFarmer/minitouch)
- minitouch 需要匹配设备 ABI；触控坐标上限可能与显示尺寸不同，调用方必须做坐标映射；单个 daemon 同时只支持一个连接。不合法事件流存在冻结触控、需要重启设备的风险。[DeviceFarmer minitouch](https://github.com/DeviceFarmer/minitouch)
- 原生 minitouch 在 Android 10+ 受安全策略影响，项目文档要求借助 STFService 转发。因此不要把手工部署 minitouch 作为 MVP 前置条件。[DeviceFarmer minitouch](https://github.com/DeviceFarmer/minitouch#for-android-10-and-up)
- MaaTouch 是 minitouch 协议的 Android 原生实现，并增加按键、文本等命令；它适合由 MaaFramework 自动探测和管理，而不适合本项目再写一套生命周期与 socket 管理。[MaaTouch](https://github.com/MaaAssistantArknights/MaaTouch)

推荐策略是“让 MaaFramework 自动选；失败则回退 `AdbShell`”，而不是固定依赖某个控制服务。只有在实测出现 ADB shell 滑动不自然、输入延迟过高或长按手势失败时，才单独诊断 MaaTouch/minitouch。

## 为什么不优先使用 Windows 消息控制雷电

Win32 `SendMessage`/`PostMessage` 的优点是可后台且不移动鼠标，但它们向雷电的宿主窗口发 Windows 消息，并不等同于向 Android guest 注入触摸。雷电官方 ADB/命令行文档没有承诺把这些消息稳定映射为 guest 触控；MaaFramework 也明确说明 Win32 输入没有通用方式，消息方案只有中等兼容性。[MaaFramework 控制方式说明](https://maafw.com/docs/2.4-ControlMethods/)

其他 Win32 变体也不符合 MVP 目标：

- `*WithCursorPos` 会短暂移动光标。
- `*WithWindowPos` 不移动鼠标，但会短暂移动窗口并可能闪烁。
- `Seize` 和 `LegacyEvent` 抢占鼠标且不支持后台。
- Win32 `FramePool`/`PrintWindow` 虽有伪最小化截图能力，但不能解决 guest 输入语义，且没有必要绕过已经存在的 ADB 通道。

以上行为均见 [MaaFramework 控制方式说明](https://maafw.com/docs/2.4-ControlMethods/)。Windows 消息可以保留为探索性备选，但不应成为雷电 MVP 主方案。

## 本机实测基线（2026-08-26）

测试环境只记录自动化能力，不记录截图中的账号、角色或画面内容：

- 雷电安装目录：`D:\leidian\LDPlayer9`；自带 ADB 版本为 34.0.4。
- `ldconsole list2` 显示 index 0 已启动；雷电自带 `adb devices -l` 同时发现一台实体设备和 `emulator-5554`，证明本机必须显式使用 `-s emulator-5554`，不能依赖默认目标。
- `ldconsole adb --index 0 --command "shell wm size"` 返回物理尺寸 `720x1280`；横屏 `adb exec-out screencap -p` 得到有效的无损 RGBA PNG，实际画面尺寸为 `1280x720`。
- 雷电窗口失焦、Codex 位于前台时，ADB 截图仍成功。
- 连续 5 次 `adb -s emulator-5554 exec-out screencap -p` 均得到有效 PNG，中位耗时 261.3 ms，最大 298.8 ms。当前全局 Pipeline `rate_limit` 为 800 ms，因此保守的 ADB 截图基线已满足 MVP 节奏。
- `adb -s emulator-5554 shell input keyevent 0` 执行成功，且 Windows 前台 HWND 未变化，说明设备侧输入路径不抢前台焦点。
- 雷电自带 `ldconsole.exe` 的本机命令帮助包含 `adb --index ... --command ...`、`list2` 和 `downcpu --rate 0~100`。MVP 不应启用 `downcpu`，避免人为降低后台实例处理能力。

这些结果证明“失焦、无鼠标、无损截图、指定实例输入”已经具备。它们没有证明“宿主窗口最小化后游戏持续更新”，该项仍需下面的最小化验收。

## 最小化、暂停与后台限制

必须区分“命令执行成功”和“游戏仍在运行”：

- ADB 连接在线，只代表 adbd 可通信。
- `screencap` 返回有效 PNG，可能仍是缓存或静止画面。
- `input` 进程退出码为 0，只代表注入请求已提交，不保证目标游戏接受或处理。
- 游戏可能在宿主最小化、Android 失去焦点、屏幕关闭、锁屏或系统省电时降低帧率/暂停逻辑。雷电和 Android 官方资料没有为本项目目标游戏给出相反保证。

最小化验收必须同时验证：

1. 最小化前后 ADB serial 不变且状态持续为 `device`。
2. 最小化后间隔抓取多帧，画面中的动画/计时或游戏状态持续变化，不能只检查 PNG 可解码。
3. 在安全页面执行一次 Maa `Click` 和一次 `Swipe`，目标 UI 按预期变化，Windows 光标和前台窗口均不变。
4. 连续运行至少 10 分钟，OCR/模板识别没有持续读取旧帧，游戏流程没有因暂停而超时。
5. 恢复窗口后画面状态与后台日志一致，不存在积压输入集中释放。

若最小化失败但失焦/遮挡成功，MVP 应明确限制为“雷电窗口保持还原，可置于其他窗口后方”；不要转回 Windows 鼠标模拟，因为那会丢失本次 MVP 的核心价值。

## 建议的 MVP 验收顺序

1. 在 `interface.json` 增加 ADB 控制器，保留现有 Win32 控制器；不修改 Pipeline。
2. 固定雷电目标实例为 index 0 / `emulator-5554`，显示与截图保持 `1280x720` 横屏、DPI 320 作为首轮基线。
3. 先在窗口可见但失焦状态运行“连续炼金”和“回收小鸡腿”，检查全部 Click/Swipe、OCR、模板与失败截图。
4. 再用窗口被遮挡状态重复，监控 Windows 前台 HWND 与鼠标位置不变化。
5. 最后执行最小化验收；失败时交付“还原但后台遮挡”的限制说明，而不是扩大到自研控制服务。

通过标准：现有两个任务入口均无需分叉 Pipeline；Windows 鼠标位置和前台窗口不被改变；失败仍能产出 MaaFramework 错误截图；最小化能力按实际新鲜帧和游戏状态单独标记为通过或受限。

## 一手来源

- [雷电模拟器：命令行接口](https://www.ldplayer.net/blog/introduction-to-ldplayer-command-line-interface.html)
- [雷电模拟器 9：连接 ADB 与多开设备号映射](https://help.ldmnq.com/docs/LD9adbserver)
- [Android Developers：Android Debug Bridge](https://developer.android.com/tools/adb)
- [AOSP Android 9：`input` 命令实现](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r61/cmds/input/src/com/android/commands/input/Input.java)
- [MaaFramework：控制方式说明](https://maafw.com/docs/2.4-ControlMethods/)
- [MaaFramework：Project Interface V2](https://maafw.com/docs/3.3-ProjectInterfaceV2)
- [DeviceFarmer：minitouch](https://github.com/DeviceFarmer/minitouch)
- [MaaAssistantArknights：MaaTouch](https://github.com/MaaAssistantArknights/MaaTouch)
