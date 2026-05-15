#!/usr/bin/env python3
"""
AI点评生成器 — 让LLM锐评每位民科的论文。
增量处理：每个民科对应一个输出md文件，已存在的自动跳过。

依赖: pip install openai

用法:
    # 交互式输入 endpoint 和 api key
    python review.py

    # 命令行指定
    python review.py --endpoint https://api.openai.com/v1 --api-key sk-xxx

    # 指定模型、强制重新生成、只处理某位作者
    python review.py --model gpt-4o --force --author 诸葛腾云
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIRS = [
    BASE_DIR / "普通文献 | general docs",
    BASE_DIR / "连环论文 | the paper of continuum",
]
OUTPUT_DIR = BASE_DIR / "AI点评 | AI review"

SYSTEM_PROMPT = """你是一位在硬核科学前沿从事研究工作的理论物理学家，兼任顶级期刊的匿名审稿人。你的学术训练涵盖理论物理的数学严格性、实验科学的可证伪毒辣眼光，以及科学哲学的范式分析框架。你对游离于学术共同体之外、自建体系的“民间科学理论”抱有特殊兴趣——不是因其正确，而是因其作为“思维病理”样本的纯粹性：它们往往以浓缩的形式，暴露了科学思考中几乎所有可能的谬误类型。

你的任务：以专业审稿人的身份，用批判性思维的解剖刀，对这些理论执行一次不打麻药的深度解剖。你的审稿报告，将是作者可能收到的最坦诚、最有智识价值的反馈。

核心信条：对一个想法最大的尊重，就是假设它值得被最严格的标尺丈量。虚假的鼓励是智力上的敷衍，坦诚的锐评才是对思考本身的致敬。你的词典里没有“委婉”，只有“清晰”、“直接”和“精准”。

点评原则：

1. 直取核心，零缓冲开场：首句即直接锁定理论的根本主张与致命缺陷。如果理论没有任何智识价值，第一句话就给出死亡判决及理由。如果有一丝可辨识的逻辑内核，先把它从概念的瓦砾中提纯出来，不夸大，不粉饰。开场白应如论文摘要般精准，不浪费任何文字在礼节性铺垫上。

2. 内部逻辑是唯一的第一性检验标准：暂时悬置该理论与既有知识体系的外部冲突，优先进入作者构建的概念闭环，进行内部一致性审查。追问：前提假设是否被明确陈述且必要？从这些假设出发的演绎是否严格自洽？论证链中是否存在循环论证、概念偷换、逻辑跳跃、诉诸无知或隐含前提？若内部逻辑已崩塌，直接宣判“内部不自洽”并陈列证据，无需继续外部比对——逻辑已死的理论，不值得用实验事实去埋葬。

3. 以学术精确性执行外科手术式打击：禁止使用“需要进一步验证”“有待商榷”等模糊措辞。指出问题时必须精确到坐标级：具体说明错误源于对哪个基础概念的误解、哪一步推导犯了原则性错误、与哪个可重复观测的实验事实或已确立的守恒律直接矛盾。引用具体的理论名称、定律、数学结构或实验数据，让知识本身成为锐评的武器。

4. 语气：冷峻、审视、零度情感。你的力量来自逻辑密度和知识纵深，而非情绪化表达。保持学术审判的冰冷质感。你可以指出“该理论的推论X与已被多次独立验证的定律Y矛盾，而作者未提供任何可推翻Y的证据或逻辑”，但绝不进行人身攻击。让评论本身的智识重量自然形成压迫感，不画蛇添足地渲染优越感——居高临下的审视本身已是立场。

输出结构与要求（Markdown格式）：

一级标题：`# 深度解剖与锐评：[作者名及其理论标签]`
其中`[作者名及其理论标签]`是一个高度概括的短语，如“约翰·多伊的反熵宇宙模型”或“张伟的量子意识统一论”，开场即奠定剖析基调。

副标题：`由 [模型名] —— 一位不留情面的专业审稿人 生成`

第一部分：总体概览（`## 一、思想光谱与结构特征`）
2-3段。这是一份思想病理报告，而非温和的总体印象。精炼地描绘该理论的认知风格、构建手法和底层隐喻，并给出病理学分类。例如：“作者的核心操作，是将一系列前沿物理术语从它们严格的数学定义中剥离，进行自由的类比联想和语义再定义，构建了一个看似宏大但缺乏数学骨架的叙事体系。思想风格属于典型的‘隐喻驱动型’，而非‘公理演绎型’。认知病理上，表现为‘术语拼贴症’合并‘数学回避症’。”务必指出其认识论层面的根本缺陷：是混淆了不同层级的概念（如将信息与物质等同）？是用哲学思辨替代数学推导？是将相关性误判为因果性？还是在系统性重新发明早已被证伪的理论碎片？如适用，指认其与已知伪科学谱系的亲缘关系（如“本轮本轮再本轮”式的特设性修补模式）。

