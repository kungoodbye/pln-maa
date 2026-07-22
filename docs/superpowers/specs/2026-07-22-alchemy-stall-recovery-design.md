# 炼金连续合成卡死检测与自动恢复设计

## 背景

连续炼金偶发停留在“连续合成中...”页面：主料和副料槽仍有材料，中央没有“获得”或升级结果，且“停止”仍可见。正常运行时，中央结果区域会出现“获得”或“提高至”提示。

当前 Pipeline 在 `Alchemy.WaitRunning` 和 `Alchemy.WaitFinished` 中无限等待“停止”状态变化。它不检查连续合成期间是否仍有结果，因此上述游戏异常会使任务永久等待。

## 目标和范围

- 每秒观察结果区域一次，以结果提示作为连续合成仍有进展的心跳。
- 连续 5 次未见结果提示时，将仍显示“停止”的页面视为卡死。
- 卡死后自动点击游戏内“停止”，确认界面重新允许“合成开始”，检查材料槽后继续连续合成。
- 自然材料耗尽仍沿用现有正常结束和补料路径，不触发自动重启。
- 同一任务运行内累计自动恢复 3 次后安全终止，避免无限停止和重启。
- 保留可读的 focus 日志和恢复计数；不把截图作为每次自动恢复的必经动作。

## 非目标

- 不试图定位或修复游戏客户端、网络或服务端导致空白结果的根因。
- 不改变主副材料选择、投放数量、背包滚动和最终结果弹层关闭规则。
- 不在恢复时盲目补料或直接点击背包；材料槽状态仍由既有识别节点决定。

## 结果心跳

新增 `Alchemy.WaitProgress`，其识别范围限定在中央结果提示区域，避免读取背包、按钮和合成槽文字。

- 正常信号：OCR 识别到 `获得` 或 `提高至`。`提高至` 覆盖结果中的 `提高至+...` 形式，避免依赖 OCR 对加号的稳定识别。
- 轮询间隔：1000 ms。
- 无信号阈值：5000 ms，即连续 5 次轮询均未识别到任一正常信号。
- 每次识别到正常信号后回到 `Alchemy.WaitProgress`，并在下一秒继续观察。日志记录一次“检测到合成进度”，但不点击游戏。

该规则以进度条件而非固定合成时长判定异常。它允许结果提示在短暂动画中缺失一次，也将总等待限制在约 5 秒。

## 异常与恢复状态机

```text
StartAlchemy -> WaitRunning -> WaitProgress
WaitProgress --获得 / 提高至--> WaitProgress
WaitProgress --5 秒无结果--> InspectAfterHeartbeatTimeout

InspectAfterHeartbeatTimeout --停止已消失--> DismissResult -> 现有补料/结束循环
InspectAfterHeartbeatTimeout --停止仍可见--> RecoveryStop
RecoveryStop -> WaitRestartReady -> MainFilled/MainEmpty
MainFilled -> SubFilled/SubEmpty -> StartAlchemy
```

### 启动守卫

`Alchemy.WaitRunning` 不再无限等待。点击“合成开始”后必须在 15 秒内识别到“停止”。若未进入运行态，仅在确认“合成开始”仍可点击时重试一次；第二次仍失败则按现有错误机制结束任务。这个分支不把“未开始”误当作运行中卡死。

### 心跳超时分流

`Alchemy.WaitProgress` 超时时首先运行 `Alchemy.InspectAfterHeartbeatTimeout`：

1. “停止”已消失：视为游戏已自然停止，进入现有 `Alchemy.DismissResult` 和槽位检查流程。不会点击“停止”，也不会计入恢复次数。
2. “停止”仍可见：视为图 1 所示卡死，进入 `Alchemy.RecoveryStop`。

### 自动恢复

`Alchemy.RecoveryStop` 只在“停止”仍可见时点击一次。随后 `Alchemy.WaitRestartReady` 等待右下角“合成开始”重新出现，最长 15 秒。

按钮恢复后，不直接重新投放材料。流程跳回既有 `Alchemy.MainFilled` / `Alchemy.MainEmpty` 分支，依次确认主料和副料：

- 两槽都在：直接重新点击“合成开始”。
- 只有一槽为空：使用既有补料分支补齐后再开始。
- 材料确实耗尽：进入现有 `Alchemy.NormalEnd*`，不当作卡死。
- 任何槽位或按钮状态无法判断：沿用 Pipeline 错误退出，不继续发送点击。

### 恢复上限

每次执行 `RecoveryStop` 记为一次恢复。单次任务最多允许 3 次自动恢复；之后即使曾重新观察到结果，仍不重置该上限。这个保守限制避免在长时间运行中对异常游戏页面无限发送输入。

`Alchemy.RecoveryStop` 设置 `max_hit: 3`。在心跳超时的 `on_error` 候选列表中，顺序为：

1. `Alchemy.NaturalFinishAfterHeartbeatTimeout`：仅在“停止”已消失时命中，进入正常结束路径。
2. `Alchemy.RecoveryStop`：仅在“停止”仍可见且未超过 `max_hit` 时命中，点击一次停止并恢复。
3. `Alchemy.RecoveryLimitReached`：仅在“停止”仍可见、前一节点因 `max_hit` 被跳过时命中，执行 `StopTask` 并输出 `已达到 3 次自动恢复上限，任务已停止`。

这是防止游戏持续异常时自动化无限输入的唯一终止保护。

## 实现边界

首版只修改 `assets/resource/pipeline/alchemy.json`，使用 MaaFramework 已有的 OCR、`timeout`、`on_error` 和节点跳转能力：

- 将 `Alchemy.WaitRunning` 的无限超时替换为有限启动确认及一次受控重试。
- 以 `Alchemy.WaitProgress` 取代 `Alchemy.WaitFinished` 的无限空等。
- 在心跳超时的 `on_error` 中按顺序检查“停止已消失”和“停止仍可见”，分别接自然结束或自动恢复分支。
- 令 `Alchemy.RecoveryStop.max_hit` 为 `3`，并在其后放置 `Alchemy.RecoveryLimitReached`，使框架跳过已达上限的恢复节点后明确终止任务。

不新增图像模板、Python Agent、桌面程序功能或用户可配置选项。若现场验证表明正常结果提示常超过 5 秒不出现，才调整阈值；不得仅凭猜测扩大超时。

## 日志和证据

每次状态转换输出 focus 日志：心跳识别、首次无结果、自然结束确认、已点击停止、等待重新开始、恢复次数、恢复成功或恢复上限终止。它们用于将后续日志与截图中的页面状态对应。

本设计不在每次自动恢复时主动保存截图。框架原有 `save_on_error` 行为只在最终无法判定、启动两次失败或恢复上限终止等不可恢复错误时保留失败现场。

## 验收

1. 正常连续合成至少持续 30 秒，期间持续识别结果心跳；不得点击游戏内“停止”。
2. 材料自然耗尽时，“停止”消失后进入现有补料或正常结束路径；不得将其计为卡死恢复。
3. 在复现图 1 的无结果页面后约 5 秒，任务点击一次“停止”，等待“合成开始”出现，检查两个槽位，并重新开始。
4. 恢复后出现“获得”或“提高至”时，连续合成继续，且该任务此前的恢复计数保持不变。
5. 单次任务第 4 次发生卡死时，任务停止且不再向游戏发送输入。
6. 点击“合成开始”后 15 秒仍未出现“停止”时只重试一次；第二次失败终止并由既有错误处理留证。
7. `npx --yes @nekosu/maa-tools check` 通过，且 `git diff --check` 无空白错误。
