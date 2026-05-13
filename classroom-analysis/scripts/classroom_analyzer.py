#!/usr/bin/env python3
"""课堂实录分析脚本。

接收 transcript_preprocessor.py 的 JSON 输出，进行深度分析：
- 问题类型检测
- 认知层级分类
- IRE/IRF 互动模式识别
- 课堂环节边界检测
- 节奏统计

用法:
    python transcript_preprocessor.py -i input.txt | python classroom_analyzer.py
    python classroom_analyzer.py --input preprocessed.json --output analysis.json
"""

import argparse
import json
import re
import sys
from typing import Optional


# ── 问题类型检测 ──────────────────────────────────────────

QUESTION_TYPE_PATTERNS = {
    "事实性回忆": [
        r"什么是", r"叫什么", r"是什么", r"有哪些", r"有几个",
        r"谁来?说说", r"还记得", r"回忆一下", r"列举", r"背诵",
        r"默写", r"定义是", r"公式是",
    ],
    "理解性解释": [
        r"怎么理解", r"什么意思", r"为什么叫", r"用自己的话",
        r"解释一下", r"说说.*含义", r"概括.*意思", r"这段.*讲了什么",
        r"意味着什么", r"说明了什么",
    ],
    "程序性操作": [
        r"怎么做", r"怎么算", r"步骤是", r"方法是",
        r"先.*再.*然后", r"如何操作", r"怎么求", r"怎么解",
    ],
    "分析性比较": [
        r"比较", r"异同", r"区别", r"联系", r"关系",
        r"为什么", r"原因", r"属于什么", r"可以分成",
        r"有什么规律", r"结构是",
    ],
    "评价性判断": [
        r"好不好", r"对不对", r"是否合理", r"优[缺点劣]",
        r"你.*觉得", r"评价", r"判断", r"同意吗",
        r"有没有道理", r"你怎么看",
    ],
    "创造性生成": [
        r"你来.*编", r"设计", r"创造", r"如果.*会怎样",
        r"假如", r"还能", r"有没有其他", r"还有.*方法",
        r"还能怎么", r"换一种",
    ],
    "追问深化": [
        r"还有吗", r"再想想", r"确定吗", r"为什么.*呢",
        r"你怎么知道", r"依据是什么", r"能证明吗",
        r"等一下", r"你再",
    ],
}


def detect_question_type(question: str) -> list[str]:
    """检测问题类型，可返回多个匹配类型。"""
    matched = []
    for qtype, patterns in QUESTION_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, question):
                matched.append(qtype)
                break
    return matched if matched else ["未分类"]


# ── 认知层级分类 ──────────────────────────────────────────

COGNITIVE_LEVEL_PATTERNS = {
    "记忆": [
        r"什么是", r"叫什么", r"有哪些", r"回忆", r"背诵",
        r"默写", r"列举", r"说出", r"记得", r"定义",
        r"公式", r"谁来说说",
    ],
    "理解": [
        r"理解", r"解释", r"含义", r"用自己的话", r"概括",
        r"说明了什么", r"意味着", r"讲了什么", r"转述",
        r"为什么叫", r"怎么理解",
    ],
    "应用": [
        r"怎么做", r"怎么算", r"解决", r"运用", r"求",
        r"解.*题", r"计算", r"完成", r"练习", r"做一做",
        r"用.*方法",
    ],
    "分析": [
        r"比较", r"异同", r"区别", r"联系", r"为什么",
        r"原因", r"规律", r"结构", r"关系", r"推理",
        r"证明", r"可以分成", r"属于",
    ],
    "评价": [
        r"好不好", r"对不对", r"合理", r"优劣", r"评价",
        r"判断", r"同意", r"怎么看", r"有没有道理",
        r"是否正确", r"是否严谨",
    ],
    "创造": [
        r"编", r"设计", r"创造", r"其他方法", r"换一种",
        r"如果.*会怎样", r"猜想", r"提出", r"自编",
        r"创作", r"表演",
    ],
}


def classify_cognitive_level(text: str) -> str:
    """根据关键词对文本进行认知层级分类。返回最高匹配层级。"""
    level_order = ["记忆", "理解", "应用", "分析", "评价", "创造"]
    matched_level = "记忆"  # 默认

    for level in level_order:
        patterns = COGNITIVE_LEVEL_PATTERNS[level]
        for pattern in patterns:
            if re.search(pattern, text):
                matched_level = level
                break

    return matched_level


def classify_question_cognitive(question: str) -> str:
    """专门对教师问题进行认知层级分类。"""
    return classify_cognitive_level(question)


# ── IRE/IRF 互动模式识别 ──────────────────────────────────

