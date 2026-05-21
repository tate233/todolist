# 智能笔记管理系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个功能强大的智能笔记管理系统，支持Markdown编辑、全文搜索、知识图谱可视化等高级功能。

## 项目简介

智能笔记管理系统是一个基于Python开发的桌面应用程序，专为知识工作者设计。它提供了完整的笔记管理功能，包括Markdown编辑、分类管理、标签系统、全文搜索和知识图谱等，帮助用户高效地组织和管理个人知识库。

### 核心特性

- **📝 Markdown编辑器** - 完整支持Markdown语法，实时预览
- **🔍 智能搜索** - 基于TF-IDF的全文搜索引擎
- **🏷️ 标签系统** - 灵活的标签管理，支持多标签
- **📁 分类管理** - 按分类组织笔记，支持自定义分类
- **🕸️ 知识图谱** - 可视化笔记之间的关联关系
- **⭐ 收藏功能** - 快速标记重要笔记
- **📊 统计分析** - 字数统计、阅读时间估算
- **💾 自动保存** - 防止数据丢失
- **📤 导入导出** - 支持Markdown和文本格式

## 技术栈

- **编程语言**: Python 3.8+
- **GUI框架**: Tkinter
- **Markdown解析**: markdown, pygments
- **搜索引擎**: 自实现TF-IDF算法
- **知识图谱**: networkx
- **打包工具**: PyInstaller

## 系统要求

- Python 3.8 或更高版本
- Windows 7/10/11、macOS 10.14+、Linux (Ubuntu 18.04+)
- 至少 100MB 可用磁盘空间
- 至少 512MB 可用内存

## 安装步骤

### 方法一：使用可执行文件（推荐）

1. 下载对应平台的可执行文件
2. 双击运行即可（无需安装Python环境）

### 方法二：从源码运行

1. **克隆或下载项目**

```bash
git clone https://github.com/yourusername/smart-notes.git
cd smart-notes
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **运行程序**

```bash
python gui.py
```

## 使用说明

### 1. 创建笔记

- 点击左上角的 "+" 按钮或使用快捷键 `Ctrl+N`
- 输入笔记标题
- 在编辑器中编写内容（支持Markdown语法）
- 选择分类和添加标签
- 点击"保存"按钮或使用 `Ctrl+S` 保存

### 2. Markdown语法支持

```markdown
# 一级标题
## 二级标题

**粗体** *斜体* ~~删除线~~

- 无序列表
1. 有序列表

