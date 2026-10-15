# 参与开发

使用 Python 3.10+。运行时保持标准库依赖；若要增加网络或平台适配，先说明如何保持本地模式独立可用。

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m careerflow demo --output ../careerflow-smoke
python scripts/build_skill.py --output dist/career-workflow-skill.zip
```

`demo` 和 ZIP 输出使用新路径，重复执行请选择新目标。演示产物只是合成流程样本，不作为内容生成质量指标。测试使用临时目录，不连接真实账号。

修改 Skill 时只把共用路由放进 `SKILL.md`，阶段特有内容放进相应参考资料，确保脱离本仓库后的安装目录也可使用。核对相对链接、调用示例和实际 CLI；新增机制应对应真实需求，避免堆叠通用提示词。

修改存储或导出时，覆盖会影响用户数据的可观察行为：失败是否留下部分写入、重复是否幂等、不同岗位和轮次是否独立、时区和公式注入是否正确处理。用合成材料复现，不提交个人简历、招聘邮件、真实 Offer 或平台资源标识。

构建发行包：

```sh
python -m pip install build
python -m build
python scripts/build_skill.py --output dist/career-workflow-skill.zip
```

提交说明写清问题、行为变化和验证。核心数据契约变更需说明旧工作区如何处理。CI 在 Windows、Linux、macOS 上执行同一测试集和 Skill 打包；本机通过不能代替其他平台验证。