def detect_ire_patterns(turns: list[dict]) -> list[dict]:
    """识别 IRE (Initiation-Response-Evaluation) 和 IRF 模式。

    IRE: 教师提问 → 学生回答 → 教师评价（封闭）
    IRF: 教师提问 → 学生回答 → 教师反馈/追问（开放，促进学习）
    """
    patterns = []
    i = 0

    while i < len(turns) - 2:
        t1 = turns[i]
        t2 = turns[i + 1]
        t3 = turns[i + 2] if i + 2 < len(turns) else None

        if t1['role'] == 'teacher' and t2['role'] == 'student' and t3 and t3['role'] == 'teacher':
            has_question = '？' in t1['text'] or '?' in t1['text']

            if has_question:
                # 判断第三个话轮是封闭评价还是开放反馈
                eval_keywords = ['对', '好', '不错', '正确', '很好', '非常好', '是的',
                                 '回答得很好', '回答正确', '答对了', '嗯']
                feedback_keywords = ['为什么', '还有', '再想想', '怎么', '能否',
                                     '确定吗', '你再', '等一下', '那', '如果']

                t3_text = t3['text']
                is_eval = any(kw in t3_text for kw in eval_keywords)
                is_feedback = any(kw in t3_text for kw in feedback_keywords)

                # 排除既是评价又是追问的情况（如"很好，还有吗？"）
                if is_eval and is_feedback:
                    pattern_type = "IRF"
                elif is_eval and not is_feedback:
                    pattern_type = "IRE"
                elif is_feedback:
                    pattern_type = "IRF"
                else:
                    pattern_type = "IRE"

                q_type = detect_question_type(t1['text'])
                cog_level = classify_question_cognitive(t1['text'])

                patterns.append({
                    "start_turn": i,
                    "initiation": {
                        "turn_id": t1['turn_id'],
                        "text": t1['text'],
                        "question_type": q_type,
                        "cognitive_level": cog_level,
                    },
                    "response": {
                        "turn_id": t2['turn_id'],
                        "text": t2['text'],
                        "raw_role": t2.get('raw_role', ''),
                    },
                    "feedback": {
                        "turn_id": t3['turn_id'],
                        "text": t3['text'],
                    },
                    "pattern_type": pattern_type,
                    "segment": t1.get('segment', ''),
                })

        i += 1

    return patterns


# ── 课堂环节边界检测 ──────────────────────────────────────

SEGMENT_MARKERS = {
    "导入": [r"导入", r"引入", r"开始", r"今天我们", r"同学们.*上课"],
    "复习/先验激活": [r"回忆", r"复习", r"上节课", r"之前.*学过", r"还记得"],
    "新知讲授": [r"新[课知]", r"学习.*新", r"今天.*学习", r"请大家看"],
    "探究活动": [r"探究", r"操作", r"动手", r"实验", r"折[纸叠]", r"观察", r"发现"],
    "讨论交流": [r"讨论", r"交流", r"小组", r"同桌", r"四人.*组", r"分享"],
    "练习应用": [r"练习", r"做一做", r"试一试", r"完成.*题", r"巩固"],
    "展示汇报": [r"汇报", r"展示", r"谁来.*说", r"请.*同学.*讲"],
    "总结归纳": [r"总结", r"归纳", r"回顾", r"今天.*学了", r"有什么收获"],
    "作业布置": [r"作业", r"课后", r"回去", r"留作.*思考"],
}


def detect_segment_boundaries(turns: list[dict]) -> list[dict]:
    """基于教师发言中的标记词检测环节边界。"""
    segments = []
    current_segment = None
    segment_start = 0

    for i, turn in enumerate(turns):
        if turn['role'] != 'teacher':
            continue

        text = turn['text']
        detected_type = None

        for seg_type, markers in SEGMENT_MARKERS.items():
            for marker in markers:
                if re.search(marker, text):
                    detected_type = seg_type
                    break
            if detected_type:
                break

        if detected_type and detected_type != current_segment:
            if current_segment:
                segments.append({
                    "segment_type": current_segment,
                    "start_turn": segment_start,
                    "end_turn": i - 1,
                    "turn_count": i - segment_start,
                    "start_timestamp": turns[segment_start].get('timestamp'),
                    "end_timestamp": turns[i - 1].get('timestamp') if i > 0 else None,
                })
            current_segment = detected_type
            segment_start = i

    # 最后一个环节
    if current_segment:
        segments.append({
            "segment_type": current_segment,
            "start_turn": segment_start,
            "end_turn": len(turns) - 1,
            "turn_count": len(turns) - segment_start,
            "start_timestamp": turns[segment_start].get('timestamp'),
            "end_timestamp": turns[-1].get('timestamp'),
        })

    return segments


# ── 互动质量统计 ──────────────────────────────────────────

def compute_interaction_stats(ire_patterns: list[dict]) -> dict:
    """计算互动模式的统计信息。"""
    if not ire_patterns:
        return {
            "total_triads": 0,
            "ire_count": 0,
            "irf_count": 0,
            "ire_ratio": 0,
            "cognitive_distribution": {},
        }

    ire_count = sum(1 for p in ire_patterns if p['pattern_type'] == 'IRE')
    irf_count = sum(1 for p in ire_patterns if p['pattern_type'] == 'IRF')

    # 认知层级分布
    cog_dist = {}
    for p in ire_patterns:
        level = p['initiation']['cognitive_level']
        cog_dist[level] = cog_dist.get(level, 0) + 1

    return {
        "total_triads": len(ire_patterns),
        "ire_count": ire_count,
        "irf_count": irf_count,
        "ire_ratio": round(ire_count / len(ire_patterns), 2) if ire_patterns else 0,
        "irf_ratio": round(irf_count / len(ire_patterns), 2) if ire_patterns else 0,
        "cognitive_distribution": cog_dist,
    }


