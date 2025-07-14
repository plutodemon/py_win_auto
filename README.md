# Windows UI 自动化工具

一个基于 pywinauto 的 Windows 应用程序自动化工具，支持窗口查找、控件定位和自动化操作。

## 特性

- 🔍 **窗口查找**：根据应用名称查找窗口
- 🎯 **控件定位**：精确定位UI控件并获取坐标
- 🖱️ **自动点击**：支持自动点击操作
- 📊 **JSON输出**：结构化的JSON格式输出，便于程序集成
- 🪟 **无界面模式**：支持后台运行，不显示控制台窗口
- 🔧 **命令行接口**：完整的命令行参数支持

## 安装与构建

### 开发环境

克隆项目

```bash
git clone https://github.com/plutodemon/py_win_auto.git
cd py_win_auto
```

安装依赖

```bash
poetry install
```

运行开发版本

```bash
poetry run python src/py_win_auto/auto.py --help
```

### 构建可执行文件

修改 `pyproject.toml` 中的 `tool.poetry-pyinstaller-plugin.scripts` 部分 构建不同版本

- `auto` - GUI版本

```toml
"auto" = { source = "src/py_win_auto/auto.py", type = "onefile", bundle = false, icon = "app.ico", windowed = true }
```

- `auto_sh` - 命令行版本

```toml
"auto_sh" = { source = "src/py_win_auto/auto.py", type = "onefile", bundle = false, icon = "app.ico", windowed = false }
```

构建exe文件

```bash
poetry build
```

## 使用方法

### 基本语法

```bash
auto_sh.exe --app <应用名称> [选项]
```

### 命令行参数

| 参数            | 类型     | 必需 | 说明             |
|---------------|--------|----|----------------|
| `--app`       | string | ✅  | 应用窗口名称（支持模糊匹配） |
| `--control`   | string | ❌  | 控件名称           |
| `--type`      | string | ❌  | 控件类型           |
| `--check`     | flag   | ❌  | 输出窗口控件树结构      |
| `--click`     | flag   | ❌  | 执行点击操作         |
| `--dump-file` | string | ❌  | 将窗口树结构保存到指定文件  |
| `-h, --help`  | flag   | ❌  | 显示帮助信息         |

### 使用示例

#### 1. 查看窗口结构

```bash
# 查看记事本窗口的控件树
auto_sh.exe --app "记事本" --check

# 将控件树保存到文件
auto_sh.exe --app "记事本" --check --dump-file "notepad_tree.txt"
```

#### 2. 定位控件

```bash
# 查找按钮控件的位置
auto_sh.exe --app "计算器" --control "等于" --type "Button"
```

#### 3. 自动点击

```bash
# 自动点击指定控件
auto_sh.exe --app "计算器" --control "1" --type "Button" --click
```

## JSON 输出格式

golang版本

```golang
type AutoResult struct {
	Success      bool   `json:"success"`
	Error        string `json:"error,omitempty"`
	ControlTitle string `json:"control_title,omitempty"`
	ControlType  string `json:"control_type,omitempty"`
	Position     struct {
		Left   int `json:"left"`
		Top    int `json:"top"`
		Right  int `json:"right"`
		Bottom int `json:"bottom"`
	} `json:"position,omitempty"`
	Center struct {
		X int `json:"x"`
		Y int `json:"y"`
	} `json:"center,omitempty"`
	Clicked      bool   `json:"clicked,omitempty"`
	Action       string `json:"action,omitempty"`
	AppName      string `json:"app_name,omitempty"`
	WindowsFound int    `json:"windows_found,omitempty"`
	DumpFile     string `json:"dump_file,omitempty"`
}
```