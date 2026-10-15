# 本地数据契约与可移植运行

工作区用 `--workspace` 显式指定，默认 `./workspace`。不使用开发者机器路径、用户名或固定账号。以下文件均包含用户私有数据，放在源码仓库外最方便；初始化还会在工作区写忽略规则。

| 文件/目录 | 用途 |
|---|---|
| profile.json | 经历事实，basic/headline/education/experiences/skills/publications |
| targets.json | 城市、岗位方向、约束和决策偏好 |
| applications.json | schema_version、revision、applications、runs、events |
| inputs/ | 用户主动提供的本地材料或离线 EML 导入 |
| runs/<run_id>/packet.json、prompt.md | 本次上下文快照和仅含当前阶段的指令 |
| artifacts/<run_id>.<后缀> | 已登记的产物副本及台账中的 SHA-256 |
| exports/ | CSV、ICS、排版草稿等显式导出文件 |

`profile.json` 和 `targets.json` 可由用户或 Agent 编辑，先读再改，保留未经请求修改的字段。台账尽量通过 CLI 变更，以保留历史、锁与原子写入。台账文件不支持多个设备自动合并；同步盘冲突须人工合并。

每次投递有稳定 ID；职位相同但批次不同也可分开。状态使用 `template` 返回的 21 个选项，可根据真实流程跳步，不强制所有人经历相同流程。历史事件包含创建、状态/时间更新和阶段交接。阶段完成只表示产物已登记及核对说明已保存，不自动改变招聘状态。

任务准备会把输入复制到任务快照中，不会发送到任何网络。可以把 `prompt.md` 交给选定的人工或 Agent；如果使用云端模型，由调用方决定数据发送与授权范围。本工具不内置或自动调用模型 API。

复现示例：

```text
careerflow --workspace ./my-career init
careerflow --workspace ./my-career add --company "示例公司" --position "目标岗位"
careerflow --workspace ./my-career stage prepare resume --application app-返回的ID --input ./jd.md
careerflow --workspace ./my-career stage complete run-返回的ID --artifact ./resume.md --note "核对经历和日期；性能指标仍待补"
careerflow --workspace ./my-career verify
```

若未安装命令，使用技能自带 `python scripts/careerflow.py` 前缀。通用宿主只需能读取 SKILL.md、选择 reference、运行 Python。安装器 `skill install --target <新目录/career-workflow>` 携带完整运行时，复制后的技能不依赖原仓库。宿主如何发现技能、是否自动刷新，由宿主能力决定，不保证每个平台都支持热加载。

并发写操作遇锁立即失败；进程崩溃可能遗留 `.careerflow.lock`。只有核对旧进程已退出后再移除锁文件。原子写入防止半截 JSON，不能代替定期备份或多设备冲突解决。
