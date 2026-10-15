# 验证记录 · v0.1.0

本记录针对本仓库的新可移植实现。原个人项目的历史审查结果不作为本版本的通过记录。

## 本地实测

2026-10-15，Windows、Python 3.12.14：

- 31 项单元与集成测试通过：同公司不同岗位、历史与幂等更新、严格日期和时段、事务回滚与互斥、当前阶段任务包、产物副本和哈希、CSV 公式防护、跨轮次 ICS 身份及时区、邮件全文和重复导入、显式现金情景计算。
- Skill 入口通过 `skill-creator` 的结构校验；安装目录在临时隔离路径中通过 Python `-I` 执行，不依赖源码、`PYTHONPATH` 或用户包，成功完成合成七阶段交接。
- 合成演示登记七份明确标记的交接文件，导出 17 列 CSV、三条 ICS 事件、Markdown 事实草稿与 HTML，引用与摘要验证通过。
- Chromium 实测 HTML：按钮、左右 / PageUp / PageDown / 空格翻页、首末页边界、打印前后恢复、390px 窄屏无横向溢出；无脚本异常、无网络请求。已检查桌面及窄屏截图。

## 可复现命令

```sh
python -m pip install .
python -m unittest discover -s tests -v
python -m careerflow demo --output ../careerflow-validation-demo
python scripts/build_skill.py --output dist/career-workflow-skill.zip
```

目录与输出文件需使用新路径。浏览器检查是本次发布的交互实测，未加入默认标准库测试集；标准库测试检查 HTML 转义与无外链资源。

## 自动化与发行

[GitHub Actions](https://github.com/gggg123445/career-workflow-kit/actions/workflows/ci.yml) 配置 Windows、Linux、macOS × Python 3.10 / 3.12 六组环境，执行安装、同一测试集、演示与 Skill 打包；另有 Python 源码包和 wheel 构建任务。以对应提交的运行结果为准。

发行格式：通用 Python wheel、源码包、携带运行时的 Skill ZIP，以及各文件的 SHA-256 清单。核心代码无运行时第三方依赖；首次构建安装可能需要获取构建工具。所有公开样本为虚构内容。

## 实测边界

七阶段演示验证文件交接和状态存储，不证明研究、简历、面试诊断的专业质量。自动测试没有连接真实邮箱、飞书或外部日历，没有执行真实投递、发信、云端写入或合同核验。没有宣称不同宿主都能热刷新技能。ICS 是否合并既有事件由目标日历软件决定，当前没有双向同步或删除传播。