# ── 问题链分析 ──────────────────────────────────────────

def analyze_question_chain(turns: list[dict]) -> dict:
    """分析教师问题链的特征。"""
    teacher_questions = []
    for t in turns:
        if t['role'] == 'teacher' and ('？' in t['text'] or '?' in t['text']):
            q_type = detect_question_type(t['text'])
            cog_level = classify_question_cognitive(t['text'])
            teacher_questions.append({
                "turn_id": t['turn_id'],
                "text": t['text'],
                "question_type": q_type,
                "cognitive_level": cog_level,
                "segment": t.get('segment', ''),
            })

    if not teacher_questions:
        return {"total_questions": 0, "type_distribution": {}, "level_distribution": {}}

    # 类型分布
    type_dist = {}
    for q in teacher_questions:
        for qt in q['question_type']:
            type_dist[qt] = type_dist.get(qt, 0) + 1

    # 认知层级分布
    level_dist = {}
    for q in teacher_questions:
        level = q['cognitive_level']
        level_dist[level] = level_dist.get(level, 0) + 1

    # 最高层级
    level_order = ["记忆", "理解", "应用", "分析", "评价", "创造"]
    max_level = "记忆"
    for q in teacher_questions:
        idx = level_order.index(q['cognitive_level']) if q['cognitive_level'] in level_order else 0
        if idx >= level_order.index(max_level):
            max_level = q['cognitive_level']

    return {
        "total_questions": len(teacher_questions),
        "questions": teacher_questions,
        "type_distribution": type_dist,
        "level_distribution": level_dist,
        "max_cognitive_level": max_level,
    }


# ── 节奏分析 ──────────────────────────────────────────

def analyze_pacing(turns: list[dict], segments: list[dict]) -> dict:
    """分析课堂节奏（需要时间戳信息）。"""
    has_timestamps = any(t.get('timestamp') is not None for t in turns)

    if not has_timestamps:
        # 无时间戳：分析轮次密度
        return {
            "has_timestamps": False,
            "total_turns": len(turns),
            "segments_turn_based": [
                {
                    "type": s['segment_type'],
                    "turn_count": s['turn_count'],
                    "density": "高" if s['turn_count'] > 10 else "中" if s['turn_count'] > 5 else "低",
                }
                for s in segments
            ],
        }

    # 有时间戳：分析时间分配
    segment_durations = []
    for s in segments:
        if s['start_timestamp'] is not None and s['end_timestamp'] is not None:
            duration = s['end_timestamp'] - s['start_timestamp']
            segment_durations.append({
                "type": s['segment_type'],
                "duration_seconds": duration,
                "turn_count": s['turn_count'],
            })

    total_time = sum(sd['duration_seconds'] for sd in segment_durations) if segment_durations else 0

    return {
        "has_timestamps": True,
        "total_duration_seconds": total_time,
        "segment_durations": segment_durations,
    }


# ── 主分析流程 ──────────────────────────────────────────

def analyze(preprocessed: dict) -> dict:
    """主分析函数。"""
    turns = preprocessed.get('turns', [])
    stats = preprocessed.get('stats', {})

    # 1. 互动模式识别
    ire_patterns = detect_ire_patterns(turns)
    interaction_stats = compute_interaction_stats(ire_patterns)

    # 2. 环节边界检测
    segments = detect_segment_boundaries(turns)

    # 3. 问题链分析
    question_chain = analyze_question_chain(turns)

    # 4. 节奏分析
    pacing = analyze_pacing(turns, segments)

    # 5. 认知层级分布（按轮次）
    turn_levels = []
    for t in turns:
        if t['role'] == 'teacher':
            level = classify_cognitive_level(t['text'])
            turn_levels.append({
                "turn_id": t['turn_id'],
                "cognitive_level": level,
                "text_preview": t['text'][:50],
            })

    # 汇总认知层级
    level_summary = {}
    for tl in turn_levels:
        level = tl['cognitive_level']
        level_summary[level] = level_summary.get(level, 0) + 1

    return {
        "input_format": preprocessed.get('format_detected', 'unknown'),
        "basic_stats": stats,
        "interaction": {
            "ire_patterns": ire_patterns,
            "stats": interaction_stats,
        },
        "segments": segments,
        "question_chain": question_chain,
        "pacing": pacing,
        "cognitive_levels": {
            "turn_levels": turn_levels,
            "summary": level_summary,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description='课堂实录深度分析：问题类型、认知层级、互动模式、环节检测'
    )
    parser.add_argument('--input', '-i', help='预处理 JSON 文件路径（默认读取 stdin）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认输出到 stdout）')
    parser.add_argument('--pretty', action='store_true', default=True,
                        help='格式化 JSON 输出（默认开启）')
    args = parser.parse_args()

    # 读取输入
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # 分析
    result = analyze(data)

    # 输出
    indent = 2 if args.pretty else None
    output = json.dumps(result, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"已输出到 {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
