# -*- coding: utf-8 -*-
"""
vault-doctor：笔记库结构体检 + 知识地图生成

═══ 它要解决的真问题 ═══
我手写的根索引 mermaid 图只有 5 个节点（索引 + 4 个分组），
但库里有 21 篇笔记、几十条前置依赖。
地图和真实结构差了 4 倍 —— 这不是"难看"，是"失真"。

═══ 它做的事 ═══
1. 通读全库，看清真实结构（← 这正是原来的工作流里缺掉的那一步）
2. 找出漂移：孤儿笔记、断链、空文件
3. 把散落在各索引页表格里的"前置关系"汇总成一张真正的 mermaid 知识地图
4. 用固定的输出契约落盘

═══ Prompt 对照实验（见下方 PROMPT_MODE）═══
同一个任务，只改 system prompt 的约束强度，各跑一次：

              限定步骤版            只给目标版
  第 1 轮      scan_vault            scan_vault
  消息轨迹     2 → 4 → 10 → 12       2 → 4 → 10 → 12
  第 2 轮      一轮并列 5 次读笔记     一轮并列 5 次读笔记
  轮数         4                     4

结论：**过程零差异，差异全在表达。**

  · 限定版用嵌套小圆点，只给目标版换成了四列表格（笔记 / 字数 / 应归入 / 理由）
  · 限定版没有收尾观察，只给目标版主动补了一段整体健康度
  · 对同一篇笔记的归类判断，只给目标版更准

推断：那句"不要自由发挥"本意只管**步骤**，但它的副作用溢出了 ——
连**表达**一起压住了。而过程之所以纹丝不动，是因为工具自身的
`description` 里还拽着引导（scan_vault 写着"必须"先调用它）。

  → 提示词无法真正"清空"引导，每一个 description 都在下指令。

═══ 安全 ═══
所有产物只写进 vault 下的 _auto/ 子目录，绝不触碰你现有的任何笔记。
"""

import json
import re
from pathlib import Path

from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, VAULT_PATH

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

VAULT = Path(VAULT_PATH)
OUTPUT_DIR = VAULT / "_auto"        # 唯一的写入区
LINK_RE = re.compile(r"\[\[([^\]|#]+)")


# ═══════════════ 工具本体 ═══════════════

def iter_notes():
    """列出库里的 .md，排除我们自己生成的 _auto 目录。"""
    return sorted(p for p in VAULT.rglob("*.md") if "_auto" not in p.parts)


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def scan_vault():
    """通读全库，返回一份结构快照。后面所有判断都基于它。"""
    if not VAULT.exists():
        return f"错误：找不到笔记目录 {VAULT}"

    notes = iter_notes()
    names = {p.stem for p in notes}

    lines = [f"笔记总数：{len(notes)}", "", "【全部笔记】标题 | 字数"]
    links = {}
    empties = []
    for p in notes:
        text = read_text(p)
        if not text.strip():
            empties.append(p.stem)
        links[p.stem] = {m.strip().split("/")[-1] for m in LINK_RE.findall(text)}
        lines.append(f"- {p.stem} | {len(text)} 字")

    lines += ["", "【出链关系】谁 -> 链到了谁（出链多的通常是索引页）"]
    for src, tgts in sorted(links.items(), key=lambda x: -len(x[1])):
        if tgts:
            lines.append(f"- {src} -> {', '.join(sorted(tgts))}")

    referenced = set()
    for t in links.values():
        referenced |= t

    lines += ["", "【孤儿笔记】没有任何笔记链接到它"]
    lines += [f"- {n}" for n in sorted(names - referenced)] or ["（无）"]

    broken = sorted({l for ts in links.values() for l in ts if l not in names})
    lines += ["", "【断链】链向不存在的笔记"]
    lines += [f"- {b}" for b in broken] or ["（无）"]

    lines += ["", "【空文件】"]
    lines += [f"- {e}" for e in empties] or ["（无）"]

    return "\n".join(lines)


def read_note(filename):
    """读一篇笔记的全文（截断到 4000 字）。主要用来读现有索引页，提取前置关系。"""
    target = Path(filename).stem
    for p in iter_notes():
        if p.stem == target:
            return f"《{p.stem}》全文：\n{read_text(p)[:4000]}"
    return f"没有找到《{filename}》，请用 scan_vault 里的准确标题。"


def write_report(filename, content):
    """把产物写进 _auto/ 目录。这是本工具唯一有副作用的操作。"""
    if not filename.endswith(".md"):
        filename += ".md"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / filename
    target.write_text(content, encoding="utf-8")
    return f"已写入：{target}"


