# Contributing to ecommerce-product-investigator

感谢你对本项目的关注！以下是参与贡献的指南。

---

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/Saber-doudou/ecommerce-product-investigator.git
cd ecommerce-product-investigator

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r scripts/requirements.txt
pip install -r requirements-dev.txt
```

## 运行测试

```bash
# 运行全部测试
pytest

# 运行单元测试
pytest tests/ --ignore=tests/integration

# 运行集成测试
pytest tests/integration/

# 带详细输出
pytest -v
```

## 代码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用 4 空格缩进，不用 Tab
- 行宽限制 120 字符
- 函数和类必须有 docstring
- 变量命名：`snake_case`（函数/变量）、`PascalCase`（类）
- 常量命名：`UPPER_SNAKE_CASE`

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响逻辑）
- `refactor`: 重构（不新增功能/不修复 Bug）
- `test`: 测试相关
- `chore`: 构建/工具链变更

**示例**：
```
feat(profit_calc): 新增税率敏感度分析维度
fix(maishou_common): 修复 close_session() 竞态条件
docs(crossborder-guide): 补充 JP/UK 市场利润对比
```

## Pull Request 流程

1. Fork 本仓库
2. 从 `master` 创建特性分支：`git checkout -b feat/my-feature`
3. 提交更改并确保测试通过
4. 推送到你的 Fork：`git push origin feat/my-feature`
5. 创建 Pull Request，填写说明

### PR 检查清单

- [ ] 代码通过 `pytest` 全部测试
- [ ] 新增功能有对应测试覆盖
- [ ] docstring 已更新
- [ ] CHANGELOG.md 已更新（如适用）

## Issue 提交规范

**Bug 报告**请包含：
- Python 版本
- 操作系统
- 复现步骤
- 期望行为 vs 实际行为
- 错误日志（如有）

**功能建议**请包含：
- 使用场景描述
- 预期行为
- 是否愿意实现

---

感谢贡献！🎉
