# MCM/ICM 从 0 到最终论文全流程 SOP

本文档总结本项目从初始化到最终 25 页论文的完整流程。目标是：下次只要给出本文件、题目数据、官方要求和既定思路，就可以尽量一次跑通，不再反复踩同样的坑。

## 0. 总原则

1. 先读已有材料，再动手建模。尤其是已经定下思路的讨论记录、复盘文件、优秀仓库和官方题目要求。
2. 区分两类代码：
   - 通用算法代码优先使用成熟包，例如 `scipy`、`cvxpy`、`statsmodels`、`lifelines`、`pandas`、`matplotlib`、`seaborn`。
   - 针对本题的数据清洗、约束构造、图表生成、论文导出代码必须自己写，并且可复现。
3. 不要重新构思已经定下的论文主线。已有方案是约束，新的工作是把它落成数据、模型、图表和论文。
4. 所有数据、图、表、论文都要能从代码或明确记录追溯来源。
5. 论文不是越短越好，也不是靠放大图片凑页数。高质量论文靠任务拆解、诊断层、公式推导、案例分析、敏感性分析和落地建议变厚。
6. 关键节点要分批 commit，让提交历史像真人逐步完成项目，而不是最后一次性塞进去。

## 1. 用户和助手的分工

### 用户负责

1. 提供题目、官方数据、官方格式要求和赛题背景。
2. 提供已有经验库、复盘文件、优秀论文和配套仓库。
3. 明确已经确定的核心思路，避免助手重新发散。
4. 对论文质量提出主观审美和结构要求，例如：
   - 摘要必须有 `Summary` 标题。
   - 目录必须存在，并包含 References。
   - 页面不能空，图表不能过大。
   - 表格、公式、推导和案例要足够丰富。
   - 需要学习优秀论文的密度和结构。
5. 负责 AI 生成图片时，根据助手给出的 prompt 生成图片，并放到指定目录。
6. 最后人工阅读 PDF，指出“不够厚”“不够像优秀论文”“格式别扭”等肉眼问题。

### 助手负责

1. 初始化项目结构、Git 和 GitHub private 仓库。
2. 检查环境，优先复用已有 Conda 环境，不盲目新建环境。
3. 制定项目计划、目录结构、代码包选择和论文路线。
4. 编写本题专用代码，运行数据清洗、模型、图表、表格导出。
5. 使用成熟算法包实现优化、统计、回归、生存分析等通用算法。
6. 编译论文，检查页数、目录、引用、排版、空白、表格和图注。
7. 根据用户反馈多轮扩充和润色论文。
8. 分批 commit，并 push 到 GitHub private 仓库。

## 2. 项目初始化流程

### 2.1 建立仓库

建议目录结构：

```text
project/
  data/
    raw/
    interim/
    processed/
  src/
    <package_name>/
  scripts/
  tests/
  figures/
    generated/
    concept/
  tables/
  reports/
  paper/
  README.md
  pyproject.toml
  environment.yml
  requirements-lock.txt
```

初始化 Git：

```powershell
git init
git branch -M main
git status
```

创建 GitHub private 仓库后添加远端：

```powershell
git remote add origin <private_repo_url>
git push -u origin main
```

经验：如果用户明确要求 private，创建远端时必须设置 private。不要先公开再改。

### 2.2 环境策略

本项目选择复用已有 `mcm` Conda 环境，而不是新建环境。这样可以减少虚拟环境混乱。

常用命令：

```powershell
conda --no-plugins run -n mcm python --version
conda --no-plugins run -n mcm python scripts/run_all.py
conda --no-plugins run -n mcm pytest -q
```

经验：

1. 如果已有环境能用，不要新建。
2. 可以更新已有环境，但要记录 `environment.yml` 和 `requirements-lock.txt`。
3. 算法包优先安装成熟包，避免自己手写优化器、回归器、生存模型等高风险底层算法。

## 3. 前期资料阅读流程

正式建模前必须读：

1. 官方题目 PDF。
2. 官方数据说明和 CSV。
3. 用户指定的核心讨论记录。本项目最关键的是：
   `Chat_Records/Pro_讨论2026C题的构思和论文结构.md`
4. 复盘文件和经验库。
5. 优秀论文和配套仓库。

读优秀论文时不要只看结论，要看它为什么显得“厚”：

