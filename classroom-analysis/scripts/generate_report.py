#!/usr/bin/env python3
"""课堂分析报告生成脚本。

接收 classroom_analyzer.py 的 JSON 输出，生成 Markdown 分析报告骨架。
根据可用数据自动跳过证据不足的段落，避免空表格。

用法:
    python transcript_preprocessor.py -i input.txt | python classroom_analyzer.py | python generate_report.py
    python generate_report.py --input analysis.json --output report.md
    python generate_report.py --input analysis.json --mode full|brief|targeted --target 5,6,7
"""

import argparse
import json
import sys
from datetime import datetime


def seconds_to_display(seconds: int) -> str:
    """将秒数转换为 MM:SS 显示格式。"""
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def get_cognitive_level_display(level: str) -> str:
    """返回认知层级的中文显示。"""
    return level if level else "未识别"


# ── 报告各段生成函数 ──────────────────────────────────────

def section_1_basic(analysis: dict) -> str:
    """第 1 段：课堂基本判断。"""
    stats = analysis.get('basic_stats', {})
    segments = analysis.get('segments', [])
    question_chain = analysis.get('question_chain', {})

    # 从环节推断核心任务
    core_task = "材料未显示"
    if segments:
        # 取第一个非导入环节作为核心学习任务
        for seg in segments:
            if seg['segment_type'] not in ('导入', '复习/先验激活', '作业布置'):
                core_task = seg['segment_type']
                break

    duration = stats.get('estimated_duration_display', '材料未显示')

    lines = [
        "## 1. 课堂基本判断\n",
        "| 维度 | 判断 | 依据 | 不确定性 |",
        "|---|---|---|---|",
        f"| 学科 | （待填写） | | |",
        f"| 学段/对象 | （待填写） | | |",
        f"| 课型 | （待填写） | | |",
        f"| 总时长 | {duration} | {'基于时间戳估算' if stats.get('estimated_duration_seconds') else '材料未显示'} | |",
        f"| 核心学习任务 | （待填写） | 环节结构可供参考 | |",
    ]
    return '\n'.join(lines)


def section_2_segments(analysis: dict) -> str:
    """第 2 段：课堂环节切分。"""
    segments = analysis.get('segments', [])

    if not segments:
        return "## 2. 课堂环节切分\n\n> 材料中未检测到明确的环节划分标记。建议根据教学逻辑手动切分。\n"

    lines = [
        "## 2. 课堂环节切分\n",
        "| 时间段 | 环节 | 教师主要行为 | 学生主要行为 | 学习任务 | 学习证据 | 初步判断 |",
        "|---|---|---|---|---|---|---|",
    ]

    for seg in segments:
        ts = ""
        if seg.get('start_timestamp') is not None:
            start = seconds_to_display(seg['start_timestamp'])
            end = seconds_to_display(seg['end_timestamp']) if seg.get('end_timestamp') else "?"
            ts = f"{start}-{end}"

        lines.append(
            f"| {ts} | {seg['segment_type']} | （待填写） | （待填写） | "
            f"（待填写） | （待填写） | 轮次数：{seg['turn_count']} |"
        )

    return '\n'.join(lines)


def section_3_teacher_behavior(analysis: dict) -> str:
    """第 3 段：教师行为分析。"""
    stats = analysis.get('basic_stats', {})
    question_chain = analysis.get('question_chain', {})

    lines = [
        "## 3. 教师行为分析\n",
        "### 3.1 教师行为分布\n",
        "| 行为类型 | 典型时间/片段 | 具体表现 | 对学习的作用 | 可能风险 |",
        "|---|---|---|---|---|",
    ]

    # 从分析数据中提取可识别的行为
    q_dist = question_chain.get('type_distribution', {})
    if q_dist:
        for qtype, count in q_dist.items():
            lines.append(f"| 提问（{qtype}） | 检测到 {count} 次 | （待补充具体表现） | （待分析） | |")

    lines.append(f"| （其他行为待补充） | | | | |")
    lines.append("")
    lines.append("### 3.2 关键教学行为解读\n")
    lines.append("- 证据：")
    lines.append("- 分析：")
    lines.append("- 教研价值：")

    return '\n'.join(lines)


def section_4_student_behavior(analysis: dict) -> str:
    """第 4 段：学生学习行为分析。"""
    lines = [
        "## 4. 学生学习行为分析\n",
        "| 学生行为 | 时间/片段 | 学生实际做了什么 | 学习意义 | 证据强度 |",
        "|---|---|---|---|---|",
        "| （待填写） | | | | |",
    ]
    return '\n'.join(lines)