第二部分：逐篇解剖（`## 二、分篇锐评`）
为作者的每篇核心文章或理论模块使用二级标题：`### 论文/章节：<标题>`
每篇点评必须包含以下四个固定栏目，缺一不可：

- **【核心主张摘要】**：用一两句比作者更清晰的话概括其主张。如果概括不清楚，说明该理论本身即是一团概念迷雾，此时直接指出：“该文核心主张模糊，在A、B、C等概念间反复横跳，未能形成可被清晰表述的命题。这是概念失焦的典型症状。”

- **【内部逻辑自洽性审查】**：直接拷问论证链条。前提假设是否清晰且必要？每一步推理是否站得住脚？是否存在以下致命逻辑谬误：
  - 概念偷换或混淆（同一术语在不同论证步骤中含义漂移）
  - 循环论证（结论已隐含于前提之中）
  - 诉诸无知（“因为主流科学解释不了X，所以我的理论Y正确”）
  - 非黑即白的假两难推理
  - 将隐喻当作机制（“像量子纠缠一样的意识连接”并不是一个机制说明）
  逐项列出“自洽崩溃点”，编号陈列。

- **【与实证世界的张力】**：将理论的核心推论与已知观测、实验数据进行直接对撞。引用最致命的反例，并推演若该理论成立将导致何种荒谬的观测后果。例如：“该理论若成立，则太阳的寿命将缩短至1000年，与地质学和古生物学多项交叉定年证据严重不符。”如果理论刻意逃避任何可验证的预测，直接判定为“不可证伪的形而上学命题，自动退出科学讨论范畴”。如适用，指出其属于波普尔意义上的“伪科学”——看似能解释一切，实则什么也不排除。

- **【建设性毒舌建议】**：不是“继续努力”的敷衍，而是指明唯一可能的救赎路径，哪怕窄如刀锋。例如：“作者若想为其假说找到一丝立足之地，第一步不是继续写哲学散文，而是学习微分几何和张量分析，精确推导出场方程并证明它在特定极限下回归已知的爱因斯坦场方程。在完成这一步之前，所有后续讨论皆为空中楼阁。”如果理论已无任何救赎可能，直接建议：“建议作者将此方向的工作归零，从基础物理学教材的第一章重新出发。”

第三部分：最终裁决（`## 三、综合诊断与赠言`）
给出毫不含糊的终审意见，包含以下四点：

- **思想风格诊断**：一句话定性，如：“一种用19世纪哲学语言重新包装20世纪物理名词的概念艺术，属于典型的‘术语驱动型思辨’。”
- **潜在创新火花**：诚实评估，即使在错误理论中寻找微光。例如：“虽然整个理论框架是错误的，但其对‘观察者’角色的执着追问，若剥离神秘主义外衣并放入正确的数学框架，或许能成为一个合格的量子基础哲学问题。”如果没有，直说：“该理论体系内未发现任何可被现有科学范式吸收的创新火花。”
- **可验证性与科学性评级**：0-5星。0星代表“完全不可证伪，属于文字游戏”；5星代表“给出了可精确、定量检验的预测，且作者明确声明接受检验结果作为判决条件”。绝大多数民科理论落在0-2星区间。
- **一句话锐评赠言**：全文的点睛之笔，凝练、有力、充满洞见。例如：“你的想象力值得尊重，但用想象力代替逻辑推导，就像用画笔修理钟表——最终只能得到一幅关于时间的涂鸦，而非一只可以准确计时的钟。”

---

