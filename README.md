# VOC 词典工具

一个简洁的词典查词与背单词工具，支持快捷键、随机背单词模式。

## 特性

- 查词翻译（优先匹配原词，其次匹配无空格缩写）
- Flashcard 模式：每 5 秒随机展示一个单词
- 无边框窗口，可拖拽，置顶切换
- 完整快捷键支持
- 纯黑主题，简约视觉

## 工具集

### 1. `merge.py` —— 词典合并工具

感谢 **https://github.com/ismartcoding/endict** 提供的词库

将 `endict` 仓库导出的 JSON 文件合并为统一的 `dict.json`。

**支持格式示例（每行一个 JSON）：**
```json
{"word": "hello", "sw": "hello", "translation": ["你好"]}
{"word": "world", "sw": "world", "translation": ["世界"]}
```

**用法：**
```bash
python merge.py /path/to/endict/data
```

### 2. `convert.py` —— 数据库转换工具

将合并后的 `dict.json` 转换为 SQLite 数据库（`dict.db`）。

**JSON 格式：**
```json
{
  "hello": {"sw": "hello", "translation": "你好"},
  "world": {"sw": "world", "translation": "世界"}
}
```

**用法：**
```bash
python convert.py dict.json
```

## 主程序 `voc.py`

### 快捷键

| 快捷键       | 功能               |
| ------------ | ------------------ |
| `Ctrl+U`     | 清空输入           |
| `Ctrl+E`     | 退出程序           |
| `Ctrl+F`     | 切换 Flashcard 模式 |
| `Ctrl+O`     | 窗口置顶切换       |
| `Ctrl+H`     | 删除输入框最后一个词 |
| `Ctrl+L`     | 聚焦查词框         |
| `Ctrl+K/J`   | 横向滚动翻译结果   |

### Flashcard 模式

点击工具栏的 `◇`（或按 `Ctrl+F`）进入该模式：

- 查词框变为只读
- 每 5 秒自动随机展示一个单词及其翻译
- 再次点击退出，恢复正常查词

## 快速开始

1. 准备符合上述格式的词典数据
2. 运行合并与转换脚本生成 `dict.db`
3. 执行主程序：
   ```bash
   python voc.py
   ```

## 数据来源

本工具适配 [endict](https://github.com/ismartcoding/endict) 导出的 JSON 词典格式（每行包含 `word`、`sw`、`translation` 字段）。你也可以按照示例格式自行准备词典。

## 环境要求

- Python 3.7+
- 依赖：`PySimpleGUI`, `Pillow`, `pysqlite3`

```bash
pip install -r requirements.txt
```

## 文件说明

- `voc.py`：主程序
- `merge.py`：JSONL → JSON 合并工具
- `convert.py`：JSON → SQLite 转换工具
- `dict.db`：最终使用的数据库文件
- `assets/`：图标资源目录