def section_5_question_chain(analysis: dict) -> str:
    """第 5 段：问题链与互动分析。"""
    question_chain = analysis.get('question_chain', {})
    interaction = analysis.get('interaction', {})
    ire_patterns = interaction.get('ire_patterns', [])
    interaction_stats = interaction.get('stats', {})

    lines = [
        "## 5. 问题链与互动分析\n",
        "### 5.1 问题链梳理\n",
        "| 时间/片段 | 教师问题 | 学生回应 | 问题类型 | 认知层级 | 追问/反馈 | 质量判断 |",
        "|---|---|---|---|---|---|---|",
    ]

    questions = question_chain.get('questions', [])
    for q in questions[:15]:  # 限制输出条目
        q_types = '、'.join(q['question_type'])
        cog = q['cognitive_level']
        # 尝试找到对应的 IRE 模式
        feedback_text = ""
        for pattern in ire_patterns:
            if pattern['initiation']['turn_id'] == q['turn_id']:
                feedback_text = pattern['feedback']['text'][:30]
                break
        lines.append(
            f"| 轮次 {q['turn_id']} | {q['text'][:40]}{'...' if len(q['text']) > 40 else ''} | "
            f"（待补充） | {q_types} | {cog} | {feedback_text or '（待补充）'} | |"
        )

    # 互动反馈诊断
    lines.append("")
    lines.append("### 5.2 互动反馈诊断\n")

    if interaction_stats.get('total_triads', 0) > 0:
        ire_count = interaction_stats['ire_count']
        irf_count = interaction_stats['irf_count']
        total = interaction_stats['total_triads']

        lines.append(f"**检测到 {total} 组 IRE/IRF 互动三元组**：")
        lines.append(f"- IRE（封闭式评价）：{ire_count} 次（{interaction_stats.get('ire_ratio', 0):.0%}）")
        lines.append(f"- IRF（开放式反馈/追问）：{irf_count} 次（{interaction_stats.get('irf_ratio', 0):.0%}）")
        lines.append("")

        if ire_count > irf_count:
            lines.append("> 互动以 IRE 为主，教师反馈多为封闭式评价，建议增加追问和开放式反馈。")
        elif irf_count > ire_count:
            lines.append("> 互动以 IRF 为主，教师反馈具有开放性，有利于学生深层思考。")
        else:
            lines.append("> IRE 和 IRF 比例相当，互动模式较为均衡。")
    else:
        lines.append("- 能够接住学生回答的片段：（待补充）")
        lines.append("- 未充分展开学生回答的片段：（待补充）")

    lines.append("")
    lines.append("- 问题链的递进性判断：（待分析）")
    lines.append("- 可改进的追问示例：（待补充）")

    return '\n'.join(lines)


def section_6_cognitive_levels(analysis: dict) -> str:
    """第 6 段：认知层级分析。"""
    cog = analysis.get('cognitive_levels', {})
    summary = cog.get('summary', {})
    segments = analysis.get('segments', [])

    lines = [
        "## 6. 认知层级分析\n",
        "| 环节/任务 | 主要认知层级 | 依据 | 是否出现层级递进 | 可提升空间 |",
        "|---|---|---|---|---|",
    ]

    if segments:
        level_order = ["记忆", "理解", "应用", "分析", "评价", "创造"]
        prev_level_idx = -1
        for seg in segments:
            # 粗略映射环节类型到认知层级
            seg_level_map = {
                "导入": "记忆",
                "复习/先验激活": "记忆",
                "新知讲授": "理解",
                "探究活动": "分析",
                "讨论交流": "分析",
                "练习应用": "应用",
                "展示汇报": "评价",
                "总结归纳": "理解",
                "作业布置": "应用",
            }
            inferred = seg_level_map.get(seg['segment_type'], "待判断")
            level_idx = level_order.index(inferred) if inferred in level_order else -1
            progression = ""
            if level_idx > prev_level_idx >= 0:
                progression = "是（递进）"
            elif level_idx == prev_level_idx:
                progression = "否（持平）"
            elif level_idx >= 0 and prev_level_idx >= 0:
                progression = "否（下降）"
            prev_level_idx = level_idx

            lines.append(
                f"| {seg['segment_type']} | {inferred}（推测） | 环节类型推断 | {progression} | （待分析） |"
            )
    else:
        lines.append("| （待补充） | | | | |")

    # 总体判断
    lines.append("")
    if summary:
        lines.append("**教师提问认知层级分布**：")
        for level in ["记忆", "理解", "应用", "分析", "评价", "创造"]:
            count = summary.get(level, 0)
            if count > 0:
                bar = "█" * count
                lines.append(f"- {level}：{count} 次 {bar}")
    lines.append("")
    lines.append("总体判断：（待结合学段和课型分析）")

    return '\n'.join(lines)