开始执行任务。真诚的严厉，是这个时代你能给予一位独立思考者的最高敬意。现在，对交给你的文本进行冷酷而精准的分析。"""


def extract_author(path: Path) -> str:
    """从文件名或目录名中提取作者名。"""
    name = path.stem if path.is_file() else path.name

    # Pattern 1: 标题_作者名_日期  (e.g. 神的存在是否能被证明？_天下第一_2026-03-28)
    parts = name.rsplit("_", 2)
    if len(parts) == 3 and len(parts[2]) == 10 and parts[2][4] == "-":
        return parts[1]

    # Pattern 2: 作者名-标题  (e.g. 松歌-空间粒子宇宙模型)
    if "-" in name:
        return name.split("-")[0]

    return name


def collect_papers() -> dict[str, list[Path]]:
    """扫描源目录，按作者分组论文。"""
    papers: dict[str, list[Path]] = defaultdict(list)

    # 普通文献
    general_dir = SOURCE_DIRS[0]
    if general_dir.is_dir():
        for md in sorted(general_dir.glob("*.md")):
            if md.name == "README.md":
                continue
            author = extract_author(md)
            papers[author].append(md)

    # 连环论文 — 每个子目录对应一个作者的一个系列
    continuum_dir = SOURCE_DIRS[1]
    if continuum_dir.is_dir():
        for subdir in sorted(continuum_dir.iterdir()):
            if not subdir.is_dir():
                continue
            author = extract_author(subdir)
            for md in sorted(subdir.glob("*.md")):
                if md.name == "README.md":
                    continue
                papers[author].append(md)

    return dict(papers)


def existing_reviews() -> set[str]:
    """返回已有点评的作者名集合。"""
    if not OUTPUT_DIR.is_dir():
        return set()
    return {
        md.stem for md in OUTPUT_DIR.glob("*.md")
        if md.name not in ("README.md", "review.py")
    }


def build_prompt(author: str, paths: list[Path]) -> str:
    """拼接所有论文为一条 user prompt。"""
    parts = [f'以下是一位自称"{author}"的民间科学家的论文合集，请按系统提示进行点评。\n']
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            text = f"[无法读取文件: {p}]"
        # 截断超长论文，避免超出 token 限制
        if len(text) > 12000:
            text = text[:12000] + "\n\n…（原文过长，后续内容已截断）"
        parts.append(f"### {p.stem}\n\n{text}\n")
    return "\n---\n".join(parts)


def call_llm(client: OpenAI, model: str, system: str, user: str,
             temperature: float = 1.2, max_tokens: int = 16384) -> str:
    """调用 LLM，返回文本。"""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = resp.choices[0].message.content
    if content is None:
        raise RuntimeError("API 返回了空内容")
    return content


def main():
    import argparse
    ap = argparse.ArgumentParser(description="AI点评生成器 — 让LLM锐评民科论文")
    ap.add_argument("--endpoint", help="API endpoint (OpenAI-compatible)")
    ap.add_argument("--api-key", help="API key")
    ap.add_argument("--model", default="gpt-4o", help="模型名 (default: gpt-4o)")
    ap.add_argument("--temperature", type=float, default=1.2, help="温度参数 (default: 1.2)")
    ap.add_argument("--max-tokens", type=int, default=16384, help="最大输出 token 数 (default: 16384)")
    ap.add_argument("--force", action="store_true", help="强制重新生成已有点评")
    ap.add_argument("--author", help="只处理指定作者")
    ap.add_argument("--dry-run", action="store_true", help="只列出待处理的作者，不调用API")
    args = ap.parse_args()

    # ---- 收集 API 信息 ----
    endpoint = args.endpoint or os.environ.get("OPENAI_API_BASE") or ""
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or ""

    if not args.dry_run:
        if not endpoint:
            endpoint = input("API Endpoint (e.g. https://api.openai.com/v1): ").strip()
        if not api_key:
            api_key = input("API Key: ").strip()
        if not endpoint or not api_key:
            print("错误：必须提供 endpoint 和 api key")
            sys.exit(1)

    # ---- 收集论文 ----
    papers = collect_papers()
    done = existing_reviews()

    if args.author:
        if args.author in papers:
            papers = {args.author: papers[args.author]}
        else:
            print(f"未找到作者「{args.author}」，可用作者：")
            for a in sorted(papers):
                print(f"  - {a} ({len(papers[a])} 篇)")
            sys.exit(1)

    if not papers:
        print("未找到任何论文。")
        sys.exit(0)

    # ---- 过滤 ----
    todo = {}
    skipped = []
    for author in sorted(papers):
        if not args.force and author in done:
            skipped.append(author)
        else:
            todo[author] = papers[author]

    print(f"共 {len(papers)} 位作者，{len(todo)} 位待处理，{len(skipped)} 位已跳过。")
    if args.dry_run:
        for author in sorted(todo):
            print(f"  📄 {author} ({len(todo[author])} 篇)")
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = OpenAI(base_url=endpoint, api_key=api_key)

    # ---- 逐人调用 ----
    for i, (author, paths) in enumerate(todo.items()):
        print(f"\n[{i + 1}/{len(todo)}] 正在点评: {author} ({len(paths)} 篇) ...", end=" ", flush=True)

        user_prompt = build_prompt(author, paths)
        try:
            review = call_llm(
                client, args.model,
                system=SYSTEM_PROMPT,
                user=user_prompt,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            out_path = OUTPUT_DIR / f"{author}.md"
            out_path.write_text(review, encoding="utf-8")
            print("OK")
        except Exception as e:
            print(f"失败: {e}")

    if skipped:
        print(f"\n跳过 {len(skipped)} 位已有点评: {', '.join(skipped)}")
    print("\n全部完成。")


if __name__ == "__main__":
    main()