def execute_tool(name, args):
    """模型说要调哪个工具，我们就去调哪个。"""
    if name == "scan_vault":
        return scan_vault()
    if name == "read_note":
        return read_note(args["filename"])
    if name == "write_report":
        return write_report(args["filename"], args["content"])
    return "未知工具：" + name


# ═══════════════ 工具清单 ═══════════════

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_vault",
            "description": (
                "扫描整个 Obsidian 笔记库，返回结构快照：全部笔记清单及字数、"
                "笔记之间的链接关系、孤儿笔记、断链、空文件。"
                "任何关于笔记库结构的任务，都必须先调用它。无参数。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_note",
            "description": (
                "读取一篇笔记的完整内容。用来查看现有索引页里的"
                "『笔记列表』表格，从中提取每篇笔记的前置依赖关系。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "笔记标题，例如 '🏗️ 类'（不用加 .md）",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_report",
            "description": "把最终产物写成一篇新笔记，保存到笔记库的 _auto/ 目录下。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "文件名，例如 'C++ 知识地图.md'"},
                    "content": {"type": "string", "description": "完整的 Markdown 正文"},
                },
                "required": ["filename", "content"],
            },
        },
    },
]


# ═══════════════ 系统提示词：两版 ═══════════════
#
# 两版唯一的区别就是下面这两段。任务目标、输出结构、铁律，三样完全相同。
# 也就是说：这是一个只改了「约束强度」的单变量对照实验。

PROMPT_STRICT = """你是笔记库结构维护助手。工作流程是固定的，不要自由发挥：

1. 先调用 scan_vault，看清全库真实结构。
2. 调用 read_note 读取各索引页（如「C++ 学习索引」「🏗️ 类」等），
   从它们表格里的『前置』一列，提取出笔记之间的真实依赖关系。
3. 最后调用 write_report 写入产物，文件名固定用「C++ 知识地图.md」。

产物必须严格按下面的结构组织，章节一个不多一个不少：

## 一、结构体检
- 孤儿笔记：逐条列出，并说明它应该归入哪个分组、理由是什么
- 断链：（没有就写"无"）
- 空文件：（没有就写"无"）

## 二、知识地图
一个 mermaid 代码块，开头写 ```mermaid 和 graph TD。
必须画出真实的笔记层级和前置依赖，不要只画几个节点。

## 三、建议
三条以内，每条都要指向具体的笔记，不要泛泛而谈。

铁律：只使用 scan_vault 和 read_note 返回的真实数据，
绝对不要编造不存在的笔记名。"""


PROMPT_LOOSE = """你是笔记库结构维护助手。

你的任务：检查用户的 Obsidian 笔记库结构是否健康，并生成一张真实反映笔记之间关系的知识地图。

你有工具可以用。先做什么、用什么、用几轮，你自己决定。

产物必须严格按下面的结构组织，章节一个不多一个不少：

## 一、结构体检
- 孤儿笔记：逐条列出，并说明它应该归入哪个分组、理由是什么
- 断链：（没有就写"无"）
- 空文件：（没有就写"无"）

## 二、知识地图
一个 mermaid 代码块，开头写 ```mermaid 和 graph TD。
必须画出真实的笔记层级和前置依赖，不要只画几个节点。

## 三、建议
三条以内，每条都要指向具体的笔记，不要泛泛而谈。

做完之后，把产物用 write_report 写成一篇笔记，文件名用「C++ 知识地图.md」。

铁律：只使用工具返回的真实数据，绝对不要编造不存在的笔记名。"""


# 实验开关：改这里就能切换两版，不用动别的代码
PROMPT_MODE = "loose"          # "strict" 或 "loose"

SYSTEM_PROMPT = PROMPT_STRICT if PROMPT_MODE == "strict" else PROMPT_LOOSE


# ═══════════════ 循环 ═══════════════

def run_agent(question, max_rounds=12):
    """核心循环。这个 for，就是 Agent 的心脏。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for round_no in range(1, max_rounds + 1):
        print(f"\n{'─' * 62}")
        print(f"第 {round_no} 轮：把 {len(messages)} 条消息发给模型")

        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print("\n任务结束。模型的收尾说明：\n")
            print(msg.content)
            return msg.content

        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            print(f"  → 调用 {name}  参数={list(args.keys()) or '无'}")

            result = execute_tool(name, args)
            preview = result[:80].replace("\n", " ")
            print(f"  → 返回：{preview}……")

            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )

    return "轮次用完了。"


if __name__ == "__main__":
    print(f"[PROMPT_MODE = {PROMPT_MODE}]")
    run_agent("帮我做一次完整的笔记库结构体检，并生成一张真实的知识地图。")