def section_7_learning_evidence(analysis: dict) -> str:
    """第 7 段：学习证据分析。"""
    lines = [
        "## 7. 学习证据分析\n",
        "| 证据类型 | 时间/片段 | 具体证据 | 证据强度 | 可支持的学习判断 | 局限 |",
        "|---|---|---|---|---|---|",
    ]
    for etype in ["理解", "应用", "迁移", "表达", "修正", "产出"]:
        lines.append(f"| {etype} | | | | | |")

    return '\n'.join(lines)


def section_8_pacing(analysis: dict) -> str:
    """第 8 段：课堂节奏分析。"""
    pacing = analysis.get('pacing', {})

    lines = [
        "## 8. 课堂节奏分析\n",
    ]

    if pacing.get('has_timestamps'):
        lines.append("| 时间段 | 时长 | 教学/学习活动 | 时间使用判断 | 依据 | 调整建议 |")
        lines.append("|---|---:|---|---|---|---|")
        for sd in pacing.get('segment_durations', []):
            dur = seconds_to_display(sd['duration_seconds'])
            lines.append(
                f"| {sd['type']} | {dur} | （待填写） | （待判断） | | |"
            )
    else:
        lines.append("| 时间段 | 时长 | 教学/学习活动 | 时间使用判断 | 依据 | 调整建议 |")
        lines.append("|---|---:|---|---|---|---|")
        for seg_p in pacing.get('segments_turn_based', []):
            lines.append(
                f"| {seg_p['type']} | — | （待填写） | 轮次密度：{seg_p['density']} | | |"
            )

    lines.append("")
    lines.append("总体节奏判断：（待分析）")

    return '\n'.join(lines)


def section_9_alignment(analysis: dict) -> str:
    """第 9 段：目标—活动—评价一致性分析。"""
    lines = [
        "## 9. 目标—活动—评价一致性分析\n",
        "| 目标/核心任务 | 对应活动 | 对应评价或学习证据 | 一致性判断 | 问题与原因 |",
        "|---|---|---|---|---|",
        "| （待填写） | | | | |",
    ]
    return '\n'.join(lines)


def section_10_highlights(analysis: dict) -> str:
    """第 10 段：课堂亮点。"""
    lines = [
        "## 10. 课堂亮点\n",
        "### 亮点一：",
        "- 证据：",
        "- 分析：",
        "- 可提炼的教研观点：",
        "",
        "### 亮点二：",
        "- 证据：",
        "- 分析：",
        "- 可提炼的教研观点：",
    ]
    return '\n'.join(lines)


def section_11_problems(analysis: dict) -> str:
    """第 11 段：问题诊断。"""
    interaction = analysis.get('interaction', {})
    stats = interaction.get('stats', {})

    lines = [
        "## 11. 问题诊断\n",
    ]

    # 如果 IRE 比例高，自动提示
    if stats.get('ire_ratio', 0) > 0.6 and stats.get('total_triads', 0) > 3:
        lines.append("### 问题一（自动检测）：互动以封闭式评价为主")
        lines.append(f"- 证据：{stats['total_triads']} 组互动三元组中，{stats['ire_count']} 组为 IRE 模式（{stats['ire_ratio']:.0%}）")
        lines.append("- 诊断：教师反馈多为判断正误的封闭式评价，较少利用学生回答推进深层学习")
        lines.append('- 对学习的影响：学生可能形成"猜测教师期望答案"的习惯，而非独立思考')
        lines.append("- 可研究化表述：IRE 主导的课堂互动模式对学生深层思维发展的影响")
        lines.append("")

    lines.append("### 问题（待补充）：")
    lines.append("- 证据：")
    lines.append("- 诊断：")
    lines.append("- 对学习的影响：")
    lines.append("- 可研究化表述：")

    return '\n'.join(lines)


def section_12_improvements(analysis: dict) -> str:
    """第 12 段：教学改进建议。"""
    lines = [
        "## 12. 教学改进建议\n",
        "| 针对问题 | 改进建议 | 可直接使用的课堂话语/任务设计 | 预期学习证据 |",
        "|---|---|---|---|",
        "| （待填写） | | | |",
    ]
    return '\n'.join(lines)


