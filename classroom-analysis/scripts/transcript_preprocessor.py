#!/usr/bin/env python3
"""课堂实录预处理脚本。

自动检测输入格式（时间戳对话、师生配对、听课笔记），
归一化为统一的 JSON 结构，提取基础统计信息。

用法:
    python transcript_preprocessor.py --input transcript.txt
    python transcript_preprocessor.py --input transcript.txt --output preprocessed.json
    cat transcript.txt | python transcript_preprocessor.py
"""

import argparse
import json
import re
import sys
from typing import Optional


# ── 格式检测 ──────────────────────────────────────────────

def detect_format(text: str) -> str:
    """检测输入文本的格式类型。

    返回值:
        "timestamped"  — 带时间戳的对话（如 【00:00-02:30】...）
        "speaker_turn" — 师/生标签的对话（如 师：... 生：...）
        "mixed_notes"  — 混合格式或听课笔记（含叙述性文字）
    """
    timestamp_pattern = re.compile(r'[【\[]\d{1,2}:\d{2}')
    speaker_pattern = re.compile(r'(?:^|\n)\s*(?:师|教师|老师|T|生|学生|S)\s*[：:]\s*\S')

    has_timestamp = bool(timestamp_pattern.search(text))
    has_speaker = bool(speaker_pattern.search(text))

    if has_timestamp and has_speaker:
        return "timestamped"
    elif has_speaker:
        return "speaker_turn"
    elif has_timestamp:
        return "timestamped"
    else:
        return "mixed_notes"


# ── 时间戳解析 ─────────────────────────────────────────────

def parse_timestamp(ts_str: str) -> Optional[int]:
    """将时间字符串转换为秒数。支持 MM:SS 和 HH:MM:SS。"""
    ts_str = ts_str.strip().strip('【】[]')
    parts = ts_str.split(':')
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None
    return None


def seconds_to_timestamp(seconds: int) -> str:
    """将秒数转换为 MM:SS 格式。"""
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


# ── 文本清洗 ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    """清洗原始文本：去除多余空白、统一分隔符。"""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── 角色识别 ──────────────────────────────────────────────

def normalize_role(raw_role: str) -> str:
    """将各种教师/学生标签归一化为 'teacher' 或 'student'。"""
    raw = raw_role.strip().rstrip('：:').strip()
    teacher_labels = {'师', '教师', '老师', 'T', 'Teacher', 'te', 't'}
    student_labels = {'生', '学生', 'S', 'Student', 's'}
    # 带编号的学生标签，如 "生1"、"学生A"
    if re.match(r'^生\d+$|^学生\d+$|^S\d+$', raw):
        return 'student'
    if raw in teacher_labels:
        return 'teacher'
    if raw in student_labels:
        return 'student'
    # 无法识别时默认为 student（学生可能被标注为具体姓名）
    return 'student'


# ── 格式解析 ──────────────────────────────────────────────

def parse_timestamped(text: str) -> list[dict]:
    """解析带时间戳的对话格式。

    支持格式:
        【00:00-02:30】导入
        师：xxx
        生1：xxx
    """
    turns = []
    turn_id = 0
    current_timestamp = None
    current_segment = ""

    # 提取时间戳段落
    segment_pattern = re.compile(
        r'[【\[](\d{1,2}:\d{2}(?::\d{2})?)[-\–—~～](\d{1,2}:\d{2}(?::\d{2})?)[】\]]\s*(.*)'
    )
    speaker_pattern = re.compile(
        r'^(师|教师|老师|T|生\d*|学生\d*|S\d*)\s*[：:]\s*(.+)', re.MULTILINE
    )

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        seg_match = segment_pattern.match(line)
        if seg_match:
            current_timestamp = parse_timestamp(seg_match.group(1))
            current_segment = seg_match.group(3).strip()
            continue

        # 检查是否为 "师：xxx" 或 "生：xxx" 同行
        # 也可能一行中有多个说话人（少见但可能）
        spk_match = speaker_pattern.match(line)
        if spk_match:
            role = normalize_role(spk_match.group(1))
            speech = spk_match.group(2).strip()
            turns.append({
                "turn_id": turn_id,
                "role": role,
                "raw_role": spk_match.group(1).strip(),
                "text": speech,
                "timestamp": current_timestamp,
                "segment": current_segment,
            })
            turn_id += 1

    return turns


def parse_speaker_turn(text: str) -> list[dict]:
    """解析师/生标签对话格式（无时间戳）。"""
    turns = []
    turn_id = 0
    speaker_pattern = re.compile(
        r'^(师|教师|老师|T|生\d*|学生\d*|S\d*)\s*[：:]\s*(.+)', re.MULTILINE
    )

    for match in speaker_pattern.finditer(text):
        role = normalize_role(match.group(1))
        speech = match.group(2).strip()
        turns.append({
            "turn_id": turn_id,
            "role": role,
            "raw_role": match.group(1).strip(),
            "text": speech,
            "timestamp": None,
            "segment": "",
        })
        turn_id += 1

    return turns


