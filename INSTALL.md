# 安装和部署指南

## 系统要求

- Python 3.12 或更高版本
- Windows 7/10/11、macOS 10.14+、Linux (Ubuntu 18.04+)
- 至少 100MB 可用磁盘空间

## 安装依赖

### 步骤1：安装Python依赖库

```bash
pip install -r requirements.txt
# 或者使用uv来管理依赖的下载与安装
# 例如 uv pip install -r requirements
# 或者 uv sync 按照pyproject.toml来同步
```

### 步骤2：运行程序

```bash
python gui.py
```

## 构建可执行文件

### 自动构建（推荐）

```bash
python build.py
```

按提示输入 `y` 开始构建。

### 手动构建

如果自动构建失败，可以使用以下命令手动构建：

**Windows:**
```bash
pyinstaller --name=SmartNotes --windowed --onefile --clean --noconfirm gui.py
```

**macOS/Linux:**
```bash
pyinstaller --name=SmartNotes --onefile --clean --noconfirm gui.py
```

构建完成后，可执行文件位于 `dist` 目录中。

## 常见问题

### Q: 提示缺少模块怎么办？

A: 确保已安装所有依赖库：
```bash
pip install markdown pygments networkx pillow matplotlib
```

Linux环境下，当运行后提示libtcl.so缺失时，可尝试通过安装动态链接库来解决问题。
以Debian环境为例，采用下列命令安装：

```bash
sudo apt install tk9.0 tcl9.0 libtcl9.0
```

### Q: 打包失败怎么办？

A: 
1. 确保PyInstaller已安装：`pip install pyinstaller`
2. 尝试手动打包命令
3. 检查Python版本是否为3.12+

### Q: 程序无法启动？

A: 
1. 检查是否安装了所有依赖
2. 尝试在命令行运行查看错误信息
3. 确保Python版本兼容

## 数据存储位置

程序数据存储在用户目录下：

- **Windows**: `C:\Users\用户名\.smart_notes`
- **macOS**: `/Users/用户名/.smart_notes`
- **Linux**: `/home/用户名/.smart_notes`

## 卸载

1. 删除程序文件
2. 删除数据目录 `.smart_notes`
3. 卸载Python依赖（可选）

## 技术支持

如遇问题，请查看：
- README.md 文档
- 项目GitHub Issues页面
