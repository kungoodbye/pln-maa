# Alchemy Material Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable Windows x64 Avalonia application that searches and multi-selects alchemy materials, then directly runs `Alchemy.EnsureUI` against the game window.

**Architecture:** A deterministic Python compiler in `pln-recode` publishes a filtered material catalog and normalized templates into tracked `pln-auto/assets/materials`. A .NET 10 Avalonia application consumes those packaged assets, saves a portable JSON profile, composes a per-profile Maa resource directory, and hosts the official MaaFramework C# binding.

**Tech Stack:** .NET 10, Avalonia 11.4.1, CommunityToolkit.Mvvm 8.4.0, Maa.Framework.Binding 5.8.0, xUnit, Python 3.13, Pillow, MaaFramework Pipeline JSON, PowerShell 7.

## Global Constraints

- Publish a self-contained `win-x64` ZIP whose user-facing entry point is `飘流炼金助手.exe`; Maa resources remain external files.
- Use MaaFramework C# APIs directly. Do not launch, automate, or package MFAAvalonia.
- Match `UnityWndClass` and `飘流幻境新世界`; use `FramePool` and `Seize`; persist title/class rules only, never HWND values.
- Preserve every existing Pipeline ROI and control-flow node. Compose only template/threshold arrays in `Alchemy.MainFilled`, `Alchemy.RefillMain`, `Alchemy.SubFilled`, `Alchemy.RefillSub`, and `Alchemy.RefillSubAfterSwipe`.
- Eligibility is non-equipment, `level > 0`, non-empty `material`, no name containing `未` or `测试`, and no `任务道具`, `家具设计图`, or `家常食谱`. Never filter by `alchemy_flag`.
- Profile identity is `item_id`; same-icon entries remain distinct. In-game selection remains visual grid order, not UI selection order.
- `automation.template_threshold` defaults to `0.78`, must satisfy `0 < threshold <= 1`, and has no UI control.
- Runtime never reads the game installation or `pln-recode`. All writes stay below the EXE's `data/` directory.

## File Structure

```text
pln-recode/tools/item-icons/build_alchemy_material_catalog.py
pln-recode/tools/item-icons/tests/test_build_alchemy_material_catalog.py
pln-auto/assets/materials/{alchemy-materials.json,icons/,templates/}
pln-auto/app/PlnAlchemyAssistant/{Models/,Services/,ViewModels/,PlnAlchemyAssistant.csproj}
pln-auto/app/PlnAlchemyAssistant.Tests/
pln-auto/tools/{package_alchemy_assistant.ps1,verify_alchemy_assistant_package.ps1}
pln-auto/.github/workflows/release-alchemy-assistant.yml
```

## Task 1: Establish the .NET 10 desktop solution

**Files:**
- Create: `app/PlnAlchemyAssistant/PlnAlchemyAssistant.csproj`
- Create: `app/PlnAlchemyAssistant/Program.cs`
- Create: `app/PlnAlchemyAssistant/App.axaml`
- Create: `app/PlnAlchemyAssistant/App.axaml.cs`
- Create: `app/PlnAlchemyAssistant/MainWindow.axaml`
- Create: `app/PlnAlchemyAssistant/MainWindow.axaml.cs`
- Create: `app/PlnAlchemyAssistant/Services/ApplicationPaths.cs`
- Create: `app/PlnAlchemyAssistant.Tests/PlnAlchemyAssistant.Tests.csproj`
- Create: `app/PlnAlchemyAssistant.Tests/ApplicationPathsTests.cs`
- Create: `app/PlnAlchemyAssistant.sln`

**Interfaces:**
- Produces `ApplicationPaths.FromExecutableRoot(string executableRoot)` for all portable file locations.
- Produces a `net10.0`, `win-x64`, self-contained Avalonia executable and xUnit test project.

- [ ] **Step 1: Verify the .NET SDK prerequisite**

Run:

```powershell
dotnet --list-sdks
```

Expected: a `10.0.*` SDK. If absent, install the official .NET 10 SDK before creating files; the installed runtime alone cannot compile the app.

- [ ] **Step 2: Write the failing path test**

```csharp
using PlnAlchemyAssistant.Services;

public sealed class ApplicationPathsTests
{
    [Fact]
    public void FromExecutableRoot_UsesPortableLocations()
    {
        var paths = ApplicationPaths.FromExecutableRoot("C:\\portable\\assistant");
        Assert.Equal("C:\\portable\\assistant\\data", paths.DataRoot);
        Assert.Equal("C:\\portable\\assistant\\data\\runtime\\resource", paths.RuntimeResourceRoot);
        Assert.Equal("C:\\portable\\assistant\\app\\materials\\alchemy-materials.json", paths.MaterialCatalogPath);
        Assert.Equal("C:\\portable\\assistant\\app\\resources", paths.PackagedResourceRoot);
    }
}
```

