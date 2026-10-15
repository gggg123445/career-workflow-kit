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

## 覆盖的工作

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

打开返回目录中的 `prompt.md` 与 `packet.json`，交给人工或任意 Agent 执行。完成内容后用返回的 `run_id` 登记：

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

模板保留所提供校招进程表的 **16 个通用字段、21 个状态**，并转换为可移植 JSON 契约；未包含原表链接、资源 ID 或私人记录。查看：

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
