---
name: classroom-analysis
description: Analyze classroom transcripts, teacher-student dialogue, lesson observation notes, classroom fragments, and teaching process records for teaching-research writing. Use when the user asks for classroom transcript analysis, classroom observation reports, teaching improvement suggestions, problem-chain analysis, cognitive-level analysis, learning-evidence analysis, or teaching-research article topics/outlines.
when_to_use: Apply to K12 subjects, higher education, teacher training, public lessons, demonstration lessons, regular lessons, new lessons, review lessons, commentary lessons, experiment lessons, discussion lessons, project lessons, writing lessons, reading lessons, PE, arts, and other classroom contexts. Use when the task requires identifying classroom structure, teacher/student behaviors, learning tasks, question chains, interaction feedback, cognitive levels, learning evidence, pacing, goal-activity-assessment alignment, classroom highlights, problems, and researchable article directions.
argument-hint: "[classroom transcript, observation notes, dialogue text, or classroom fragment]"
---

# Classroom Analysis Skill

You are analyzing classroom materials for teaching research writing, not merely producing a generic lesson evaluation. Convert classroom chronology, teacher-student talk, and observation notes into evidence-based classroom analysis, improvement suggestions, and researchable article ideas.

## Supporting Files

本 skill 配有脚本和参考文件，可在分析前运行脚本进行预处理，也可直接查阅参考文件辅助判断。

### 脚本（scripts/）

三个脚本通过 JSON 管道串联，可在分析前运行以提取结构化数据：

```bash
# 完整管道：预处理 → 分析 → 报告骨架
python scripts/transcript_preprocessor.py -i transcript.txt \
  | python scripts/classroom_analyzer.py \
  | python generate_report.py --output report.md

# 也可以分步运行
python scripts/transcript_preprocessor.py -i transcript.txt -o preprocessed.json
python scripts/classroom_analyzer.py -i preprocessed.json -o analysis.json
python generate_report.py -i analysis.json --mode brief --output report.md
```

| 脚本 | 功能 | 输出 |
|---|---|---|
| `transcript_preprocessor.py` | 格式检测、文本归一化、基础统计（轮次数、师生比、问题数） | JSON |
| `classroom_analyzer.py` | 问题类型检测、认知层级分类、IRE/IRF 互动模式识别、环节边界检测 | JSON |
| `generate_report.py` | 生成报告 Markdown 骨架，支持 `--mode full/brief/targeted` | Markdown |

脚本输出为**辅助参考**，不可替代对课堂文本的深度阅读。认知层级和问题类型的自动分类基于关键词启发式，需人工校验。

### 参考文件（references/）

| 文件 | 内容 | 使用时机 |
|---|---|---|
| `cognitive_levels.md` | Bloom 认知层级框架按学段适配（小学低/高年级、初中、高中），含学科化示例 | 第 6 段认知层级分析时参照 |
| `lesson_type_dimensions.md` | 9 种课型（新授课、复习课、实验课、写作课等）的特化分析维度 | 第 1 段确定课型后，叠加对应特化维度 |
| `article_templates.md` | 6 种教研文章类型的结构化大纲模板 | 第 13-14 段生成文章选题时参照 |
| `quality_checklist.md` | 15 段报告的逐段质量检查清单 | 报告完成后自检 |
| `example_input_output.md` | 完整示例：10 轮初中数学课堂对话 → 对应的第 1-6 段分析输出 | 分析前参考，建立输出标准预期 |

## Analysis Mode

根据输入材料的完整度和用户意图选择分析模式：

| 模式 | 条件 | 输出范围 | 脚本参数 |
|---|---|---|---|
| **完整报告** | 完整课堂实录 + 用户未限定范围 | 全部 15 段 | `--mode full` |
| **精简报告** | 材料较短或用户要求精简 | 第 1,2,5,6,11,15 段 | `--mode brief` |
| **片段分析** | 材料不完整或仅含部分环节 | 跳过第 8（节奏）、9（一致性）等需要完整数据的段 | `--mode targeted --target 1,2,3,4,5,6` |
| **定向分析** | 用户明确指定分析维度 | 只输出相关段 + 必要的上下文段（1、2） | `--mode targeted --target <段号>` |

如果用户未指定，默认使用**完整报告**模式。

## Scope

Use this skill for:

- K12 Chinese, mathematics, English, science, history, geography, morality/law, arts, PE, and other subjects.
- Higher education classrooms.
- Teacher training lessons.
- Public lessons, demonstration lessons, regular lessons, observed lessons, and classroom fragments.
- New lessons, review lessons, commentary lessons, experiment lessons, discussion lessons, project lessons, writing lessons, reading lessons, and other lesson types.

Accept input such as:

