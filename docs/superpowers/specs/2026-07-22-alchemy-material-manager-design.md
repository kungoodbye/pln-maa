# 炼金材料管理器与一键运行设计

## 背景

现有 `pln-auto` 已有经过人工测试的 MaaFramework Pipeline：检查合成页面和排序、按背包视觉顺序补主副材料、单次上滑搜索副料、开始连续合成、关闭结果弹窗、材料耗尽时正常停止，并在异常时保留截图。

第一阶段新增一个面向使用者的 Windows 桌面程序。它负责从游戏物品资源中搜索、多选炼金主材和副材，并在同一窗口中直接连接游戏并启动已有 Pipeline。使用者不需要打开或操作 MFAAvalonia。

本设计只覆盖炼金材料管理和一键运行，不增加配方、数量、阈值或滚动次数等面向使用者的开关。

## 目标和非目标

### 目标

- 交付一个可解压运行的 Windows x64 包，入口为 `飘流炼金助手.exe`。
- 可按中文名称搜索、查看图标，并分别多选主材和副材。
- 材料候选来自已反编译的游戏物品数据，不需要用户提供游戏截图。
- 点击开始后自动查找游戏窗口、生成本次材料的资源覆盖、运行 `Alchemy.EnsureUI`，并显示状态与日志。
- 主副材均按背包视觉顺序优先；UI 选择列表的顺序不改变游戏内选择顺序。
- 选择和窗口匹配规则以可编辑 JSON 保存，重启后保留。
- 正常耗尽、用户停止、连接失败和 Pipeline 错误在 UI 中有明确的不同状态；Pipeline 错误继续保留原有失败截图。

### 非目标

- 不自动从任意游戏页面导航到合成页。
- 不改变现有的材料放入数量、一次副料滚动、合成结果关闭或停止判断逻辑。
- 不在 UI 中提供材料识别阈值、任务开关、鼠标模式或任意 Pipeline 高级参数。
- 不包含 MFAAvalonia，也不通过模拟点击其界面来执行任务。
- 不尝试将 MaaFramework 原生库、OCR 模型和物品资源压入单一二进制文件。

## 交付结构

发布物是便携 ZIP。解压后用户只需运行根目录的 `飘流炼金助手.exe`；它以自包含 .NET 发布，目标机器不需要安装 .NET。

```text
飘流炼金助手/
  飘流炼金助手.exe
  app/
    resources/                 # Maa Pipeline、OCR、空槽模板和运行时资源
    materials/                 # 精简物品目录、图标和标准化识别模板
    native/                    # MaaFramework 与 Avalonia 所需原生依赖
  data/
    material-profile.json      # 用户材料和窗口规则，首次运行创建
    runtime/                   # 根据 profile 生成的可写 Maa 资源目录与日志
  THIRD-PARTY-NOTICES.md
  LICENSE
```

`data/` 与程序同目录，方便备份和手动编辑；程序发现目录不可写时明确报错，不静默改用其他位置。更新发布包时只替换 `app/` 和 EXE，保留用户的 `data/`。

## 材料目录和模板

### 离线构建来源

材料目录在开发/发布阶段从以下来源生成，运行时不读取游戏安装目录或反编译文件：

- `pln-recode/runs/2026-07-21-111734/parsed/itemdata.json`：物品 ID、名称、类别、等级、`material` 标记与图标 ID。
- `pln-recode/tools/item-icons/output/catalog.json`：物品 ID 到图标文件的映射。
- `pln-recode/tools/item-icons/output/icons/`：原始图标 PNG。

生成产物为 `alchemy-materials.json` 与每个候选的缩略图/绿色掩码识别模板。条目以 `item_id` 为主键，绝不只按图标 ID；多个物品可复用同一图标，但 profile 仍保存用户选中的具体物品 ID。

候选过滤规则固定为：非装备、`level > 0`、`material` 非空、名称不含“未”或“测试”、不属于“任务道具”，且名称不属于“家具设计图”或“家常食谱”。不使用 `alchemy_flag` 作为投入材料白名单，因为它描述炼金产物性质而不是投入资格。

