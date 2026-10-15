# vault-doctor · 笔记库结构体检 Agent

检查 Obsidian 笔记库的结构健康度，找出**掉队**和**断链**的笔记，并自动生成一张真实反映笔记关系的知识地图。

一次运行约 30 秒。

---

## 一、它有什么用

如果你的笔记库是下面这样，它就有用：

| 你的情况 | 它能帮你做什么 |
|---|---|
| 笔记越来越多，索引页开始跟不上 | 列出**没被任何索引收录**的笔记 |
| 不确定有没有链接指向了不存在的笔记 | 扫出全部**断链** |
| 建了占位笔记，忘了往里写东西 | 找出**空文件** |
| 想看看自己的知识结构长什么样 | 生成一张 mermaid 知识地图，可直接在 Obsidian 里渲染 |
| 手工维护知识图太累、还老是忘 | 每次跑一遍，图就是最新的 |

**一句话：它替你抬头看一眼全局。**

> 它不替代你的笔记软件。它解决的是"**没有任何环节负责通读全库**"这件事——手工维护的索引页会漏，因为它只在你想起它的时候才更新。

---

## 二、它输出什么

### 产物文件

```
<你的笔记库>/_auto/C++ 知识地图.md
```

- 写入位置固定在笔记库下的 `_auto/` 子目录
- **不会修改、不会删除你任何现有笔记**
- 文件名可以改（见「七、参数」）

### 产物内容

固定三节，章节一个不多一个不少。

**① 结构体检** —— 用表格逐条列出发现的问题：

| 笔记 | 字数 | 应归入 | 理由 |
|---|---|---|---|
| `C++ Rule of Five 详解` | 0 字 | 🏗️ 类 | 三/五法则讲的五个特殊成员函数，是「构造函数与析构函数」的延伸 |
| `C++ 分层算法练习题` | 8131 字 | 顶层（与索引并列） | 跨主题综合练习，不属于任何单一分组 |

**② 知识地图** —— 一个 `mermaid graph TD` 代码块：

- **实线** = 笔记里已经存在的链接
- **虚线** = 模型建议新增的归属关系

**③ 建议** —— 三条以内，每条都指向具体笔记，不说空话。

### 终端输出

运行时会在终端打印完整执行轨迹，方便确认它到底干了什么：

```
第 1 轮：把 2 条消息发给模型
  → 调用 scan_vault  参数=无
  → 返回：笔记总数：21  【全部笔记】标题 | 字数 …

第 2 轮：把 4 条消息发给模型
  → 调用 read_note  参数=['filename']
  → 返回：《C++ 学习索引》全文：…

第 3 轮：把 10 条消息发给模型
  → 调用 write_report  参数=['filename', 'content']
  → 返回：已写入：E:\Obsidian\notes\_auto\C++ 知识地图.md……

第 4 轮：把 12 条消息发给模型
任务结束。
```

---

## 三、它是怎么判断的

| 检查项 | 判定规则 |
|---|---|
| **孤儿笔记** | 全库里没有任何笔记通过 `[[链接]]` 指向它 |
| **断链** | 笔记里的 `[[xxx]]` 指向的文件不存在 |
| **空文件** | `.md` 内容为空，或只有空白字符 |

> **注意**：孤儿 ≠ 没用。一篇笔记没被链接，可能只是你还没给它加入口。

---

## 四、安装

**要求**：Python 3.8 以上（开发环境为 Python 3.14）

```bash
pip install openai
```

**只需要这一个依赖。** 目录遍历、双链解析全部用标准库完成。

---

## 五、配置

复制模板，再填自己的值：

```bash
cp config.example.py config.py         # Windows: copy config.example.py config.py
```

打开 `config.py`，填四处：

```python
API_KEY    = "sk-你的密钥"                # https://platform.deepseek.com 申请
BASE_URL   = "https://api.deepseek.com"   # 换别家模型改这里
MODEL      = "deepseek-chat"
VAULT_PATH = r"E:\Obsidian\notes"         # 你的笔记库根目录
```

> `VAULT_PATH` 填**笔记库根目录**——就是能看到 `.obsidian` 文件夹的那一层。
>
> `config.py` 已在 `.gitignore` 中排除，不会被提交。

---

## 六、使用

```bash
python vault_doctor.py
```

没有命令行参数。跑完去笔记库的 `_auto/` 目录看产物。

想换一个提问，改文件最后这行：

```python
run_agent("帮我做一次完整的笔记库结构体检，并生成一张真实的知识地图。")
```

---

## 七、参数

| 位置 | 参数 | 说明 |
|---|---|---|
| 文件顶部 | `PROMPT_MODE` | `"loose"`（默认）或 `"strict"` —— 见附录 B |
| 文件底部 | `run_agent(question, max_rounds=12)` | `max_rounds` 是循环轮数上限，防止模型无限索要工具 |
| `read_note` 内部 | 单篇截断 4000 字 | 防止上下文溢出 |

---

## 八、目录结构

```
vault-doctor/
├── vault_doctor.py       主程序（工具定义 + 循环 + 两版 system prompt）
├── config.example.py     配置模板，复制为 config.py 后填值
├── .gitignore            排除 config.py 与运行产物
└── README.md             本文件
```

---

## 九、常见问题

**`UnicodeEncodeError: 'ascii' codec can't encode characters in position 10-16`**

`config.py` 里的 API Key 还是占位符，没换成真的。报错里 `position 10-16` 指向的正是 `Bearer sk-在这里粘贴你的key` 这串字符中文字符的位置——数一下就能定位。

**`can't open file '...\vault_doctor.py': No such file or directory`**

当前目录不对。先切到项目目录再运行：

```bash
cd path/to/vault-doctor
python vault_doctor.py
```

**`ModuleNotFoundError: No module named 'config'`**

没建 `config.py`。见「五、配置」。

**跑出来笔记数是 0**

`VAULT_PATH` 填错了，或者指向的不是笔记库根目录。

**模型一直要工具、停不下来**

把 `max_rounds` 调小，或把 `PROMPT_MODE` 换成 `"strict"`。

---

## 十、安全说明

- **只读你的笔记**。全项目唯一的写入操作是往 `<笔记库>/_auto/` 写产物
- **不会修改或删除任何现有笔记**
- API Key 只存在本地 `config.py`，该文件已被 `.gitignore` 排除
- 模型只能通过三个工具接触你的文件：全库扫描、读单篇、写产物——**没有删除能力**

---

## 十一、它是怎么工作的

一个标准的 tool-calling 循环：

```
用户提问
   ↓
把消息 + 工具清单发给模型
   ↓
模型自主决定调用哪个工具（可能一次调好几个）
   ↓
本地执行工具，结果作为 role="tool" 的消息回灌
   ↓
模型拿着结果再决定一次 …… 直到它不再需要工具
   ↓
输出最终结果
```

**三个工具：**

| 工具 | 类型 | 作用 |
|---|---|---|
| `scan_vault()` | 确定性 | 全库扫描，返回结构快照 |
| `read_note(title)` | 确定性 | 读单篇笔记全文 |
| `write_report(name, content)` | 有副作用 | 写入产物（限定在 `_auto/` 目录内） |

---
---
