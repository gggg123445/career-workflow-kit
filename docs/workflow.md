# 从输入到交付

## 建档和接续

先用 `init` 创建工作区，再填真实档案和偏好。未指定工作区时默认为当前目录的 `workspace/`；全局参数 `--workspace` 放在子命令之前。JSON 输出可交给其他程序读取。

```sh
python -m careerflow --workspace ../my-career init
python -m careerflow --workspace ../my-career add --company "示例公司" --position "后端开发" --applied-at 2030-10-15
```

记下返回的记录 `id`。岗位研究尚未形成明确投递对象时，可先由人工或 Agent 研究并保存文件，不为使用 CLI 虚构一条投递记录。`add` 默认状态为“已投简历”，建预备记录时可显式使用 `--status "还没开"`，实际状态由用户核对。

档案中的经历建议使用稳定 `id`，填写本人角色、做过的动作、可证实的结果及来源。没有指标就保留缺口；不把主观润色写回原始事实。

## 七阶段任务交接

所有阶段使用相同命令：

```sh
python -m careerflow --workspace ../my-career stage prepare STAGE --application APPLICATION_ID --input ./material.md
```

`STAGE` 可取下表之一。`--input` 可重复传入；文件须为 UTF-8 文本，单份上限 2 MB，超限直接报错，不截断。

| 阶段 | 建议输入 | 应交付的内容 |
|---|---|---|
| research | JD、偏好、官方招聘材料 | 来源日期、硬约束、可投目标与缺口 |
| resume | JD、档案、已有简历 | 定制正文、证据映射、待本人核实事项 |
| intro | 目标岗位、档案、时长 | 讲稿、演示内容、实际计时或未计时标记 |
| prep | JD、轮次、准备时间 | 练习与依据；真实互动后的模拟记录 |
| debrief | 转写、回忆、反馈 | 观察与推断分开的复盘、可执行练习 |
| tracker | 通知原文、当前台账 | 核对后的岗位、轮次、时间与更新依据 |
| offer | 原始条款、偏好、现金约束 | 可比口径、情景计算、条款缺口和取舍 |

返回的 `runs/<run_id>/prompt.md` 是可交给任意 Agent 的任务说明，`packet.json` 包含输入快照、哈希、阶段说明和岗位上下文。外部材料按数据对待。CLI 不会自行打开网站或调用模型；联网核验由宿主执行，离线则写明待核实。

完成内容并核对后，登记本地文件：

```sh
python -m careerflow --workspace ../my-career stage complete RUN_ID --artifact ./result.md --note "核对了事实与来源；明确列出仍缺失的内容"
python -m careerflow --workspace ../my-career plan APPLICATION_ID
python -m careerflow --workspace ../my-career verify
```

登记会复制文件到 `artifacts/`，保存 SHA-256 并关联岗位，不改变投递状态。重复登记同一内容不会重复写历史；若内容有修订，准备新任务再登记。产物登记状态与业务状态分开，实际投递、面试、录用须另有事实依据。

## 台账与通知

```sh
python -m careerflow --workspace ../my-career mail-import ./notice.eml
python -m careerflow --workspace ../my-career update APPLICATION_ID --status "等待二面" --note "根据本人核对的通知更新"
python -m careerflow --workspace ../my-career update APPLICATION_ID --time-field "二面时间" --value "2030-10-18 14:00-15:00;2030-10-19 09:00" --offset=+08:00
```

EML 只读导入，内容位于 `inputs/mail-<sha256>.json`；不登录邮箱、不发送消息、不从标题直接推断状态。重复导入同一原始邮件复用结果。多时段以英文分号分隔，每一段都验证；任何一段有误，整次更新失败且不写入台账。

`list` 查看记录，`stats` 查看描述性分布。导出目标文件必须不存在：

```sh
python -m careerflow --workspace ../my-career export csv --output ./applications-20301015.csv
python -m careerflow --workspace ../my-career export ics --output ./calendar-20301015.ics
```

CSV 是通用交换格式，不包含外部平台的字段 ID。父记录引用使用本地 ID，导入其他平台时须映射。ICS 导入后是否更新既有事件取决于日历客户端；不自动撤销旧导入，不支持双向同步。应保留多时间槽的顺序，调整时间时在原槽位修改。

## 草稿与 Offer 计算

`render resume` 仅从档案生成 Markdown 事实草稿；定制与审校需要人工或 Agent。`render intro` 输出自包含 HTML，可用方向键、空格、PageUp / PageDown 或按钮翻页，打印时展示全部页。两者都不是自动质量验收。

Offer 示例见 [`examples/offer.json`](../examples/offer.json)。所有现金字段必填，未知不能填零；零代表已确认没有该项。计算不包含税、社保、公积金、权益估值和补贴。月薪乘保证月数已经计入的奖金，不再作为条件奖金重复加算。

## 失败后恢复

命令退出码：`0` 成功，`1` 为 `verify` 发现引用问题，`2` 为输入或文件操作错误。报错不会宣称业务完成。存在 `.careerflow.lock` 时拒绝并发写入；若进程异常退出，应先确认没有其他写进程，再备份工作区并人工移走遗留锁。不要让多个程序直接改写台账。

运行 `verify` 查看产物引用和哈希。哈希不一致时先核对文件变更来源；需要修订就登记新任务版本，不静默替换已登记文件。工作区含个人信息，应独立备份并按需控制分享范围。