def section_13_topics(analysis: dict) -> str:
    """第 13 段：可研发文章选题。"""
    lines = [
        "## 13. 可研发文章选题\n",
        "| 选题 | 问题意识 | 核心论点 | 课堂证据基础 | 研究角度 | 文章类型 |",
        "|---|---|---|---|---|---|",
        "| （待填写） | | | | | |",
    ]
    return '\n'.join(lines)


def section_14_outline(analysis: dict) -> str:
    """第 14 段：推荐文章大纲。"""
    lines = [
        "## 14. 推荐文章大纲\n",
        "### 推荐题目\n",
        "### 中心论点\n",
        "### 一、问题提出：课堂现象与研究价值\n",
        "### 二、课堂证据：关键片段与问题呈现\n",
        "### 三、机制分析：任务、问题链、反馈或证据的内在关系\n",
        "### 四、改进设计：教学策略与课堂实施路径\n",
        "### 五、评价方式：如何收集新的学习证据\n",
        "### 六、结论：可迁移的教研启示\n",
    ]
    return '\n'.join(lines)


def section_15_limitations(analysis: dict) -> str:
    """第 15 段：分析限制说明。"""
    stats = analysis.get('basic_stats', {})
    pacing = analysis.get('pacing', {})

    lines = [
        "## 15. 分析限制说明\n",
        "- 材料缺失项：",
    ]

    # 自动检测缺失项
    missing = []
    if not pacing.get('has_timestamps'):
        missing.append("时间戳信息（无法精确分析课堂节奏）")
    if stats.get('student_turns', 0) == 0:
        missing.append("学生发言记录")
    if stats.get('narrative_turns', 0) > 0:
        missing.append("部分材料为叙述性笔记，非原始对话（影响对话分析精度）")

    for item in missing:
        lines.append(f"  - {item}")

    if not missing:
        lines.append("  - （待根据实际情况补充）")

    lines.append("")
    lines.append("- 因缺失而不能确认的判断：（待补充）")
    lines.append("- 建议补充的证据：（待补充）")

    return '\n'.join(lines)


# ── 主生成流程 ──────────────────────────────────────────

SECTIONS = {
    1: section_1_basic,
    2: section_2_segments,
    3: section_3_teacher_behavior,
    4: section_4_student_behavior,
    5: section_5_question_chain,
    6: section_6_cognitive_levels,
    7: section_7_learning_evidence,
    8: section_8_pacing,
    9: section_9_alignment,
    10: section_10_highlights,
    11: section_11_problems,
    12: section_12_improvements,
    13: section_13_topics,
    14: section_14_outline,
    15: section_15_limitations,
}


def generate_report(analysis: dict, mode: str = "full", targets: list[int] = None) -> str:
    """生成 Markdown 分析报告。

    参数:
        analysis: classroom_analyzer.py 的输出
        mode: "full"（全部 15 段）、"brief"（仅 1,2,5,6,11,15）、"targeted"（指定段）
        targets: targeted 模式下指定的段号列表
    """
    title = "# 课堂实录分析报告\n"
    meta = f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 模式：{mode}\n"

    if mode == "brief":
        section_ids = [1, 2, 5, 6, 11, 15]
    elif mode == "targeted" and targets:
        section_ids = [s for s in targets if s in SECTIONS]
        # 片段分析也包含基础信息
        if 1 not in section_ids:
            section_ids.insert(0, 1)
    else:
        section_ids = list(SECTIONS.keys())

    parts = [title, meta, "---\n"]

    for sid in section_ids:
        section_func = SECTIONS[sid]
        parts.append(section_func(analysis))
        parts.append("")

    parts.append("---\n")
    parts.append('*本报告骨架由分析脚本自动生成，标注"待填写"的部分需结合课堂文本证据补充。*')

    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(
        description='生成课堂分析报告 Markdown 骨架'
    )
    parser.add_argument('--input', '-i', help='分析 JSON 文件路径（默认读取 stdin）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认输出到 stdout）')
    parser.add_argument('--mode', choices=['full', 'brief', 'targeted'], default='full',
                        help='报告模式：full=全部 15 段, brief=精简 6 段, targeted=指定段')
    parser.add_argument('--target', type=str, default=None,
                        help='targeted 模式下指定段号，逗号分隔，如 "5,6,7"')
    args = parser.parse_args()

    # 读取输入
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # 解析 target
    targets = None
    if args.target:
        try:
            targets = [int(x.strip()) for x in args.target.split(',')]
        except ValueError:
            print("错误：--target 参数格式应为逗号分隔的数字，如 '5,6,7'", file=sys.stderr)
            sys.exit(1)

    # 生成报告
    report = generate_report(data, mode=args.mode, targets=targets)

    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"已输出到 {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == '__main__':
    main()