1. 有 Summary、目录、Notations、Assumptions。
2. 每个任务拆成多个 subsection / subsubsection。
3. 有大量诊断表、对比表、敏感性分析表。
4. 公式不仅给结果，还解释为什么这样建模。
5. 图表不是大而空，而是小而密、和正文互相解释。
6. 每个 Figure 都有独立、简短、规范的 caption。
7. 结论不是空喊，最后有 memo / policy / implementation / risk control。

## 4. 数据与代码流水线

### 4.1 数据层

原始数据放：

```text
data/raw/
```

中间表放：

```text
data/interim/
```

最终建模结果放：

```text
data/processed/
```

本项目核心数据产物包括：

```text
data/interim/long_panel.csv
data/interim/active_set_by_week.csv
data/interim/elimination_events.csv
data/processed/fan_vote_estimates.csv
data/processed/rule_counterfactuals.csv
data/processed/baseline_comparison.csv
data/processed/threshold_sensitivity.csv
data/processed/contestant_instability.csv
data/processed/selected_effects.csv
```

### 4.2 代码层

建议将本题专用代码模块化：

```text
src/<package_name>/
  config.py
  data_loader.py
  data_audit.py
  build_panel.py
  reconstruct_events.py
  voting_rules.py
  fan_constraints.py
  fan_estimation.py
  validation.py
  counterfactuals.py
  controversy.py
  effects.py
  proposed_system.py
  uncertainty.py
  diagnostics.py
  plots.py
  export_tables.py
  model_outputs.py
```

经验：

1. 每个模块只做一类事情。
2. 图表和表格都由代码导出，不手动复制数字。
3. 关键结果同时写入 `reports/key_results.csv`，方便论文引用。
4. 图表清单写入 `reports/figure_manifest.csv`，避免忘记哪些图被使用。

### 4.3 一键运行脚本

必须有：

```text
scripts/run_all.py
```

它负责按顺序运行：

1. 数据读取和审计。
2. 长表转换和 active set 重建。
3. elimination events 重建。
4. fan vote constraints 和 maximum entropy 估计。
5. rule counterfactuals。
6. controversy / effects / proposed system。
7. figure generation。
8. table export。
9. report summaries。

运行：

```powershell
conda --no-plugins run -n mcm python scripts/run_all.py
```

## 5. 图表准备流程

### 5.1 代码生成图

代码图放：

```text
figures/generated/
```

适合代码生成的图：

1. 数据结构图。
2. 分布图。
3. heatmap。
4. validation dashboard。
5. baseline comparison。
6. sensitivity curve。
7. trajectory plot。
8. effects forest plot。

### 5.2 AI 生成图

AI 概念图放：

```text
figures/concept/
```

适合 AI 生成的图：

1. 总体 workflow 图。
2. voting rule mechanism 图。
3. proposed system flowchart。
4. producer decision card。

经验：

1. 需要 AI 生成的图，必须提前给出精确 prompt 和目标路径。
2. AI 图只承担概念表达，不能承载核心数值结果。
3. 论文里的关键模型证据必须来自代码生成图和表。
4. AI 图片生成完后，必须检查文件路径、尺寸、清晰度和是否被 LaTeX 正确引用。

## 6. 论文写作流程

### 6.1 写作前必须先列 plan

论文开写前先列结构计划，通常包括：

1. Summary。
2. Contents。
3. Introduction / Problem Restatement。
4. Notation and Assumptions。
5. Data Audit and Preprocessing。
6. Model Formulation。
7. Fan Vote Estimation。
8. Validation。
9. Counterfactual Analysis。
10. Controversial Cases。
11. Effects Model。
12. Proposed System。
13. Sensitivity Analysis。
14. Quality Control / Audit。
15. Memo。
16. Strengths, Limitations, Extensions。
17. References。

经验：不要一上来写正文。先让用户确认 plan，这样后面改动更少。

### 6.2 第一版论文

第一版重点是把全链条写通：

1. 摘要能概括问题、方法、结果、建议。
2. 每个模型都能对应数据产物。
3. 每张图表都在正文解释。
4. References 能编译。

第一版通常不追求最终页数，但不能太薄。

### 6.3 根据优秀论文扩充

本项目的关键经验：论文从 17 页、20 页扩到 25 页，靠的是补真实内容，而不是放大图片。

应该补：