- [ ] **Step 3: Run the test and confirm it fails**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~ApplicationPathsTests
```

Expected: FAIL because the solution and application project do not exist.

- [ ] **Step 4: Create projects and the minimal app**

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType><TargetFramework>net10.0</TargetFramework>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier><SelfContained>true</SelfContained>
    <PublishSingleFile>false</PublishSingleFile><Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings><AssemblyName>飘流炼金助手</AssemblyName>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Avalonia" Version="11.4.1" />
    <PackageReference Include="Avalonia.Desktop" Version="11.4.1" />
    <PackageReference Include="Avalonia.Themes.Fluent" Version="11.4.1" />
    <PackageReference Include="CommunityToolkit.Mvvm" Version="8.4.0" />
    <PackageReference Include="Maa.Framework.Binding" Version="5.8.0" />
  </ItemGroup>
  <ItemGroup>
    <Content Include="..\\..\\assets\\resource\\**\\*" Link="app\\resources\\%(RecursiveDir)%(Filename)%(Extension)" CopyToOutputDirectory="PreserveNewest" CopyToPublishDirectory="PreserveNewest" />
    <Content Include="..\\..\\assets\\materials\\**\\*" Link="app\\materials\\%(RecursiveDir)%(Filename)%(Extension)" CopyToOutputDirectory="PreserveNewest" CopyToPublishDirectory="PreserveNewest" />
  </ItemGroup>
</Project>
```

```csharp
namespace PlnAlchemyAssistant.Services;

public sealed record ApplicationPaths(string ExecutableRoot, string DataRoot,
    string RuntimeResourceRoot, string MaterialCatalogPath,
    string PackagedResourceRoot, string MaterialTemplateRoot, string ProfilePath)
{
    public static ApplicationPaths FromExecutableRoot(string executableRoot)
    {
        var root = Path.GetFullPath(executableRoot);
        var data = Path.Combine(root, "data");
        return new(root, data, Path.Combine(data, "runtime", "resource"),
            Path.Combine(root, "app", "materials", "alchemy-materials.json"),
            Path.Combine(root, "app", "resources"),
            Path.Combine(root, "app", "materials", "templates"),
            Path.Combine(data, "material-profile.json"));
    }
}
```

Create standard Avalonia `BuildAvaloniaApp`, open an empty fixed-minimum `MainWindow`, and reference the app project from tests. Use `Microsoft.NET.Test.Sdk` 17.14.1, `xunit` 2.9.2, and `xunit.runner.visualstudio` 3.1.1 in the test project.