- Time-stamped classroom transcripts.
- Teacher-student dialogue text.
- Lesson observation notes.
- Classroom fragments.
- Teaching process records.
- Classroom observation materials.

If the material is partial, lacks timestamps, or lacks student artifacts, still analyze what is available, but explicitly state the limits.

## Core Principles

1. Evidence first: every important judgment must cite specific time ranges, teacher/student utterances, activity descriptions, or observable classroom episodes from the provided material.
2. Do not evaluate the teacher as a person. Evaluate classroom behavior, instructional design, learning opportunities, task quality, interaction quality, and evidence of learning.
3. Avoid vague praise or criticism. Do not write claims such as “the atmosphere was active” or “the effect was good” unless the text shows concrete evidence, such as multiple students explaining, revising, questioning, producing work, or applying concepts.
4. Serve teaching-research writing. Move from “what happened” to “what problem is worth researching,” “what mechanism may explain it,” and “what argument can be developed into an article.”
5. Do not invent missing evidence. If student work, board writing, slides, worksheets, assessment results, grouping details, or final products are absent, name the absence and explain how it limits inference.
6. Preserve uncertainty. Use wording such as “文本显示,” “可初步判断,” “尚不能证明,” and “需要结合学生作品/练习结果进一步确认” where appropriate.
7. Quote economically. Use short quotations or concise paraphrases, but include enough detail for the reader to verify the analysis.
8. Adapt to lesson type. After identifying the lesson type in Section 1, consult `references/lesson_type_dimensions.md` for additional analysis dimensions specific to that lesson type (e.g., experiment procedure for lab lessons, revision feedback for writing lessons).

## Required Analysis Order

Follow this sequence. Do not jump directly to article topics before completing the classroom evidence analysis.

### 1. Basic Identification

Identify:

- Subject.
- School stage or learner level.
- Lesson type.
- Approximate total duration.
- Core learning task or central learning problem.

If any item cannot be inferred, write “材料未显示” and explain what evidence would be needed.

### 2. Classroom Segmentation

Segment the lesson chronologically. Use timestamps where available. Common segments include:

- Introduction or problem posing.
- Prior knowledge activation.
- New knowledge construction.
- Activity inquiry or experiment.
- Discussion or collaborative learning.
- Practice and feedback.
- Presentation or sharing.
- Summary, transfer, or reflection.

For each segment, identify the teacher’s main action, the students’ main learning action, the task, and the observable learning evidence.

### 3. Teacher Behavior Annotation

Annotate teacher behaviors with evidence. Categories may include:

- Explanation.
- Questioning.
- Follow-up questioning.
- Demonstration/modeling.
- Organizing activities.
- Giving instructions.
- Providing feedback.
- Summarizing.
- Guiding comparison.
- Scaffolding.
- Evaluating or correcting.
- Connecting prior and new knowledge.

Analyze not only frequency, but function: what learning opportunity did the behavior create or close down?

### 4. Student Behavior Annotation

Annotate student behaviors with evidence. Categories may include:

- Listening.
- Answering.
- Discussing.
- Operating/experimenting.
- Practicing.
- Presenting.
- Questioning.
- Reflecting.
- Creating.
- Revising.
- Explaining reasoning.
- Comparing strategies.

Distinguish “students were present” from “students performed meaningful learning actions.”

### 5. Learning Task Analysis

Determine what students actually did, not only what the teacher intended. For each major task, identify:

- Task name.
- Task goal.
- Input or material used.
- Student action required.
- Expected output.
- Actual evidence of completion.
- Cognitive demand.
- Whether the task is individual, pair, group, or whole-class.

Check whether tasks require students to think, explain, apply, evaluate, create, or merely repeat and follow.

### 6. Question Chain Analysis

Analyze the teacher’s question chain and student responses:

- Question type: factual recall, comprehension, procedural, analytical, comparative, causal, evaluative, creative, reflective, metacognitive.
- Cognitive level: memory, understanding, application, analysis, evaluation, creation.
- Sequence: whether questions form a progressive chain or isolated checks.
- Follow-up quality: whether the teacher asks students to justify, compare, revise, extend, or transfer.
- Student uptake: whether students answer with words, reasoning, examples, operations, products, or questions.

Evaluate whether questions open thinking space or lead students to guess the teacher’s expected answer.

### 7. Interaction and Feedback Analysis

Analyze how teacher feedback handles student responses:

- Did the teacher acknowledge the substance of the student answer?
- Did the teacher identify what was correct, incomplete, or worth extending?
- Did the teacher ask students to explain reasons or evidence?
- Did feedback redirect, deepen, compare, or summarize?
- Did the teacher connect one student’s response to another student’s response?
- Were student errors used as learning resources?

Use “接住学生回答” as a key lens: identify whether student responses became material for further learning or were quickly closed by teacher evaluation.

### 8. Cognitive Level Analysis

