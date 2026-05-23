# VOC 词典工具

简洁的词典查词与背单词工具，支持快捷键、随机背单词模式

## 特性

- 查词翻译（优先匹配原词，其次匹配无空格缩写）
- Flashcard 模式：每 5 秒随机展示单词
- 无边框窗口，可拖拽，置顶切换
- 完整快捷键支持，纯黑主题

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+U` | 清空输入 |
| `Ctrl+E` | 退出程序 |
| `Ctrl+F` | 切换 Flashcard 模式 |
| `Ctrl+O` | 窗口置顶切换 |
| `Ctrl+H` | 删除最后一个词 |
| `Ctrl+L` | 聚焦查词框 |
| `Ctrl+K/J` | 横向滚动翻译 |

## 工具说明

### `merge.py` - 合并词典
将 endict 导出的 JSONL 合并为 `dict.json`
```bash
python merge.py /path/to/endict/data
```

### `convert.py` - 转换数据库
将 `dict.json` 转换为 `dict.db`
```bash
python convert.py dict.json
```

### `voc.py` - 主程序
```bash
python voc.py
```

## 打包成可执行文件

```bash
pyinstaller --onefile -w --add-data "assets;assets" voc.py
```

**⚠️ 重要：**
- `dict.db` 必须与 `voc.exe/voc.py` 放在**同一目录**下
- 程序运行时会在当前目录读取 `dict.db`，不会打包进 exe

## 文件结构

```
voc/
├── voc.py              # 主程序
├── merge.py            # 合并工具
├── convert.py          # 转换工具
├── dict.db             # 词典数据库（与exe同目录）
├── assets/             # 图标资源
│   └── icon.png
└── requirements.txt    # 依赖
```

## 依赖

```bash
pip install PySimpleGUI Pillow
```

## 数据来源

适配 [endict](https://github.com/ismartcoding/endict) 导出的 JSON 格式