所有符合条件的图标随包分发，供离线搜索和显示；启动任务时只把本次主副材所需的标准化模板复制到可写运行时目录。模板生成使用固定的 1280x720 显示比例、绿色透明掩码和数量文字裁切规则，与现有 `alchemy/*.png` 模板保持一致。默认模板阈值为 `0.78`，保存在 profile 的可编辑运行字段中，而不是 UI 控件。程序要求该值在 `0 < threshold <= 1` 内；不合法时在启动前报出配置错误。

### Profile

`data/material-profile.json` 的版本化结构如下；显示名称和图标 ID是目录快照，运行时以 `item_id` 重新校验。

```json
{
  "schema_version": 1,
  "window": {
    "class_name": "UnityWndClass",
    "title": "飘流幻境新世界"
  },
  "automation": {
    "template_threshold": 0.78
  },
  "materials": {
    "main": [
      { "item_id": "46155", "name": "天狗面具模", "icon_id": "1729" }
    ],
    "secondary": [
      { "item_id": "32024", "name": "馒头", "icon_id": "1207" }
    ]
  }
}
```

保存时主材和副材各自去重。目录版本变化时，缺失或不再符合过滤规则的 ID 不会被静默删除，而是作为配置错误显示，直到用户移除或重新选择。

## UI 和交互

单窗口采用工作台布局：左侧为“主材”和“副材”两个固定高度的已选材料列表；右侧是共享的搜索结果区；底部为连接状态、滚动日志与运行控制。

- 搜索按名称包含匹配，输入为空时显示候选首批结果。结果显示图标、名称与物品 ID，便于区分同名物品。
- 每个结果可加入主材或副材；已加入的一侧显示为稳定尺寸的材料项，可单独移除。同一物品允许同时存在于主材和副材，因为两槽的用途由用户选择决定。
- 开始按钮仅在主副材均至少选择一项且应用处于空闲、已完成或失败状态时可用。
- 运行时材料编辑控件锁定，开始按钮替换为停止按钮；停止由 MaaFramework API 终止任务，绝不点击游戏内“停止”。
- 运行日志持续显示连接、配置生成、Pipeline focus 消息、正常耗尽、用户停止和异常。异常日志提供失败截图所在的本地路径。
- 自动查找唯一的 `UnityWndClass` + “飘流幻境新世界”窗口。无匹配时提示用户启动游戏；多匹配时显示窗口标题和类名的选择列表，用户选择后只保存标题/类名规则，不保存会失效的 HWND。

不在界面中重复解释现有炼金规则；前置条件或不可继续的状态以简短错误信息呈现，例如“未检测到合成页面”“材料槽含未选择材料”。

## 运行架构

应用是一个 Avalonia 前端和 MaaFramework C# SDK 宿主，二者在同一进程内运行。采用官方 SDK 而非控制 MFAAvalonia：

1. `MaaToolkit.Shared.Desktop.Window.Find()` 枚举桌面窗口。
2. 选定的 `DesktopWindowInfo` 用 `ToWin32ControllerWith` 创建 Win32 控制器，使用 `FramePool` 截图和 `Seize` 鼠标模式；以 `LinkOption.Start` 重新连接当前 HWND。
3. `PipelineComposer` 将打包的基线资源复制/同步到 `data/runtime/resource`，复制本次选择的模板，并生成 `pipeline/alchemy.json`。
4. `MaaResource` 加载此运行时资源，`MaaTasker` 绑定控制器和资源后追加 `Alchemy.EnsureUI` 任务。
5. SDK 回调被转换为 UI 日志和状态事件。任务完成、取消和错误各自完成一次状态转换并释放控制器、资源和任务对象。

`PipelineComposer` 只修改与材料候选有关的节点：`Alchemy.MainFilled`、`Alchemy.RefillMain` 使用主材模板；`Alchemy.SubFilled`、`Alchemy.RefillSub`、`Alchemy.RefillSubAfterSwipe` 使用副材模板。其余 Pipeline 节点逐字保留基线，包括 ROI、排序检查、一次上滑、数量确认、关闭弹窗、失败截图和停止判断。