Use the six-level framework flexibly. Refer to `references/cognitive_levels.md` for grade-level adaptation and subject-specific examples. The evaluation of cognitive levels must be contextualized by grade band: a lesson dominated by memory and understanding in lower primary is not necessarily low-quality.

1. Memory: recalling facts, definitions, procedures, vocabulary, formulas, or text details.
2. Understanding: explaining meaning, summarizing, classifying, interpreting, or translating representations.
3. Application: using knowledge, methods, language, concepts, or procedures in a concrete task.
4. Analysis: comparing, distinguishing, inferring relationships, identifying causes, structures, strategies, or evidence.
5. Evaluation: judging quality, validity, reasonableness, strategy, expression, or solution with criteria.
6. Creation: producing, designing, composing, modeling, proposing, performing, or generating new work.

Do not mechanically label every sentence. Identify dominant levels by lesson segment and by major task. Explain transitions, stagnation, or missed opportunities.

### 9. Learning Evidence Analysis

Identify whether the text contains evidence of student learning, including:

- Understanding: students explain concepts, meanings, text, methods, or reasoning.
- Application: students use knowledge or skills in a task.
- Transfer: students apply learning to a new context or similar problem.
- Expression: students articulate reasoning, observation, argument, interpretation, or creative work.
- Revision: students correct, refine, compare, or improve previous thinking.
- Product: students produce answers, notes, experiments, writings, designs, performances, models, or other artifacts.

Classify evidence strength:

- Strong: concrete student output or explanation is visible.
- Medium: student participation is visible but output quality is partly unknown.
- Weak: only teacher intention or activity arrangement is visible.
- Absent: no direct evidence in the material.

### 10. Classroom Pacing Analysis

Use timestamps where available to analyze time allocation:

- Duration of each segment.
- Ratio of teacher talk, student talk, task work, feedback, and summary if inferable.
- Whether important learning tasks received enough time.
- Whether introduction, explanation, activity, practice, feedback, and reflection were balanced.
- Whether high-cognitive tasks were rushed or low-cognitive tasks took excessive time.

If timestamps are missing, analyze sequence and density instead of exact duration.

### 11. Goal-Activity-Assessment Alignment

Analyze alignment among:

- Learning goals: explicit or inferred.
- Learning activities: what students actually did.
- Assessment or evidence: what showed whether goals were reached.

Judge:

- Are activities directly serving the core goal?
- Is there evidence that students reached the goal?
- Does feedback address the goal or only manage correctness/participation?
- Are tasks and questions aligned with the intended cognitive level?
- Are there gaps between intended outcome and observable evidence?

### 12. Highlights and Problem Diagnosis

Identify classroom highlights and problems with evidence. For each highlight/problem:

- State the claim.
- Cite time range or episode.
- Explain why it matters pedagogically.
- Connect it to learning opportunity, student thinking, task design, interaction quality, or research value.

Problems should be framed as design/behavior issues, not personal criticism. Examples:

- “问题链停留在事实确认，缺少促成解释和比较的追问.”
- “活动有操作但缺少产出标准，导致学习证据不够清晰.”
- “反馈多为判断正误，较少利用学生回答推进概念建构.”

### 13. Teaching Improvement Suggestions

Provide actionable suggestions. Each suggestion must include:

- Target issue.
- Suggested adjustment.
- Concrete implementation example, such as a revised question, task instruction, feedback sentence, worksheet prompt, discussion rule, evaluation criterion, or time allocation change.
- Expected learning evidence after the adjustment.

Avoid generic advice such as “increase interaction” unless you specify how, where, and why.

### 14. Teaching-Research Article Topics and Outlines

Generate article topics based on the classroom evidence. Refer to `references/article_templates.md` for structural templates of six article types. Each topic must include:

- Title.
- Problem awareness: what classroom problem or tension the article addresses.
- Core argument: the claim or thesis, not merely a theme.
- Evidence basis: which classroom episodes support the topic.
- Research angle: task design, question chain, learning evidence, feedback, classroom pacing, cognitive progression, alignment, subject-specific literacy, etc.
- Suitable article type: case analysis, teaching reflection, lesson study report, classroom observation report, action research, teaching strategy paper, or subject pedagogy paper.

Then recommend one best topic and produce an article outline with:

- Proposed title.
- Central thesis.
- Introduction: problem origin and classroom context.
- Section 1: classroom evidence and problem identification.
- Section 2: mechanism analysis or theoretical interpretation.
- Section 3: improvement design or strategy reconstruction.
- Section 4: expected evidence and evaluation method.
- Conclusion: transferable teaching-research insight.

The topic must have a clear problem and arguable thesis. Do not output only decorative titles.

## Fixed Markdown Output Template

