# career-workflow-kit

[![CI](https://github.com/gggg123445/career-workflow-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/gggg123445/career-workflow-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

本地优先的求职全流程工具，提供 **独立工作流** 与 **按需加载的 Agent Skill** 两种运行模式。支持校招和跳槽；核心只使用 Python 标准库，无运行时第三方依赖，无平台账号要求。

**Local-first career workflow and a portable, progressively loaded agent skill.** Python 3.10+, MIT, no runtime dependencies. All CLI operations run locally. An agent or a person supplies the research, writing and judgment.

## 两种运行模式

| 模式 | 如何运行 | 适合的场景 |
|---|---|---|
| 独立工作流 | CLI 准备任务包 → 人工或任意 Agent 完成 → 登记产物 | 不绑定模型平台，希望自行安排工具与执行顺序 |
| 动态 Skill | 宿主先读 `SKILL.md`，再按当前阶段加载一份参考资料 | 在支持文件型技能的 Agent 中持续处理求职任务 |

两种模式使用同一个数据契约和运行时，可以交接和断点续做。Skill 安装包自带运行时，移走原仓库后仍能执行。技能发现、刷新和热加载由各宿主实现；本项目提供目录安装与按阶段读取接口，不承诺所有宿主自动刷新。

## 功能总览

围绕“一个岗位从了解、准备、面试到决策”的过程组织材料。每条投递记录有稳定 ID，同一岗位的 JD、简历版本、准备包、复盘和 Offer 分析可关联保存；切换 Agent 或更换运行模式后，可以从已有文件接着做。

可以按完整链路使用，也可以只处理当前任务：例如改一份简历、做一次文字模拟面试、整理一封二面通知，或对比两份 Offer。

| 阶段 ID | Skill / 人工内容工作 | CLI 确定性操作 |
|---|---|---|
| `research` | 核验岗位来源、约束与投递顺序 | 保存研究任务与产物关联 |
| `resume` | 按 JD 选择真实经历、定制简历 | 从档案生成事实草稿；登记定制版本 |
| `intro` | 准备讲稿、自我介绍与演示内容 | 生成无外链 HTML 事实演示稿 |
| `prep` | 笔试练习、模拟面试、追问 | 交接输入、保存准备包与版本 |
| `debrief` | 从真实转写或回忆复盘并安排练习 | 关联岗位、复盘材料与后续任务 |
| `tracker` | 核对通知中的岗位、轮次、时间 | 台账历史、EML 全文导入、CSV / ICS 导出 |
| `offer` | 比较条款、偏好与取舍 | 根据显式输入计算税前现金情景 |

内容研究与判断由使用者或宿主 Agent 执行，CLI 不调用模型。`prepare` 生成任务包，`complete` 登记核对后的文件；它们不自动证明内容质量，也不表示已经投递、发信或写入云端。

## 七个阶段能具体做什么

### 1. 岗位研究与投递优先级 · `research`

把“想找什么工作”整理成有依据的候选岗位和下一步动作。

- **输入**：目标城市、岗位方向、毕业时间等硬约束、个人经历，以及已有 JD 或招聘公告。
- **内容工作**：检查招聘资格与地点，逐项对照经历证据，比较实际差距、截止时间和准备成本。宿主有检索能力时核验企业招聘页与正式公告，并记录来源和核验日期；离线时比较用户提供的材料，保留开放状态待核验项。
- **交付**：可比较的岗位清单、推荐理由、资格缺口、投递顺序与下一步动作。冲刺 / 主力 / 备选用于分配准备精力，不表示录取概率。
- **工具衔接**：采纳岗位后通过 `add` 建立记录，后续材料按同一 ID 关联。尚未确定目标时可先研究，不需要为了使用工具虚构投递。

示例请求：“结合我的档案比较这三份 JD，优先上海，列出硬性不满足的条件和本周准备顺序。”

### 2. 经历建档与岗位定制简历 · `resume`

把已有经历变成可追溯的事实档案，再按不同 JD 组织投递稿。

- **输入**：真实经历、已有简历、项目材料与目标 JD。档案保留经历 ID、时间、个人职责、行动、结果及指标依据；材料解析使用宿主具备的工具。
- **内容工作**：区分 JD 的硬条件、工作职责与加分项，建立“要求 → 经历证据 → 缺口 → 改写动作”对照。调整项目顺序与表达，说明做了什么、如何验证和为何有效；保留个人贡献与团队成果的区别。
- **交付**：定制简历正文、JD 对照、关键改动说明和待补事项。不同岗位分别关联版本，重跑同一阶段可以保留旧稿。
- **工具衔接**：`render resume` 将档案排成 Markdown 事实草稿；定制和审校由 Agent 或人工继续完成。PDF / Word 导出取决于宿主工具，CLI 本身不提供这两种格式的排版引擎。

示例请求：“按这份后端 JD 改简历，保留经历 ID 和改写依据；没有数据的结果标待补，不编匹配百分比。”

### 3. 自我介绍、讲稿与 HTML 演示 · `intro`

围绕目标岗位选择最有说服力的经历，让讲稿与页面表达同一组事实。

- **输入**：职业档案、目标岗位、使用场景和期望时长，例如 1 / 3 / 5 分钟。
- **内容工作**：提炼个人定位，选取一到两段关键经历，组织开场、证据与求职动机；长版本增加证据深度，并给出分页要点与时间分配。
- **交付**：可直接讲的稿件、逐页提纲、需要朗读验证的时间安排，以及可选 HTML 演示。字数估算与实际朗读计时分开记录。
- **工具衔接**：`render intro` 从档案生成自包含 HTML 事实草稿，无 CDN 或在线资源依赖；支持上一页 / 下一页、方向键、空格和 PageUp / PageDown，带页码、首尾边界控制及打印全部页面的逻辑。可在此基础上按讲稿调整内容。

示例请求：“为这个岗位准备 3 分钟自我介绍，重点讲两个项目，给我讲稿、分页内容和待计时标记。”

### 4. 笔试备考与互动模拟面试 · `prep`

根据岗位要求和剩余时间安排练习，让准备内容与本人经历相连。

- **输入**：JD、关联简历、面试轮次、已有薄弱点和可用准备时间。
- **内容工作**：按重要性与可补齐程度安排知识点、代码题、项目追问和行为问题。重点题给出考察点、回答或解题框架、追问方向与验证方法；用户回忆题、可核验公开题和生成练习分别标注来源。
- **交付**：备考计划、重点题与参考框架、代码验证结果或未执行说明。互动模拟采用一问一答，在用户回答后继续追问，结束时根据实际回答整理反馈与练习。
- **工具衔接**：CLI 准备带岗位上下文的任务包并登记准备材料；出题、问答与反馈由宿主 Agent 执行。代码运行、语音交互取决于宿主能力，文字模拟不生成语速或停顿评价。

示例请求：“我还有两天准备这场面试，先排计划，再围绕简历里的数据项目逐题追问，等我回答后再反馈。”

### 5. 面试复盘与针对性练习 · `debrief`

把真实面试材料整理成有证据的问题诊断，再转成下一轮能执行的改进动作。

- **输入**：面试转写、文字回忆、反馈，以及对应岗位和简历。先说明材料是否完整、说话人是否明确、是否有可信时间信息。
- **内容工作**：还原 Q/A，检查是否切题、知识是否准确、案例是否支持结论、取舍与验证是否讲清。将可观察的表达问题与对面试官意图的推断分开，不补写缺失回答。
- **交付**：Q/A 摘要、重点问题的“原句 → 影响 → 保持事实的改写 → 下一次练习”，并优先给出两到三个最值得改进的方向。
- **工具衔接**：复盘文件登记到对应投递记录，后续 `prep` 任务可显式传入复盘材料继续训练；任务关联由文件和记录 ID 维护，不自动宣称能力已提升。

示例请求：“复盘这份二面回忆，区分我确实没答到的内容与可能的追问意图，再给三项下次能检查的练习。”

### 6. 投递台账、通知整理与日历导出 · `tracker`

统一记录不同公司、岗位和面试轮次，减少通知分散、时间遗漏及同公司多岗位混淆。

- **输入**：明确进展、招聘通知原文、当地时间与时区。`.eml` 可通过 `mail-import` 离线导入，保存解码后的完整正文及来源摘要；相同原始邮件重复导入复用结果。
- **内容工作**：核对公司、岗位、批次、考试类型、轮次、固定时间或截止时间、入口与设备要求。匹配不明时保留原文与待确认项，不凭公司名更新另一岗位，也不把未知轮次填成一面。
- **交付**：核对后的台账、更新依据、歧义清单，以及供其他软件导入的 CSV / ICS 文件。状态采用校招模板的 21 个选项，可以按企业实际流程跳步。
- **工具衔接**：`add` / `list` / `update` 管理记录，更新保留历史；五类时间字段支持固定时段、截止时间与分号分隔的多场安排。非法日期、逆序时段或混杂无效文本会拒绝整次更新。ICS 按岗位、轮次和时间槽建立 UID，转换为 UTC 并包含提醒；`stats` 展示状态和城市分布。

示例请求：“读取这封二面通知，先核对是不是这个岗位；确认后记录时间，并导出我可以自行导入日历的 ICS。”

### 7. Offer 口径统一与决策辅助 · `offer`

把不同薪酬结构放到同一口径下，结合条款、岗位内容和个人偏好比较取舍。

- **输入**：Offer 原始条款、币种、月薪、保证发薪月数、保证津贴、条件奖金、首年签字费，以及团队、职责、地点和个人约束。未知值与已确认的零值分开。
- **内容工作**：区分保证现金、条件现金、一次性现金与权益，检查试用期、奖金条件、签字费返还和权益归属等缺口；结合成长、稳定、工作节奏和城市等因素说明选择理由。权重来自用户，不默认用单一综合分决定去向。
- **交付**：各 Offer 的可比口径表、现金情景、重要条件与待核实项，以及不同偏好下的取舍理由。权益单列说明，不直接当作可兑现现金。
- **工具衔接**：`offer-calc` 使用十进制计算用户显式提供的税前条目，输出下面四种口径；不自动填市场参数，也不计算税后、社保、公积金或股票价格。

| 计算输出 | 组成 |
|---|---|
| 年度保证现金 | 月薪 × 保证发薪月数 ＋ 保证年度津贴 |
| 条件奖金全额兑现时的年度现金 | 年度保证现金 ＋ 条件奖金 |
| 含签字费的首年保证现金 | 年度保证现金 ＋ 首年签字费 |
| 条件奖金全额兑现且含签字费的首年现金 | 年度保证现金 ＋ 条件奖金 ＋ 首年签字费 |

示例请求：“统一这两份 Offer 的保证现金与首年现金口径，把未确认奖金、签字费返还条件和股权单列，再结合我的偏好比较。”

## 贯穿全流程的能力

| 能力 | 具体行为与用途 |
|---|---|
| 共享事实档案 | `profile.json` 保存经历，`targets.json` 保存偏好；不同阶段复用同一份事实，任务包保存当次快照 |
| 独立岗位与版本关联 | 每条投递有稳定 ID；同公司不同岗位分开，同阶段可以多次执行，历史任务和已登记产物保留 |
| 可交接的任务包 | `stage prepare` 生成 `packet.json` 与 `prompt.md`，包含当前阶段说明、档案、岗位和显式传入的材料，可交给人工或任意能读文件的 Agent |
| 产物登记与核对说明 | `stage complete` 保存文件副本、SHA-256 与核对说明；`plan` 查看各阶段最新状态，`verify` 检查引用与文件摘要 |
| 按需加载 Skill | 先读取元数据与轻量入口，再只加载当前阶段资料；安装目录自带运行时，可脱离原仓库执行 |
| 本地文件交换 | Markdown 事实草稿、HTML 演示、CSV 台账、ICS 日历、邮件导入 JSON；阶段登记还接受 TXT、JSON、PDF、DOCX、PPTX 等文件，但不自动解析或生成所有这些格式 |
| 写入保护 | 台账写入使用独占锁和原子替换；导出、渲染和 Skill 安装拒绝覆盖已有目标；CSV 对可能触发表格公式的文本作防护 |
| 可选平台扩展 | 通用模板与本地记录 ID 可供独立适配器映射；现有核心在没有平台账号、连接器或模型 SDK 时仍可运行 |

一种典型用法是：先比较岗位并建档 → 按 JD 定制简历 → 准备自我介绍与笔面试 → 登记通知和时间 → 面后复盘并继续练习 → 统一 Offer 口径再作选择。进程台账贯穿其中，各阶段也可跳过、重跑或单独使用。

## 快速开始

需要可用的 Python 3.10 或更新版本。在 Windows 可将命令中的 `python` 换为 `py -3`，macOS / Linux 可换为 `python3`。

```sh
git clone https://github.com/gggg123445/career-workflow-kit.git
cd career-workflow-kit
python -m pip install .
python -m careerflow --version
python -m careerflow demo --output ./demo-workspace
```

演示使用虚构档案和公司，测试七阶段任务交接、三条日历事件及文件导出；七份占位产物有明确标记，不作为真实求职成果。`demo-workspace` 必须是尚不存在的目录。离线已有源码时也可直接运行：

```sh
python src/careerflow/skill/scripts/careerflow.py demo --output ./demo-workspace
```

真实工作使用独立的私人目录，建议放在仓库之外：

```sh
python -m careerflow --workspace ../my-career init
python -m careerflow --workspace ../my-career add --company "示例公司" --position "软件工程师" --city "上海"
python -m careerflow --workspace ../my-career list
```

编辑新建的 `profile.json` 填入真实经历，编辑 `targets.json` 填入偏好。用返回的 `id` 替换下面的 `APPLICATION_ID`；同一公司不同岗位分别建记录。

```sh
python -m careerflow --workspace ../my-career stage prepare resume --application APPLICATION_ID --input examples/jd.md
```

打开返回目录中的 `prompt.md` 与 `packet.json`，交给人工或任意 Agent 执行。完成内容后用返回的任务 `id` 替换下面的 `RUN_ID` 登记：

```sh
python -m careerflow --workspace ../my-career stage complete RUN_ID --artifact ./resume.md --note "已核对经历与 JD；量化结果仍待本人补充"
python -m careerflow --workspace ../my-career plan APPLICATION_ID
python -m careerflow --workspace ../my-career verify
```

`verify` 检查文件引用与 SHA-256，不评价简历质量。阶段可以跳过或重跑，不要求先把七项全部做完。完整操作见 [工作流指南](docs/workflow.md)。

## Skill 模式

### 安装与调用

将技能安装到宿主能够发现的目录；`--target` 是**尚不存在的技能文件夹本身**：

```sh
python -m careerflow skill install --target ../agent-skills/career-workflow
```

也可从 [Releases](https://github.com/gggg123445/career-workflow-kit/releases) 下载 Skill ZIP，解压得到 `career-workflow/`。将该文件夹放到宿主的技能目录，按宿主方式刷新发现。支持显式技能调用的宿主可以使用 `$career-workflow`；其他宿主可以直接读取其 `SKILL.md`。

技能目录包含入口、七阶段参考资料、数据契约、可选 UI 元数据和自带运行时的脚本：

```text
career-workflow/
├── SKILL.md
├── references/
├── agents/openai.yaml
└── scripts/
    ├── careerflow.py
    └── _runtime/careerflow/
```

独立测试安装后的技能，不需要 pip 安装本项目：

```sh
python ../agent-skills/career-workflow/scripts/careerflow.py --version
```

不要只复制源码里的 `skill/` 子目录来分发：自包含目录应由安装命令或发布 ZIP 生成。

### 动态按需加载

```sh
python -m careerflow skill catalog
python -m careerflow skill load
python -m careerflow skill load resume
```

第一步取元数据，第二步读取轻量入口，第三步只读取简历阶段。宿主可将这些输出接入自己的 Skill loader；没有专有 SDK 或必需 MCP 服务。例：“按这份 JD 改简历，保留事实依据”“复盘这份面试回忆”“核对这封通知里的二面时间”。

## 校招进程表与文件导出

模板保留所提供校招进程表的 **16 个通用字段、21 个状态**，并转换为可移植 JSON 契约；未包含原表链接、资源 ID 或私人记录。

| 字段用途 | 模板字段 |
|---|---|
| 岗位基本信息 | 投递公司、岗位、城市、网址链接 |
| 投递进展 | 投递状态、投递时间 |
| 考试与面试安排 | 测评时间、笔试时间、一面时间、二面时间、三面时间 |
| 辅助信息与关联 | 备注、邮件总结要点、薪资情况、AI状态判断、父记录 |

这些是交换模板字段，当前 CLI 提供其中的记录创建、状态、时间和备注更新；其余字段保留在数据契约中，供人工维护或适配器使用。`AI状态判断` 是保留字段，不表示导入邮件后会自动推断招聘状态。

```sh
python -m careerflow template
python -m careerflow --workspace ../my-career update APPLICATION_ID --time-field "二面时间" --value "2030-10-18 14:00-15:00" --offset=+08:00
python -m careerflow --workspace ../my-career export csv --output ./applications.csv
python -m careerflow --workspace ../my-career export ics --output ./calendar.ics
```

CSV 以稳定的 `application_id` 开头，后接 16 个模板字段。ICS 按岗位、轮次和时间槽生成独立事件，包含时区转换和提醒。严格时间语法、重复导入限制见 [tracker 参考资料](src/careerflow/skill/references/tracker.md)。导出文件供用户导入其他软件，CLI 不连接或修改飞书、邮箱、日历。

其他常用命令：

```sh
python -m careerflow --workspace ../my-career mail-import ./notice.eml
python -m careerflow --workspace ../my-career render resume --output ./facts-resume.md
python -m careerflow --workspace ../my-career render intro --output ./intro.html
python -m careerflow offer-calc examples/offer.json
python -m careerflow --workspace ../my-career stats
```

邮件导入保存全文与来源摘要，不自动判定状态；Offer 计算区分保证现金、条件奖金与首年签字费，不估算税后收入；统计仅展示当前分布，不虚构漏斗转化率。

## 数据与扩展

所有工作数据保存在用户指定目录，核心文件为 `profile.json`、`targets.json`、`applications.json`。写入使用独占锁和原子替换；阶段产物保留哈希与历史。初始化、导出、安装拒绝覆盖已有目标。公开示例全部为虚构材料。

接口和边界见 [架构说明](docs/architecture.md)、[数据契约](src/careerflow/skill/references/data-contract.md)。外部平台适配器可以基于稳定记录 ID 与本地契约单独实现；当前版本没有内置云同步、自动投递或邮件发送功能。

## 开发与验证

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/build_skill.py --output dist/career-workflow-skill.zip
```

测试与实测范围见 [验证记录](docs/validation.md)，贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。本仓库是从原个人工具中独立整理的新发行版，原项目的私有配置、经历、邮件和审查数据不属于发行包。

## 许可证

[MIT](LICENSE)。