1. `Identifiability boundary`：解释隐藏 fan vote 为什么只能识别 feasible region。
2. `Rule disagreement mechanism`：用公式解释 rank 和 percent 为什么会分歧。
3. `Case interpretation`：解释 Vinny、Bobby Bones、Bristol Palin、Joanna Krupa 等高杠杆案例。
4. `Data-driven controversy scan`：不要只分析题目点名的人，也要全局扫描。
5. `Professional dancer and celebrity effects`：给出模型公式和估计结果。
6. `Rule-design scorecard`：把推荐规则和备选规则横向比较。
7. `Risk controls`：说明制作方风险与控制方法。
8. `Quality Control and Reproducibility`：说明每个结论如何被审计。
9. `Viewer Communication and Audit Package`：说明结果如何向观众公开和存档。

不应该补：

1. 无来源的猜测。
2. 和题目无关的背景故事。
3. 过大的图。
4. 长到像正文的 caption。
5. 没有解释的堆表。

## 7. 格式和排版经验

### 7.1 Summary

必须有 `Summary` 标题。摘要不能只有半页，要尽量写满但不啰嗦。

摘要建议包含：

1. 问题本质。
2. 数据规模。
3. 方法。
4. 核心结果。
5. 推荐方案。
6. 现实解释。

### 7.2 目录

必须有目录，并确认 References 在目录里。

如果目录因为条目太多变成两页，可压缩目录：

```latex
{\small
\renewcommand{\baselinestretch}{0.94}\selectfont
\tableofcontents
}
```

经验：目录单独多出一页会浪费页数，也会显得不专业。

### 7.3 段落

使用统一风格：

```latex
\usepackage{indentfirst}
\setlength{\parskip}{0pt}
\setlength{\parindent}{1.2em}
```

经验：不要一会儿段前空行、一会儿首行缩进。标准论文通常首行缩进，段间距小。

### 7.4 图表

图表策略：

1. 重要总览图可以稍大。
2. 普通诊断图应紧凑。
3. 表格尽量信息密度高。
4. 不要一页只有两张大图。
5. 每张 figure 应有自己的 caption。
6. caption 要短，不要写成长段解释。
7. 解释放正文，不放 caption。

推荐 LaTeX 设置：

```latex
\captionsetup{font=footnotesize,labelfont=bf,skip=2pt}
\setlength{\textfloatsep}{0.55em plus 0.2em minus 0.2em}
\setlength{\floatsep}{0.45em plus 0.2em minus 0.2em}
\setlength{\intextsep}{0.45em plus 0.2em minus 0.2em}
\AtBeginEnvironment{tabular}{\small}
\AtBeginEnvironment{tabularx}{\small}
```

### 7.5 加粗

可以适度加粗：

1. 摘要中的核心变量、方法和结论。
2. 表示关键概念的第一次出现。
3. Memo 或 recommendation 中的核心建议。

不要全文大面积加粗，否则像宣传稿。

### 7.6 页数

如果页数太少，优先补：

1. 模型边界和假设。
2. 公式推导。
3. 诊断表。
4. 案例解释。
5. 敏感性分析。
6. 风险控制和落地流程。

如果页数超了，优先压：

1. 目录。
2. caption。
3. 图尺寸。
4. 重复段落。
5. 空白 float。

不要一味删图。图可以小而密地保留。

## 8. 最终检查清单

### 8.1 代码检查

```powershell
conda --no-plugins run -n mcm python scripts/run_all.py
conda --no-plugins run -n mcm pytest -q
```

期望：

```text
7 passed
```

### 8.2 LaTeX 编译