开始前生成一个槽位守卫：主/副槽必须是空槽或当前所选材料之一。两种情况之外，任务以“材料槽含未选择材料”失败并且不点击背包，避免在遗留材料上追加投入。

运行状态机是：`Idle -> Validating -> Preparing -> Connecting -> Running -> (Completed | Stopped | Failed)`。所有 UI 状态变更都在 UI 线程执行；资源生成和 SDK 等待在后台任务执行。进入终态后重新允许编辑和开始。

## 错误处理

- Profile JSON 格式无效、主/副材为空、ID 不在目录中、资源缺失或运行目录不可写：不创建控制器，显示本地配置错误。
- 游戏窗口不存在或连接失败：不运行 Pipeline，保留用户选择并显示可重试错误。
- 无法确认合成页面、排序、槽位、数量弹窗或其他 Pipeline 识别步骤：由 MaaFramework 返回失败，UI 标记失败并报告 `data/runtime/debug/on_error/` 下截图路径。
- 材料耗尽及副材单次上滑后仍找不到材料：沿用 `Alchemy.NormalEnd*`，标记为“正常完成”，不生成失败截图。
- 用户停止：停止当前 `MaaTasker`，等待释放完成后标记“已停止”；不会尝试关闭游戏弹窗或修改材料选择。
- 已运行时应用退出：请求停止并等待有限时间；无法正常释放时只结束本地进程，不额外向游戏发送输入。

## 测试和验收

### 单元与结构测试

- 目录构建测试覆盖筛选规则、ID/图标映射、多图标共享、重复选择和目录版本变更。
- Profile 测试覆盖新建、保存、加载、非法 JSON、空主副材和失效 ID。
- 模板测试验证每个生成模板存在、尺寸固定、绿色掩码和非绿色像素同时存在；已知的小齿轮、柴薪、馒头、草菇、普通石块作为回归样本。
- Composer 测试断言仅替换五个材料节点，主副数组与 profile 一致，其他节点哈希不变，基线 JSON 和生成 JSON 均能通过 Maa schema 检查。
- 窗口规则测试覆盖唯一命中、无命中、多命中、标题/类名保存和不保存 HWND。
- Runner 测试用 SDK/控制器适配层假对象验证状态机、停止、日志转发和异常清理，不启动游戏。

### 人工验收

- 搜索“小齿轮”“柴薪”“天狗面具模”“馒头”“草菇”“普通石块”并能在主副两侧任意组合选择和保存。
- 解压发布 ZIP 到无开发环境的 Windows x64 机器，双击 EXE 可启动；不需要 .NET、MFAAvalonia 或游戏资源反编译目录。
- 唯一游戏窗口自动连接，多个候选窗口可选择，无窗口时不发送输入。
- 在已确认的合成页、物等小到大排序、槽位为空的条件下，主副材料按背包视觉顺序补入并开始连续炼金。
- 连续炼金结束后正确处理正常耗尽、用户停止和识别失败，日志和失败截图可定位。
- 发布包包含许可证和第三方声明，且用户 `data/` 在更新程序文件后仍可继续使用。

## 依赖和发布

- 前端：Avalonia 11，.NET 10 Windows x64 自包含发布。
- 自动化：MaaFramework 官方 C# Binding 与对应的 Windows 原生运行库；使用 `MaaToolkit.Shared.Desktop.Window.Find`、Win32 Controller、MaaResource 和 MaaTasker。
- 构建机需要 .NET 10 SDK；当前本机只有 .NET Runtime，实施前需要安装 SDK 或改用 CI 构建。
- 发布流程扩展现有 GitHub Actions：先构建材料目录/模板和 Avalonia publish，再将发布输出、Maa 原生库、项目资源、OCR、许可证压缩为 Windows x64 ZIP。
- 包中保留 MaaFramework、Avalonia 及其依赖的适用许可证和第三方声明。