[链接](https://example.com)
![图片](image.png)

`代码` 或

```python
def hello():
    print("Hello World")
```

| 表格 | 列 |
|------|-----|
| 内容 | 内容 |
```

### 3. 搜索笔记

- 在左侧搜索框输入关键词
- 按回车或点击"搜索"按钮
- 系统会根据相关度排序显示结果

**搜索范围**:
- 笔记标题
- 笔记内容
- 标签

### 4. 分类管理

- 使用分类下拉框选择分类
- 可以在配置中添加自定义分类
- 支持按分类筛选笔记

### 5. 标签系统

- 在标签输入框中输入标签，用逗号分隔
- 例如: `Python, 编程, 学习`
- 标签可用于搜索和关联笔记

### 6. 收藏功能

- 勾选"收藏"复选框标记重要笔记
- 在分类下拉框选择"收藏"查看所有收藏的笔记

### 7. 导入导出

**导入笔记**:
- 文件 → 导入笔记
- 支持 .md 和 .txt 格式

**导出笔记**:
- 选择要导出的笔记
- 文件 → 导出笔记
- 选择保存位置和格式

### 8. 知识图谱

- 工具 → 知识图谱
- 查看笔记之间的关联关系
- 显示孤立笔记和社区结构

### 9. 统计信息

- 工具 → 统计信息
- 查看笔记总数、字数统计
- 分类和标签分布

## 快捷键

| 功能 | 快捷键 |
|------|--------|
| 新建笔记 | Ctrl+N |
| 保存笔记 | Ctrl+S |
| 搜索 | Ctrl+F |
| 撤销 | Ctrl+Z |
| 重做 | Ctrl+Y |

## 项目结构

```
project1/
├── config.py              # 配置管理模块
├── note_model.py          # 笔记数据模型和管理
├── markdown_parser.py     # Markdown解析器
├── search_engine.py       # 搜索引擎和知识图谱
├── gui.py                 # 图形用户界面
├── build.py               # 打包脚本
├── count_lines.py         # 代码统计工具
├── requirements.txt       # 项目依赖
├── README.md             # 项目说明
└── LICENSE               # MIT许可证
```

## 核心功能实现

### 1. 笔记管理 (note_model.py)

- **Note类**: 笔记数据模型，包含标题、内容、分类、标签等属性
- **NoteManager类**: 笔记管理器，实现CRUD操作
- 支持笔记链接和反向链接
- 提供统计分析功能

**关键方法**:
```python
create_note()      # 创建笔记
update_note()      # 更新笔记
delete_note()      # 删除笔记
search_notes()     # 搜索笔记
get_statistics()   # 获取统计信息
```

### 2. Markdown解析 (markdown_parser.py)

- 基于markdown库实现
- 支持代码高亮（pygments）
- 提取标题、链接、图片等元素
- 字数统计和阅读时间估算

**关键功能**:
```python
parse_to_html()         # 转换为HTML
extract_headings()      # 提取标题
extract_links()         # 提取链接
get_word_count()        # 字数统计
create_toc()            # 生成目录
```

### 3. 搜索引擎 (search_engine.py)

- **倒排索引**: 高效的全文搜索
- **TF-IDF算法**: 计算文档相关度
- **相关笔记推荐**: 基于内容相似度

**搜索流程**:
1. 分词和标准化
2. 构建倒排索引
3. 计算TF-IDF分数
4. 按相关度排序

### 4. 知识图谱 (search_engine.py)

- **节点**: 每篇笔记是一个节点
- **边**: 笔记之间的链接关系
- **社区发现**: 识别相关笔记群组
- **中心性分析**: 找出核心笔记

**图谱功能**:
```python
build_graph()           # 构建图谱
get_connected_notes()   # 获取关联笔记
get_central_notes()     # 获取中心笔记
get_communities()       # 社区发现
```

## 代码规范

本项目遵循以下编码规范：

- **PEP 8**: Python代码风格指南
- **类型提示**: 使用typing模块进行类型标注
- **文档字符串**: 清晰的函数和类说明
- **异常处理**: 妥善处理可能的异常
- **模块化设计**: 功能模块相互独立

## 构建可执行文件

使用PyInstaller将应用程序打包为可执行文件：

```bash
python build.py
```

生成的可执行文件位于 `dist` 目录中。

### 手动打包命令

```bash
pyinstaller --name=SmartNotes --windowed --onefile gui.py
```

## 数据存储

程序会在用户目录下创建 `.smart_notes` 文件夹：

```
.smart_notes/
├── notes.db              # 笔记数据库（JSON格式）
├── notes/                # 笔记文件目录
│   ├── xxx.md           # 单个笔记文件
│   └── ...
├── attachments/          # 附件目录
├── exports/              # 导出文件目录
├── config.json          # 配置文件
└── search_index.json    # 搜索索引
```

**位置**:
- Windows: `C:\Users\用户名\.smart_notes`
- macOS: `/Users/用户名/.smart_notes`
- Linux: `/home/用户名/.smart_notes`

## 常见问题

### Q: 如何备份笔记？

A: 笔记数据存储在 `.smart_notes` 目录中，直接复制该文件夹即可备份。

### Q: 支持哪些Markdown语法？

A: 支持标准Markdown语法，包括标题、列表、链接、图片、代码块、表格等。

### Q: 搜索不到笔记怎么办？

A: 尝试使用"工具 → 重建索引"功能重建搜索索引。

### Q: 如何导入大量笔记？

A: 可以将Markdown文件放入 `.smart_notes/notes` 目录，然后重启程序。

### Q: 支持同步到云端吗？

A: 当前版本不支持，但可以手动将 `.smart_notes` 文件夹同步到云盘。

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 开发路线图

- [x] 基础笔记管理功能
- [x] Markdown编辑和预览
- [x] 全文搜索引擎
- [x] 知识图谱
- [ ] 图表可视化
- [ ] 云端同步
- [ ] 移动端应用
- [ ] 插件系统
- [ ] 多语言支持
- [ ] 协作编辑

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页：https://github.com/yourusername/smart-notes
- 问题反馈：https://github.com/yourusername/smart-notes/issues
- 邮箱：your.email@example.com

## 致谢

感谢以下开源项目：

- [Python](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [markdown](https://python-markdown.github.io/)
- [Pygments](https://pygments.org/)
- [NetworkX](https://networkx.org/)
- [PyInstaller](https://www.pyinstaller.org/)

## 更新日志

### v1.0.0 (2024-01-01)

- 初始版本发布
- 实现基础笔记管理功能
- 支持Markdown编辑和预览
- 实现全文搜索引擎
- 添加知识图谱功能
- 提供图形用户界面

---

**注意**：本项目仅供学习和研究使用。