Use the following template by default. Add tables where they improve clarity, but do not omit required sections. See `references/example_input_output.md` for a complete example of sections 1-6.

If a section lacks sufficient evidence, do not fill the table with empty rows. Instead, write a brief note: "材料中未观察到 XX 证据，因此无法完成此维度分析。建议补充 YY 材料。"

For shorter transcripts or targeted analysis, use the brief/targeted modes (see Analysis Mode above) to skip sections that require data not present in the material.

```markdown
# 通用课堂实录分析报告

## 1. 课堂基本判断

| 维度 | 判断 | 依据 | 不确定性 |
|---|---|---|---|
| 学科 |  |  |  |
| 学段/对象 |  |  |  |
| 课型 |  |  |  |
| 总时长 |  |  |  |
| 核心学习任务 |  |  |  |

## 2. 课堂环节切分

| 时间段 | 环节 | 教师主要行为 | 学生主要行为 | 学习任务 | 学习证据 | 初步判断 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 3. 教师行为分析

### 3.1 教师行为分布

| 行为类型 | 典型时间/片段 | 具体表现 | 对学习的作用 | 可能风险 |
|---|---|---|---|---|
|  |  |  |  |  |

### 3.2 关键教学行为解读

- 证据：
- 分析：
- 教研价值：

## 4. 学生学习行为分析

| 学生行为 | 时间/片段 | 学生实际做了什么 | 学习意义 | 证据强度 |
|---|---|---|---|---|
|  |  |  |  |  |

## 5. 问题链与互动分析

### 5.1 问题链梳理

| 时间/片段 | 教师问题 | 学生回应 | 问题类型 | 认知层级 | 追问/反馈 | 质量判断 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

### 5.2 互动反馈诊断

- 能够接住学生回答的片段：
- 未充分展开学生回答的片段：
- 问题链的递进性判断：
- 可改进的追问示例：

## 6. 认知层级分析

| 环节/任务 | 主要认知层级 | 依据 | 是否出现层级递进 | 可提升空间 |
|---|---|---|---|---|
|  |  |  |  |  |

总体判断：

## 7. 学习证据分析

| 证据类型 | 时间/片段 | 具体证据 | 证据强度 | 可支持的学习判断 | 局限 |
|---|---|---|---|---|---|
| 理解 |  |  |  |  |  |
| 应用 |  |  |  |  |  |
| 迁移 |  |  |  |  |  |
| 表达 |  |  |  |  |  |
| 修正 |  |  |  |  |  |
| 产出 |  |  |  |  |  |

## 8. 课堂节奏分析

| 时间段 | 时长 | 教学/学习活动 | 时间使用判断 | 依据 | 调整建议 |
|---|---:|---|---|---|---|
|  |  |  |  |  |  |

总体节奏判断：

## 9. 目标—活动—评价一致性分析

| 目标/核心任务 | 对应活动 | 对应评价或学习证据 | 一致性判断 | 问题与原因 |
|---|---|---|---|---|
|  |  |  |  |  |

## 10. 课堂亮点

### 亮点一：
- 证据：
- 分析：
- 可提炼的教研观点：

### 亮点二：
- 证据：
- 分析：
- 可提炼的教研观点：

## 11. 问题诊断

### 问题一：
- 证据：
- 诊断：
- 对学习的影响：
- 可研究化表述：

### 问题二：
- 证据：
- 诊断：
- 对学习的影响：
- 可研究化表述：

## 12. 教学改进建议

| 针对问题 | 改进建议 | 可直接使用的课堂话语/任务设计 | 预期学习证据 |
|---|---|---|---|
|  |  |  |  |

## 13. 可研发文章选题

| 选题 | 问题意识 | 核心论点 | 课堂证据基础 | 研究角度 | 文章类型 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 14. 推荐文章大纲

### 推荐题目

### 中心论点

### 一、问题提出：课堂现象与研究价值

### 二、课堂证据：关键片段与问题呈现

### 三、机制分析：任务、问题链、反馈或证据的内在关系

### 四、改进设计：教学策略与课堂实施路径

### 五、评价方式：如何收集新的学习证据

### 六、结论：可迁移的教研启示

## 15. 分析限制说明

- 材料缺失项：
- 因缺失而不能确认的判断：
- 建议补充的证据：
```

## Quality Checklist Before Final Response

Use the detailed per-section checklist in `references/quality_checklist.md` for thorough verification. Additionally, before returning the final report, verify:

- The report follows the required 15-section template.
- Claims cite specific time ranges, utterances, or classroom episodes.
- The analysis distinguishes teacher intention from student evidence.
- The analysis does not evaluate the teacher personally.
- Missing information and inference limits are clearly stated.
- Article topics include both problem awareness and a core argument.
- Improvement suggestions are operational and tied to diagnosed problems.
- The final recommended outline is usable for teaching-research writing.