```powershell
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

检查：

```powershell
pdfinfo paper/main.pdf
rg -n "LaTeX Warning|Overfull|Undefined|undefined|Label\(s\)|Rerun" paper/main.log
```

期望：

1. 页数符合要求。
2. 无 undefined references。
3. 无 overfull hbox。
4. References 在目录里。
5. Summary 标题存在。
6. 最后一页不是大片空白。

### 8.3 人眼检查

必须人工看 PDF：

1. 摘要是否满而不乱。
2. 目录是否一页。
3. page 13、page 17 这类中间页是否空。
4. 图是否过大。
5. 表是否太少。
6. 公式是否足够解释模型。
7. caption 是否简短。
8. memo 是否清楚。
9. 论文是否像一篇完整建模论文，而不是代码报告。

## 9. 分批 commit 策略

推荐提交顺序：

```text
chore: initialize project structure
data: add official problem data and source log
env: configure mcm analysis environment
analysis: add data reconstruction pipeline
analysis: add fan support inference and validation
analysis: add counterfactual and sensitivity diagnostics
figures: add generated and concept visuals
paper: draft full report
paper: polish typography and figure layout
paper: deepen analysis and restore diagnostics
paper: add audit communication section
docs: add end-to-end workflow SOP
```

经验：

1. 每次 commit 只表达一个阶段。
2. 不要把代码、论文、图片、环境大杂烩成一次提交。
3. 用户要求“分批 commit”时，必须真的分批。
4. 每次提交前跑测试或至少说明为什么没跑。

## 10. 本项目关键踩坑与修正

### 问题 1：论文太短，像水文

修正：

1. 学优秀论文，不只学格式，还学分析层数。
2. 增加模型诊断、识别边界、公式解释、案例分析和风险控制。
3. 保持图表紧凑，而不是放大凑页数。

### 问题 2：摘要没有 Summary 标题

修正：在 summary sheet 明确写 `Summary`。

### 问题 3：没有目录或目录缺 References

修正：

```latex
\tableofcontents
\clearpage
\phantomsection
\addcontentsline{toc}{section}{References}
```

如果目录变两页，压缩目录字号和行距。

### 问题 4：页面太空

修正：

1. 缩小普通图。
2. 缩短 caption。
3. 用表格、公式、段落解释填充逻辑空白。
4. 避免一页只有一两张图。
5. 必要时固定关键 float 顺序，防止图表乱飞。

### 问题 5：表格太少、公式太少

修正：

1. 把每个模型的输入、输出、诊断写成表。
2. 把核心 rule、constraint、objective、threshold 写成公式。
3. 对公式解释其意义，而不是只摆出来。

### 问题 6：AI 图和代码图混用不清

修正：

1. AI 图放 `figures/concept/`。
2. 代码图放 `figures/generated/`。
3. 数值证据必须来自代码图。
4. AI 图只做 workflow、mechanism、memo card 等概念图。

### 问题 7：图被删了导致内容变薄

修正：

1. 不轻易从正文移除图。
2. 如果图太占空间，缩小或改成紧凑布局。
3. 保持 `figure_manifest.csv`，检查哪些图已使用。

### 问题 8：References 单独挤出额外页

修正：先看是正文超了还是目录超了。本项目是目录多出一页，通过压缩目录回到总 25 页。

### 问题 9：权限导致 commit/push 中断

修正：

1. 先确保文件已保存和编译成功。
2. 权限恢复后从 `git status` 继续。
3. 不要重做论文内容。
4. 按顺序跑测试、`git add`、`git commit`、`git push`。

## 11. 下次最短可执行流程

1. 用户给出题目、数据、官方要求、既定思路文档和本 SOP。
2. 助手读官方题目、既定思路和优秀范文。
3. 助手建立项目结构和 private GitHub 仓库。
4. 助手复用 `mcm` 环境，补齐依赖。
5. 助手写并运行 `scripts/run_all.py`。
6. 助手生成所有代码图、表、报告。
7. 助手列出 AI 图 prompt 和目标路径。
8. 用户生成 AI 图并放入 `figures/concept/`。
9. 助手写论文第一版。
10. 助手对照优秀论文补充诊断层、公式层、案例层、风险层。
11. 助手编译并检查 Summary、目录、References、页数、图表密度。
12. 用户肉眼审阅并指出不满意处。
13. 助手继续压实版面和补实质内容。
14. 助手跑测试、编译、检查 PDF。
15. 助手分批 commit 并 push。

## 12. 最终交付物

最终项目至少应包含：

```text
paper/main.pdf
paper/main.tex
reports/key_results.csv
reports/figure_manifest.csv
reports/data_audit_report.md
reports/sanity_check_report.md
reports/submission_checklist.md
reports/full_workflow_from_zero_to_final_paper.md
figures/generated/*.png
figures/concept/*.png
tables/*.tex
data/processed/*.csv
src/<package_name>/*.py
tests/*.py
```

最终 Git 状态应为干净：

```powershell
git status --short
```

应无输出。

最后一批检查：

```powershell
conda --no-plugins run -n mcm pytest -q
pdfinfo paper/main.pdf
git log --oneline -5
```

本项目最终状态：

1. PDF 总页数：25 页。
2. 测试：7 passed。
3. 论文包含 Summary、目录、References。
4. 图表、公式、诊断、案例、敏感性、审计沟通层均已补齐。
5. 最新论文相关提交包括：
   - `paper: deepen analysis and restore diagnostics`
   - `paper: add audit communication section`