def parse_mixed_notes(text: str) -> list[dict]:
    """解析混合格式或听课笔记。

    尝试提取所有可识别的说话人发言，其余作为叙述性笔记。
    """
    turns = []
    turn_id = 0

    # 先尝试提取明确的说话人发言
    speaker_pattern = re.compile(
        r'(师|教师|老师|T|生\d*|学生\d*|S\d*)\s*[：:]\s*(.+?)(?=(?:师|教师|老师|T|生\d*|学生\d*|S\d*)\s*[：:]|\Z)',
        re.DOTALL
    )

    found_speakers = list(speaker_pattern.finditer(text))

    if found_speakers:
        # 处理说话人之前/之间的叙述性文字
        last_end = 0
        for match in found_speakers:
            # 匹配前的叙述文字
            before = text[last_end:match.start()].strip()
            if before:
                turns.append({
                    "turn_id": turn_id,
                    "role": "narrative",
                    "raw_role": "叙述",
                    "text": before,
                    "timestamp": None,
                    "segment": "",
                })
                turn_id += 1

            role = normalize_role(match.group(1))
            speech = match.group(2).strip()
            turns.append({
                "turn_id": turn_id,
                "role": role,
                "raw_role": match.group(1).strip(),
                "text": speech,
                "timestamp": None,
                "segment": "",
            })
            turn_id += 1
            last_end = match.end()

        # 最后一段叙述
        after = text[last_end:].strip()
        if after:
            turns.append({
                "turn_id": turn_id,
                "role": "narrative",
                "raw_role": "叙述",
                "text": after,
                "timestamp": None,
                "segment": "",
            })
    else:
        # 无法识别任何说话人，整体作为叙述
        turns.append({
            "turn_id": 0,
            "role": "narrative",
            "raw_role": "叙述",
            "text": text,
            "timestamp": None,
            "segment": "",
        })

    return turns


# ── 统计计算 ──────────────────────────────────────────────

def compute_stats(turns: list[dict]) -> dict:
    """计算基础统计信息。"""
    teacher_turns = [t for t in turns if t['role'] == 'teacher']
    student_turns = [t for t in turns if t['role'] == 'student']
    narrative_turns = [t for t in turns if t['role'] == 'narrative']

    # 问题统计
    question_marks_cn = sum(t['text'].count('？') + t['text'].count('?') for t in turns)

    # 教师问题数（教师发言中包含问号的条目数）
    teacher_questions = sum(
        1 for t in teacher_turns
        if '？' in t['text'] or '?' in t['text']
    )

    # 时间段统计
    timestamps = [t['timestamp'] for t in turns if t['timestamp'] is not None]
    segments = list(dict.fromkeys(t['segment'] for t in turns if t['segment']))

    # 估算总时长
    total_duration = None
    if timestamps:
        max_ts = max(timestamps)
        min_ts = min(timestamps)
        # 粗略估算：最后一个时间戳 + 平均每轮 30 秒
        total_duration = max_ts + 30

    # 教师/学生发言字数
    teacher_chars = sum(len(t['text']) for t in teacher_turns)
    student_chars = sum(len(t['text']) for t in student_turns)

    return {
        "total_turns": len(turns),
        "teacher_turns": len(teacher_turns),
        "student_turns": len(student_turns),
        "narrative_turns": len(narrative_turns),
        "t_s_ratio": round(len(teacher_turns) / max(len(student_turns), 1), 2),
        "total_question_marks": question_marks_cn,
        "teacher_question_count": teacher_questions,
        "teacher_chars": teacher_chars,
        "student_chars": student_chars,
        "char_ratio_t_s": round(teacher_chars / max(student_chars, 1), 2),
        "segment_count": len(segments),
        "segments": segments,
        "estimated_duration_seconds": total_duration,
        "estimated_duration_display": seconds_to_timestamp(total_duration) if total_duration else None,
    }


# ── 主流程 ──────────────────────────────────────────────

def preprocess(text: str) -> dict:
    """主预处理函数：检测格式、解析、统计。"""
    cleaned = clean_text(text)
    fmt = detect_format(cleaned)

    if fmt == "timestamped":
        turns = parse_timestamped(cleaned)
    elif fmt == "speaker_turn":
        turns = parse_speaker_turn(cleaned)
    else:
        turns = parse_mixed_notes(cleaned)

    stats = compute_stats(turns)

    return {
        "format_detected": fmt,
        "stats": stats,
        "turns": turns,
        "raw_text_preview": cleaned[:500] + ("..." if len(cleaned) > 500 else ""),
    }


def main():
    parser = argparse.ArgumentParser(
        description='课堂实录预处理：格式检测、归一化、基础统计'
    )
    parser.add_argument('--input', '-i', help='输入文件路径（默认读取 stdin）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认输出到 stdout）')
    parser.add_argument('--pretty', action='store_true', default=True,
                        help='格式化 JSON 输出（默认开启）')
    args = parser.parse_args()

    # 读取输入
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("错误：输入为空", file=sys.stderr)
        sys.exit(1)

    # 处理
    result = preprocess(text)

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