- [ ] **Step 5: Verify the baseline and commit it**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~ApplicationPathsTests
dotnet build app\PlnAlchemyAssistant\PlnAlchemyAssistant.csproj -c Debug
git add app\PlnAlchemyAssistant app\PlnAlchemyAssistant.Tests app\PlnAlchemyAssistant.sln
git commit -m "feat: scaffold alchemy assistant desktop app"
```

Expected: both .NET commands exit `0` before the commit.

## Task 2: Compile the filtered material asset pack in `pln-recode`

**Files:**
- Create: `D:/飘流幻境新世界/pln-recode/tools/item-icons/build_alchemy_material_catalog.py`
- Create: `D:/飘流幻境新世界/pln-recode/tools/item-icons/tests/test_build_alchemy_material_catalog.py`
- Modify: `D:/飘流幻境新世界/pln-recode/tools/item-icons/README.md`
- Create: `assets/materials/alchemy-materials.json`
- Create: `assets/materials/icons/`
- Create: `assets/materials/templates/`

**Interfaces:**
- Produces `build_material_pack(itemdata_path, icon_catalog_path, icon_root, output_root) -> dict`.
- Each catalog item contains exactly `item_id`, `name`, `icon_id`, `icon_file`, and `template_file`; paths are relative to `assets/materials`.

- [ ] **Step 1: Write failing eligibility and template tests**

```python
class MaterialPackTests(unittest.TestCase):
    def test_is_eligible_keeps_known_materials_and_rejects_excluded_rows(self):
        self.assertTrue(module.is_eligible({"id": "32024", "name": "馒头", "level": 1, "type": "料理", "category": "料理", "material": "麦"}))
        self.assertTrue(module.is_eligible({"id": "46155", "name": "天狗面具模", "level": 1, "type": "兽虫制品", "category": "兽虫制品", "material": "木材"}))
        self.assertFalse(module.is_eligible({"id": "1", "name": "测试道具", "level": 1, "type": "道具", "category": "道具", "material": "木材"}))
        self.assertFalse(module.is_eligible({"id": "2", "name": "任务道具", "level": 1, "type": "道具", "category": "任务道具", "material": "木材"}))

    def test_write_template_creates_71_by_55_green_mask_png(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            Image.new("RGBA", (32, 32), (255, 0, 0, 255)).save(source)
            destination = Path(directory) / "template.png"
            module.write_template(source, destination)
            image = Image.open(destination).convert("RGB")
            self.assertEqual((71, 55), image.size)
            self.assertIn((255, 0, 0), image.getdata())
```

- [ ] **Step 2: Confirm failure and implement the compiler**

Run from `D:\飘流幻境新世界\pln-recode\tools\item-icons`:

```powershell
python -m unittest tests.test_build_alchemy_material_catalog -v
```

Expected: FAIL because the compiler module does not exist. Then implement:

```python
EXCLUDED_CATEGORY_NAMES = {"任务道具", "家具设计图", "家常食谱"}
EXCLUDED_NAME_PARTS = ("未", "测试")

def is_eligible(item: dict) -> bool:
    name = str(item.get("name", "")).strip()
    category = str(item.get("category", "")).strip()
    item_type = str(item.get("type", "")).strip()
    return (int(item.get("level", 0) or 0) > 0
        and bool(str(item.get("material", "")).strip())
        and "装备" not in item_type and "装备" not in category
        and category not in EXCLUDED_CATEGORY_NAMES
        and not any(part in name for part in EXCLUDED_NAME_PARTS))

def write_template(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGBA").resize((71, 70), Image.Resampling.LANCZOS)
    green = Image.new("RGB", (71, 70), (0, 255, 0))
    green.paste(image, mask=image.getchannel("A"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    green.crop((0, 0, 71, 55)).save(destination, "PNG")
```

Flatten `catalog.json` into an `icon_id -> icon_file` map, join ItemData by `icon_id`, filter, sort by `(name, int(item_id))`, copy each source icon once to `icons/s<icon_id>.png`, and write `templates/s<icon_id>.png`. JSON is `{"schema_version": 1, "source": {...}, "items": [...]}` with SHA-256 input JSON values. Reject missing icons and conflicting duplicate item IDs.

- [ ] **Step 3: Run tests and publish the tracked asset pack**

Run from `D:\飘流幻境新世界\pln-recode`:

```powershell
python -m unittest tools.item-icons.tests.test_build_alchemy_material_catalog -v
python tools\item-icons\build_alchemy_material_catalog.py --itemdata runs\2026-07-21-111734\parsed\itemdata.json --icon-catalog tools\item-icons\output\catalog.json --icon-root tools\item-icons\output\icons --output ..\pln-auto\assets\materials
```

Expected: tests PASS and the catalog contains IDs `32024`, `37089`, `41005`, `43001`, and `46155`, each with existing icon/template files.

- [ ] **Step 4: Document rebuild and commit only published assets**

Document the command, source run, and output ownership in the recode README. Do not initialize Git in `pln-recode`. Then run:

```powershell
git -C D:\飘流幻境新世界\pln-auto add assets\materials
git -C D:\飘流幻境新世界\pln-auto commit -m "feat: add generated alchemy material catalog"
```

## Task 3: Implement catalog and portable profile persistence

**Files:**
- Create: `app/PlnAlchemyAssistant/Models/MaterialEntry.cs`
- Create: `app/PlnAlchemyAssistant/Models/MaterialSelection.cs`
- Create: `app/PlnAlchemyAssistant/Models/AutomationOptions.cs`
- Create: `app/PlnAlchemyAssistant/Models/MaterialCatalog.cs`
- Create: `app/PlnAlchemyAssistant/Models/MaterialProfile.cs`
- Create: `app/PlnAlchemyAssistant/Models/WindowRule.cs`
- Create: `app/PlnAlchemyAssistant/Services/MaterialCatalogStore.cs`
- Create: `app/PlnAlchemyAssistant/Services/MaterialProfileStore.cs`
- Create: `app/PlnAlchemyAssistant.Tests/MaterialCatalogStoreTests.cs`
- Create: `app/PlnAlchemyAssistant.Tests/MaterialProfileStoreTests.cs`

**Interfaces:**
- Produces `MaterialCatalogStore.LoadAsync`, `Search(string, int)`, `MaterialProfileStore.LoadOrCreateAsync`, and `SaveAsync`.
- Produces immutable material/profile records consumed by the resource composer, runner, and view model.

- [ ] **Step 1: Write failing catalog and profile tests**

```csharp
[Fact]
public async Task Search_ReturnsNameMatchesSortedByNameThenItemId()
{
    var store = await MaterialCatalogStore.LoadAsync(_catalogPath, CancellationToken.None);
    var matches = store.Search("草菇", 20);
    Assert.Collection(matches, item => Assert.Equal("41005", item.ItemId));
}

[Fact]
public async Task SaveThenLoad_PreservesSeparateMainAndSecondarySelections()
{
    var store = new MaterialProfileStore(_profilePath);
    var profile = MaterialProfile.Default with
    {
        Main = [new MaterialSelection("37089", "柴薪", "7027")],
        Secondary = [new MaterialSelection("32024", "馒头", "1207")]
    };
    await store.SaveAsync(profile, CancellationToken.None);
    Assert.Equal(profile, await store.LoadOrCreateAsync(CancellationToken.None));
}
```

- [ ] **Step 2: Run the tests and confirm missing-type failures**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter "FullyQualifiedName~MaterialCatalogStoreTests|FullyQualifiedName~MaterialProfileStoreTests"
```

Expected: FAIL with missing model/store compiler errors.

- [ ] **Step 3: Implement records, loading, searching, and atomic saves**

```csharp
public sealed record MaterialEntry(string ItemId, string Name, string IconId, string IconFile, string TemplateFile);
public sealed record MaterialCatalog(int SchemaVersion, IReadOnlyDictionary<string, MaterialEntry> ByItemId);
public sealed record MaterialSelection(string ItemId, string Name, string IconId);
public sealed record AutomationOptions(double TemplateThreshold)
{
    public static readonly AutomationOptions Default = new(0.78);
}
public sealed record WindowRule(string ClassName, string Title)
{
    public static readonly WindowRule Default = new("UnityWndClass", "飘流幻境新世界");
}
public sealed record MaterialProfile(int SchemaVersion, WindowRule Window,
    AutomationOptions Automation, IReadOnlyList<MaterialSelection> Main,
    IReadOnlyList<MaterialSelection> Secondary)
{
    public static readonly MaterialProfile Default = new(1, WindowRule.Default, AutomationOptions.Default, [], []);
}
```

Use JSON `snake_case` names and indentation, yielding `automation.template_threshold`. `LoadOrCreateAsync` returns `Default` without writing when no profile exists. `SaveAsync` requires schema `1`, valid `Automation.TemplateThreshold`, distinct IDs inside each target list, and non-empty snapshot fields; writes `<profile>.tmp` then calls `File.Move(temp, profile, true)`. The profile stores only `item_id`, `name`, and `icon_id`; it never stores catalog image paths. Loading invalid JSON or schema must name the profile path in its error; missing catalog IDs are reported by the composer. `Search` does ordinal substring matching, limits to `limit`, and sorts by name then numeric item ID.

- [ ] **Step 4: Pass the store tests and commit**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.sln
git add app\PlnAlchemyAssistant app\PlnAlchemyAssistant.Tests
git commit -m "feat: persist alchemy material profiles"
```

Expected: test suite exits `0` before commit.

## Task 4: Compose a profile-specific Maa resource directory

**Files:**
- Create: `app/PlnAlchemyAssistant/Models/PreparedRuntime.cs`
- Create: `app/PlnAlchemyAssistant/Services/RuntimeResourceComposer.cs`
- Create: `app/PlnAlchemyAssistant.Tests/RuntimeResourceComposerTests.cs`

**Interfaces:**
- Consumes a `MaterialCatalog` passed to the composer constructor and produces `RuntimeResourceComposer.PrepareAsync(MaterialProfile, CancellationToken) -> Task<PreparedRuntime>`.
- `PreparedRuntime` exposes `ResourceRoot`, `MainTemplatePaths`, and `SecondaryTemplatePaths`.

- [ ] **Step 1: Write a failing composer test**

```csharp
[Fact]
public async Task Prepare_ReplacesOnlyTheFiveMaterialTemplateNodes()
{
    var prepared = await _composer.PrepareAsync(_profile, CancellationToken.None);
    var file = Path.Combine(prepared.ResourceRoot, "pipeline", "alchemy.json");
    var json = JsonNode.Parse(await File.ReadAllTextAsync(file))!.AsObject();
    Assert.Equal("alchemy/user/37089.png", json["Alchemy.MainFilled"]!["template"]![0]!.GetValue<string>());
    Assert.Equal("alchemy/user/32024.png", json["Alchemy.SubFilled"]!["template"]![0]!.GetValue<string>());
    Assert.Equal(json["Alchemy.SubFilled"]!["template"]!.ToJsonString(), json["Alchemy.RefillSub"]!["template"]!.ToJsonString());
    Assert.NotNull(json["Alchemy.ScrollSubOnce"]);
    Assert.True(File.Exists(Path.Combine(prepared.ResourceRoot, "image", "alchemy", "user", "37089.png")));
}
```

- [ ] **Step 2: Run it and confirm it fails**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~RuntimeResourceComposerTests
```

Expected: FAIL because `RuntimeResourceComposer` does not exist.

- [ ] **Step 3: Implement deterministic copy and JSON composition**

```csharp
public sealed record PreparedRuntime(string ResourceRoot,
    IReadOnlyList<string> MainTemplatePaths, IReadOnlyList<string> SecondaryTemplatePaths);

public sealed class RuntimeResourceComposer
{
    public RuntimeResourceComposer(ApplicationPaths paths, MaterialCatalog catalog);
    public Task<PreparedRuntime> PrepareAsync(MaterialProfile profile, CancellationToken cancellationToken);
    private static void ReplaceTemplateSet(JsonObject pipeline, IReadOnlyList<string> nodes,
        IReadOnlyList<string> templates, double threshold);
    private static void CopyDirectory(string source, string destination);
}
```

Validate non-empty main/secondary selections. Resolve every `MaterialSelection.ItemId` through the constructor catalog and reject a missing or mismatched snapshot before writing. Delete only `data/runtime/resource` after confirming it is below `ApplicationPaths.DataRoot`; copy `app/resources`; copy each resolved template to `image/alchemy/user/<item_id>.png`. Parse `pipeline/alchemy.json` with `JsonNode`; replace template paths and equal-length repeated threshold arrays using `profile.Automation.TemplateThreshold` only in these nodes: main `Alchemy.MainFilled`, `Alchemy.RefillMain`; secondary `Alchemy.SubFilled`, `Alchemy.RefillSub`, `Alchemy.RefillSubAfterSwipe`. Serialize indented JSON. Missing baseline/template/node throws `InvalidOperationException` before a Maa controller is created.

- [ ] **Step 4: Run composer tests and static schema validation, then commit**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~RuntimeResourceComposerTests
npx --yes @nekosu/maa-tools check
git add app\PlnAlchemyAssistant app\PlnAlchemyAssistant.Tests
git commit -m "feat: compose alchemy resources from material profile"
```

Expected: tests and Maa check exit `0`; test fixtures assert `Alchemy.DismissResult`, `Alchemy.ScrollSubOnce`, and `Alchemy.WaitRunning` were unchanged.

## Task 5: Add Maa window discovery and task execution adapters

**Files:**
- Create: `app/PlnAlchemyAssistant/Models/WindowCandidate.cs`
- Create: `app/PlnAlchemyAssistant/Models/RunState.cs`
- Create: `app/PlnAlchemyAssistant/Models/RunEvent.cs`
- Create: `app/PlnAlchemyAssistant/Services/IWindowFinder.cs`
- Create: `app/PlnAlchemyAssistant/Services/MaaWindowFinder.cs`
- Create: `app/PlnAlchemyAssistant/Services/IAlchemyRunner.cs`
- Create: `app/PlnAlchemyAssistant/Services/IMaaSession.cs`
- Create: `app/PlnAlchemyAssistant/Services/MaaAlchemyRunner.cs`
- Create: `app/PlnAlchemyAssistant/Services/MaaFrameworkSession.cs`
- Create: `app/PlnAlchemyAssistant.Tests/MaaAlchemyRunnerTests.cs`
- Modify: `app/PlnAlchemyAssistant/Program.cs`

**Interfaces:**
- `IWindowFinder.Find(WindowRule)` returns live candidates without serializing an HWND.
- `IAlchemyRunner.RunAsync(PreparedRuntime, WindowCandidate, IProgress<RunEvent>, CancellationToken)` executes only `Alchemy.EnsureUI`.
- `IAlchemyRunner.StopAsync()` is idempotent.

- [ ] **Step 1: Write failing fake-adapter state tests**

```csharp
[Fact]
public async Task RunAsync_ForwardsFocusLogAndReportsCompletion()
{
    var events = new List<RunEvent>();
    var runner = new MaaAlchemyRunner(new FakeMaaSession("已确认合成页面", RunState.Completed));
    var state = await runner.RunAsync(_runtime, _candidate, new Progress<RunEvent>(events.Add), CancellationToken.None);
    Assert.Equal(RunState.Completed, state);
    Assert.Contains(events, entry => entry.Message == "已确认合成页面");
}

[Fact]
public async Task StopAsync_CancelsTheActiveSessionOnlyOnce()
{
    var session = new FakeMaaSession("", RunState.Stopped);
    var runner = new MaaAlchemyRunner(session);
    var running = runner.RunAsync(_runtime, _candidate, null, CancellationToken.None);
    await runner.StopAsync();
    await runner.StopAsync();
    await running;
    Assert.Equal(1, session.StopCalls);
}
```

- [ ] **Step 2: Run the tests and confirm missing-type failure**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~MaaAlchemyRunnerTests
```

Expected: FAIL with missing runner/state types.

- [ ] **Step 3: Implement official Maa bindings behind testable interfaces**

```csharp
public sealed record WindowCandidate(nint Handle, string Title, string ClassName);
public enum RunState { Idle, Validating, Preparing, Connecting, Running, Stopping, Completed, Stopped, Failed }
public sealed record RunEvent(DateTimeOffset Timestamp, RunState State, string Message, string? ScreenshotPath = null);
public interface IWindowFinder { IReadOnlyList<WindowCandidate> Find(WindowRule rule); }
public interface IAlchemyRunner
{
    Task<RunState> RunAsync(PreparedRuntime runtime, WindowCandidate window,
        IProgress<RunEvent>? progress, CancellationToken cancellationToken);
    Task StopAsync();
}
public interface IMaaSession : IAsyncDisposable
{
    Task<RunState> ExecuteAsync(IProgress<RunEvent>? progress, CancellationToken cancellationToken);
    Task StopAsync();
}
```

`MaaWindowFinder` calls official `MaaToolkit.Shared.Desktop.Window.Find()`, maps results, requires exact class and title containing the saved title. `MaaAlchemyRunner` guards one active `IMaaSession` with `SemaphoreSlim`; its production session re-enumerates `DesktopWindowInfo` and resolves the selected `WindowCandidate.Handle` immediately before connecting. `MaaFrameworkSession` creates that controller with `FramePool`, `Seize`, and `LinkOption.Start`; loads `MaaResource`; creates `MaaTasker`; appends `Alchemy.EnsureUI`; relays callback focus text; and disposes all three objects in `finally`. Cancellation and `StopAsync` call the tasker stop API exactly once and await background work. Tests inject `FakeMaaSession` through the `MaaAlchemyRunner` constructor.

Before any Maa type is used, `Program` verifies `runtimes/win-x64/native` beside the EXE contains `MaaFramework.dll`, `MaaToolkit.dll`, and `MaaWin32ControlUnit.dll`, adds it to native DLL search paths, and reports an explicit startup error if any are missing.

- [ ] **Step 4: Run the adapter tests and commit**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~MaaAlchemyRunnerTests
git add app\PlnAlchemyAssistant app\PlnAlchemyAssistant.Tests
git commit -m "feat: run alchemy through MaaFramework binding"
```

Expected: tests pass with fakes only; no unit test starts a game or queries the desktop.

## Task 6: Implement material selection and execution state view model

**Files:**
- Create: `app/PlnAlchemyAssistant/ViewModels/MainWindowViewModel.cs`
- Create: `app/PlnAlchemyAssistant.Tests/MainWindowViewModelTests.cs`
- Modify: `app/PlnAlchemyAssistant/App.axaml.cs`

**Interfaces:**
- Consumes Tasks 3-5 stores/services.
- Exposes `SearchText`, `SearchResults`, `MainMaterials`, `SecondaryMaterials`, `State`, `LogLines`, `StartCommand`, `StopCommand`, `AddMainCommand`, `AddSecondaryCommand`, `RemoveMainCommand`, and `RemoveSecondaryCommand`.

- [ ] **Step 1: Write failing selection and start-gate tests**

```csharp
[Fact]
public async Task AddCommands_KeepSeparateDeduplicatedListsAndPersist()
{
    var vm = await CreateViewModelAsync();
    vm.AddMainCommand.Execute(_bun);
    vm.AddMainCommand.Execute(_bun);
    vm.AddSecondaryCommand.Execute(_bun);
    Assert.Single(vm.MainMaterials);
    Assert.Single(vm.SecondaryMaterials);
    Assert.True(vm.CanStart);
}

[Fact]
public async Task Start_WhenNoWindowMatches_FailsWithoutCallingRunner()
{
    var vm = await CreateViewModelAsync(windows: []);
    await vm.StartAsync();
    Assert.Equal(RunState.Failed, vm.State);
    Assert.Equal(0, _runner.RunCalls);
    Assert.Contains(vm.LogLines, line => line.Contains("未找到游戏窗口", StringComparison.Ordinal));
}
```

- [ ] **Step 2: Run the tests and confirm failure**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~MainWindowViewModelTests
```

Expected: FAIL because the view model is missing.

- [ ] **Step 3: Implement commands and state transition rules**

Use `ObservableObject` and `AsyncRelayCommand`. Search uses `MaterialCatalogStore.Search(value, 100)`. Add converts the selected `MaterialEntry` to `MaterialSelection`; remove operates by `MaterialSelection.ItemId`; both deduplicate only in the selected target list and persist profile after each change. `CanStart` requires non-empty main/secondary lists and state `Idle`, `Completed`, `Stopped`, or `Failed`.

`StartAsync` transitions `Validating -> Preparing -> Connecting -> Running -> Completed|Stopped|Failed`. It validates profile, composes resources, finds windows, fails on zero, opens candidate selection on multiple, saves only chosen title/class rule, then calls the runner. Append transitions and runner events to a bounded 500-line log. During preparation/connection/running/stopping every search/add/remove command has `CanExecute == false`. `StopAsync` sets `Stopping`, calls `IAlchemyRunner.StopAsync`, and lets the active start operation publish the terminal state.

- [ ] **Step 4: Pass view-model tests and commit**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.sln
git add app\PlnAlchemyAssistant app\PlnAlchemyAssistant.Tests
git commit -m "feat: manage selected materials and task state"
```

Expected: tests include automatic single-window start, two-window selection, invalid threshold, stop idempotence, and edit lock while running.

## Task 7: Build the usable Avalonia window

**Files:**
- Modify: `app/PlnAlchemyAssistant/MainWindow.axaml`
- Modify: `app/PlnAlchemyAssistant/MainWindow.axaml.cs`
- Modify: `app/PlnAlchemyAssistant/App.axaml`
- Modify: `app/PlnAlchemyAssistant/App.axaml.cs`
- Create: `app/PlnAlchemyAssistant.Tests/MainWindowBindingTests.cs`

**Interfaces:**
- Consumes Task 6 `MainWindowViewModel` as `DataContext`.
- Produces a single desktop workspace with main/sub material lists, shared search results, window candidate selection, run controls, and logs.

- [ ] **Step 1: Write a failing headless binding test**

```csharp
[Fact]
public void MainWindow_BindsSearchAndRunButtonsToViewModelCommands()
{
    var view = new MainWindow { DataContext = CreateReadyViewModel() };
    Assert.NotNull(view.FindControl<TextBox>("MaterialSearchBox"));
    Assert.NotNull(view.FindControl<Button>("StartButton"));
    Assert.NotNull(view.FindControl<Button>("StopButton"));
}
```

Add `Avalonia.Headless.XUnit` 11.4.1 to the test project and register its test application.

- [ ] **Step 2: Run the test and confirm failure**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.Tests\PlnAlchemyAssistant.Tests.csproj --filter FullyQualifiedName~MainWindowBindingTests
```

Expected: FAIL because named controls do not exist.

- [ ] **Step 3: Implement layout and interaction bindings**

Build a three-row grid: compact status/command toolbar, main material workspace, fixed-height log panel. The workspace has a shared search pane and separate fixed-height main/sub selection panes. Result rows display a 40x40 icon, name, item ID, and icon-only add-main/add-secondary buttons with tooltips. Selected rows use the same display plus an icon-only remove button. Use `ScrollViewer` for result/selection lists and a read-only scrollable log control.

Bind start to `CanStart`, stop to running/stopping, and lock material edits while running. Show a modal owned `Window` when the view model exposes multiple candidates; each row chooses one title/class candidate. No game, file, or Maa call belongs in code-behind.

- [ ] **Step 4: Run UI tests, inspect manually, and commit**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.sln
dotnet run --project app\PlnAlchemyAssistant\PlnAlchemyAssistant.csproj
git add app\PlnAlchemyAssistant app\PlnAlchemyAssistant.Tests
git commit -m "feat: add alchemy material manager UI"
```

Expected: tests pass; searching `馒头` shows an icon result, each add target remains independent, start is disabled until both lists have items, and logs remain readable after scrolling.

## Task 8: Package native Maa dependencies and portable release

**Files:**
- Create: `tools/package_alchemy_assistant.ps1`
- Create: `tools/verify_alchemy_assistant_package.ps1`
- Create: `.github/workflows/release-alchemy-assistant.yml`
- Create: `THIRD-PARTY-NOTICES.md`
- Create: `docs/zh_cn/user/alchemy-material-manager.md`
- Modify: `.gitignore`

**Interfaces:**
- `package_alchemy_assistant.ps1 -Version <version> -MaaNativeRoot <deps-bin>` writes `artifacts/飘流炼金助手-<version>-win-x64.zip`.
- `verify_alchemy_assistant_package.ps1 -PackagePath <zip>` exits zero only for a complete portable package.

- [ ] **Step 1: Write a failing package verifier**

```powershell
param([Parameter(Mandatory)] [string] $PackagePath)
$required = @('飘流炼金助手.exe', 'app/resources/pipeline/alchemy.json', 'app/materials/alchemy-materials.json', 'runtimes/win-x64/native/MaaFramework.dll', 'THIRD-PARTY-NOTICES.md', 'LICENSE')
$extract = Join-Path $env:TEMP ('pln-alchemy-package-' + [guid]::NewGuid())
Expand-Archive -LiteralPath $PackagePath -DestinationPath $extract
$missing = $required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $extract $_)) }
if ($missing) { throw "Package missing: $($missing -join ', ')" }
```

- [ ] **Step 2: Verify that an empty ZIP fails**

Run:

```powershell
Compress-Archive -Path README.md -DestinationPath $env:TEMP\empty-alchemy.zip -Force
tools\verify_alchemy_assistant_package.ps1 -PackagePath $env:TEMP\empty-alchemy.zip
```

Expected: FAIL listing missing executable and Maa native library.

- [ ] **Step 3: Implement stage-and-zip packaging**

```powershell
param([Parameter(Mandatory)] [string] $Version, [Parameter(Mandatory)] [string] $MaaNativeRoot)
$root = Split-Path -Parent $PSScriptRoot
$stage = Join-Path $root 'artifacts/stage'
$publish = Join-Path $root 'artifacts/publish'
Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
dotnet publish "$root/app/PlnAlchemyAssistant/PlnAlchemyAssistant.csproj" -c Release -r win-x64 --self-contained true -o $publish
New-Item -ItemType Directory -Path $stage -Force | Out-Null
Copy-Item "$publish/*" $stage -Recurse -Force
Copy-Item $MaaNativeRoot (Join-Path $stage 'runtimes/win-x64/native') -Recurse -Force
New-Item -ItemType Directory -Path (Join-Path $stage 'data') -Force | Out-Null
Copy-Item "$root/LICENSE", "$root/THIRD-PARTY-NOTICES.md" $stage -Force
Compress-Archive -Path "$stage/*" -DestinationPath "$root/artifacts/飘流炼金助手-$Version-win-x64.zip" -Force
```

Reject a native root without `MaaFramework.dll`, `MaaToolkit.dll`, and `MaaWin32ControlUnit.dll`. Stage no MFAAvalonia files. Add `artifacts/` to `.gitignore`. Notices name MaaFramework, Maa.Framework.Binding, Avalonia, CommunityToolkit.Mvvm, versions, source URLs, and licenses. The user guide documents unpack/start, `data/material-profile.json`, game prerequisites, logs, error screenshot path, and asset rebuild.

The workflow uses `windows-latest`, installs .NET 10, downloads MaaFramework Windows x64 as the existing workflow does, runs `dotnet test`, packages, verifies, uploads the ZIP, and attaches it to `v*` releases.

- [ ] **Step 4: Build a local package, verify it, and commit**

Run after official MaaFramework Windows x64 binaries exist at `deps/bin`:

```powershell
tools\package_alchemy_assistant.ps1 -Version 0.1.0 -MaaNativeRoot deps\bin
tools\verify_alchemy_assistant_package.ps1 -PackagePath artifacts\飘流炼金助手-0.1.0-win-x64.zip
git add tools .github/workflows/release-alchemy-assistant.yml THIRD-PARTY-NOTICES.md docs/zh_cn/user/alchemy-material-manager.md .gitignore
git commit -m "build: package portable alchemy assistant"
```

Expected: both scripts exit `0`; ZIP has external resources/assets, an empty `data/`, native Maa DLLs, notices, and no `MFAAvalonia.exe`.

## Task 9: Validate against the game and close the release checklist

**Files:**
- Modify: `docs/zh_cn/user/alchemy-material-manager.md`
- Modify: `docs/superpowers/specs/2026-07-22-alchemy-material-manager-design.md`

**Interfaces:**
- Consumes Task 8 ZIP and a real 1280x720 game composition page.
- Produces dated acceptance results and relative log/screenshot paths; it does not change Pipeline behavior.

- [ ] **Step 1: Write the manual acceptance checklist before live input**

Add unchecked entries for material search/icon display; add/remove persistence after restart; one/zero/multiple window behavior; start/stop; normal main/sub material exhaustion; failure screenshot off the composition page; and startup from a fresh extracted ZIP with no `pln-recode`, game assets, or MFAAvalonia.

- [ ] **Step 2: Run automated checks before starting the game**

Run:

```powershell
dotnet test app\PlnAlchemyAssistant.sln
npx --yes @nekosu/maa-tools check
tools\verify_alchemy_assistant_package.ps1 -PackagePath artifacts\飘流炼金助手-0.1.0-win-x64.zip
git diff --check
```

Expected: every command exits `0`. Do not send game input when one fails.

- [ ] **Step 3: Perform controlled game verification**

Open the composition page with `物等小→大` visible. Select `柴薪` and `天狗面具模` as main; select `馒头`, `草菇`, and `普通石块` as secondary. Verify search, icon display, persistence, and automatic connection of the single game window. Start and inspect UI logs for page/sort confirmation, material refill, “已点击合成开始”, running “停止” recognition, result-close retry, and normal depletion. In a separate run use UI stop; confirm it does not click the in-game stop control.

- [ ] **Step 4: Verify failure behavior and portability**

Run a fresh extraction with no `pln-recode`, game asset directory, or MFAAvalonia nearby. Start outside the composition page. Expected: `Failed` state, actionable log, and screenshot below `data/runtime/debug/on_error/`. Return to the composition page and confirm the saved profile starts without reselecting materials.

- [ ] **Step 5: Record results, final checks, and commit**

Run:

```powershell
git diff --check
git status --short
git add docs/zh_cn/user/alchemy-material-manager.md docs/superpowers/specs/2026-07-22-alchemy-material-manager-design.md
git commit -m "docs: record alchemy assistant verification"
```

Expected: no whitespace errors. Document any failed manual check as failed and do not tag a release until a focused fix passes.

## Plan Self-Review

| Specification requirement | Tasks |
| --- | --- |
| Searchable icon material library and independent main/secondary multiselect | 2, 3, 6, 7 |
| ItemData/catalog filtering and stable item IDs | 2, 3 |
| Editable portable profile and default `0.78` threshold | 3, 6 |
| Dynamic templates while retaining existing alchemy flow | 4 |
| Official direct Maa window and task execution | 5 |
| Automatic one-window connection and multiple-window selection | 5, 6, 7 |
| Start, safe stop, live logs, errors, and screenshots | 5, 6, 7, 9 |
| Portable Windows x64 ZIP without MFAAvalonia | 1, 8, 9 |
| Unit, schema, package, and game verification | 1-9 |

The plan has no deferred tasks or unresolved interfaces. Application types are defined before later tasks consume them. The material compiler remains in `pln-recode`; the tracked asset pack is the only runtime cross-project dependency.
