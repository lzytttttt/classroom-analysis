# classroom-analysis

将课堂实录、师生对话、听课笔记转化为基于证据的课堂分析报告、教学改进建议和可研发文章选题的 Claude Code Skill。

## 功能

- 自动检测课堂实录格式（时间戳对话 / 师生标签 / 听课笔记）
- 提取基础统计：轮次数、师生比、问题数、时间分配
- 识别 IRE/IRF 互动模式、问题类型、认知层级
- 生成 15 段标准化教研分析报告骨架
- 支持完整报告、精简报告、定向分析三种模式
- 参考文件覆盖 K12 四学段认知层级框架、9 种课型特化维度、6 种教研文章模板

## 快速开始

```bash
# 完整管道：预处理 → 分析 → 报告骨架
python scripts/transcript_preprocessor.py -i input.txt \
  | python scripts/classroom_analyzer.py \
  | python scripts/generate_report.py -o report.md

# 精简模式（6 段）
python scripts/generate_report.py -i analysis.json --mode brief -o brief_report.md

# 定向分析（指定段号）
python scripts/generate_report.py -i analysis.json --mode targeted --target 5,6,7 -o focused.md
```

无第三方依赖，仅需 Python >= 3.8。

## 文件结构

```
classroom-analysis/
├── SKILL.md                          Skill 主文件
├── README.md                         本文件
├── requirements.txt                  依赖声明（stdlib only）
├── scripts/
│   ├── transcript_preprocessor.py    文本预处理（格式检测、归一化、统计）
│   ├── classroom_analyzer.py         深度分析（问题类型、认知层级、IRE/IRF、环节检测）
│   └── generate_report.py            报告骨架生成
└── references/
    ├── cognitive_levels.md           Bloom 认知层级框架（按学段适配）
    ├── lesson_type_dimensions.md     9 种课型特化分析维度
    ├── article_templates.md          6 种教研文章大纲模板
    ├── quality_checklist.md          15 段报告逐段质量检查清单
    └── example_input_output.md       完整示例（输入 → 第 1-6 段输出）
```

## 使用方式

在 Claude Code 中直接使用，上传课堂实录文本即可触发 skill。脚本可单独运行用于预处理，也可完全由 Claude 直接分析文本而跳过脚本。

## 作者

**lzytttttt** · lzytttttt@gmail.com

## 许可证

[MIT License](LICENSE)

Copyright (c) 2026 lzytttttt
