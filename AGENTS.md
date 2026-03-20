# AGENTS.md

## 仓库定位

本仓库是 **AstrBot 钓鱼娱乐插件** 仓库，提供钓鱼、背包、商店、市场、抽卡、交易所、社交互动、Web 后台管理等完整玩法。

- 主框架仓库：<https://github.com/AstrBotDevs/AstrBot>
- 插件开发 Wiki：<https://docs.astrbot.app/dev/star/plugin-new.html>

AI 在本仓库工作时，必须优先理解这是一个 **AstrBot Star 插件**，而不是独立应用。任何实现都应尽量复用当前插件既有分层与数据模型，不要脱离 AstrBot 插件生命周期凭空重构。

## 先读这些文件

开始修改前，建议按下面顺序建立上下文：

1. `main.py`
   - 插件入口、依赖装配、命令注册中心、后台管理启停入口。
   - 新功能通常最终都需要在这里接线。
2. `_conf_schema.json`
   - 插件配置 schema，新增配置项时必须同步更新。
3. `metadata.yaml`
   - 插件元数据。
4. `core/domain/models.py`
   - 主要领域模型定义。
5. `core/services/`
   - 业务逻辑主层，绝大多数规则修改都应落在这里。
6. `core/repositories/`
   - SQLite 数据访问层。
7. `handlers/`
   - AstrBot 事件与命令处理层，负责解析输入、调用 service、拼装输出。
8. `manager/server.py`
   - Quart 后台管理入口。
9. `tests/`
   - 现有单元测试，修改核心算法或工具函数时优先补测试。

## 当前代码结构

### 1. 插件入口层

- `main.py`
  - `FishingPlugin(Star)` 是插件主类。
  - 这里负责：
    - 从 AstrBot 配置中读取并整理 `game_config`
    - 初始化数据库与 migration
    - 装配 repository / service / handler
    - 用 `@filter.command`、`@filter.regex`、`@filter.permission_type` 注册命令

### 2. 业务分层

- `handlers/`
  - 面向聊天命令和事件。
  - 只做输入解析、权限判断、结果消息拼装。
  - 不要把复杂业务规则继续堆进 handler。

- `core/services/`
  - 业务规则主层。
  - 钓鱼、背包、市场、交易所、红包、借贷、骰宝、成就等逻辑主要在这里。
  - 新规则优先加在 service，而不是 `main.py` 或模板里。

- `core/repositories/`
  - SQLite 仓储层。
  - 负责 CRUD、查询、事务边界附近的数据访问逻辑。
  - 如果只是字段读写或查询条件变化，优先改 repo。

- `core/domain/`
  - 领域模型与 loan 相关模型。

- `core/database/`
  - 数据库连接与 migration。
  - 新增表或字段时，优先通过新增 migration 文件实现，保持兼容旧存档。

### 3. 展示层

- `draw/`
  - 图片渲染相关逻辑，例如图鉴、背包、排行、帮助等。
  - 这里适合放绘制逻辑，不适合塞业务判断。

- `manager/`
  - Quart Web 后台。
  - `manager/server.py` 为入口。
  - `templates/` + `static/` 为后台页面资源。
  - 适合做管理后台 CRUD，不适合复制核心业务逻辑；应尽量复用 service。

### 4. 测试层

- `tests/`
  - 当前已有纯 Python 单元测试。
  - 测试通过 `monkeypatch` 模拟 `astrbot.api`，所以很多核心逻辑可以脱离完整 AstrBot 环境验证。

## 开发落点规则

### 新增聊天命令

推荐路径：

1. 在对应 `handlers/*_handlers.py` 中新增处理方法。
2. 如有业务规则变更，在 `core/services/` 中新增或扩展 service 方法。
3. 如需新数据访问，在 `core/repositories/` 中补查询或写入逻辑。
4. 在 `main.py` 中通过 `@filter.command` / `@filter.regex` 接线。
5. 补充必要测试。

不要直接把完整业务流程写进 `main.py` 的命令函数里。

### 修改业务规则

- 概率、结算、价格、库存、经济、冷却、成就等奖励逻辑，优先改 `core/services/`。
- 仅当输入解析或回复文案需要变化时，再动 `handlers/`。

### 新增配置项

必须同时检查这些位置：

1. `_conf_schema.json`
2. `main.py` 中的配置读取和 `game_config` 组装
3. 实际消费该配置的 service

不要只改 schema 或只改默认值，否则很容易出现“配置写了但业务没读到”的问题。

### 修改数据库结构

- 在 `core/database/migrations/` 下新增 migration，延续当前编号风格。
- 尽量保持向后兼容，避免破坏旧用户存档。
- 如果只是查询优化，不要轻易改 schema。

### 修改后台管理

- 页面结构在 `manager/templates/`
- 前端行为在 `manager/static/js/`
- 样式在 `manager/static/css/`
- 后端路由在 `manager/server.py`

涉及业务校验时，优先复用 service，不要在后台路由里重新写一套规则。

## 本仓库的重要事实

### 1. 这是插件，不是独立机器人项目

- 需要遵循 AstrBot 的 Star 插件模式。
- 命令注册集中在 `main.py`。
- 框架对象主要来自 `astrbot.api`、`astrbot.api.event`、`astrbot.api.star`。

### 2. 数据目录不是固定写死在仓库内

`main.py` 中优先通过 `self.context.get_data_dir(self.plugin_id)` 获取数据目录，失败时才回退到 `data/`。

因此：

- 不要假设数据库一定在仓库根目录。
- 涉及缓存、临时文件、图片输出时，优先沿用现有 `data_dir` / `tmp_dir` 机制。

### 3. 插件标识以当前代码实际值为准

当前代码中可见：

- `metadata.yaml` 的 `name` 为 `astrbot_plugin_fishing_again`
- `main.py` 中 `plugin_id` 也为 `astrbot_plugin_fishing_again`

开发时不要想当然改回其他名称，除非明确要做兼容性迁移。

### 4. 旧存档兼容性很重要

README 与现有实现都明确强调兼容旧数据。任何涉及：

- 用户表
- 背包实例
- 市场/交易所数据
- 成就、称号、红包、借贷等历史数据

的改动，都要优先考虑迁移成本与兼容路径。

### 5. Service 层已经承担大量核心职责

例如：

- `fishing_service.py` 管理钓鱼、自动钓鱼、每日刷新等核心流程
- `fish_weight_service.py` 管理权重与 EV 拟合逻辑
- 交易所、市场、红包、借贷、骰宝也都有相对独立的 service

新增逻辑前先搜索是否已有相近 service，不要重复造轮子。

## AI 开发建议

### 建议工作顺序

1. 先定位需求属于哪一层。
2. 用 `rg` 搜现有功能、命令、数据模型和 service。
3. 先读再改，优先沿用已有命名和返回结构。
4. 小步修改，尽量让 handler、service、repo 职责清晰。
5. 核心逻辑改动后补测试或至少跑相关测试。

### 推荐搜索关键词

- 命令注册：`@filter.command`
- 管理员命令：`@filter.permission_type`
- 正则入口：`@filter.regex`
- 后台入口：`create_app(`
- migration：`run_migrations`
- 核心钓鱼：`go_fish`
- 权重算法：`FishWeightService`

### 修改原则

- 优先复用现有 service / repo，不要平行再造一套实现。
- 优先做增量修改，不做大范围无收益重构。
- 输出文案可保持当前中文风格一致。
- 代码注释语言保持与周边文件一致，当前仓库以中文注释为主。

## 测试与验证

跑python需要找框架层的虚拟环境:

AstrBot\data\plugins\plugins....  -<插件目录
AstrBot\.venv -<这里是虚拟环境目录

常用本地验证方式：

- 运行测试：`pytest` 如果虚拟环境没有安装，则直接安装再测试
- 运行指定测试：`pytest tests/test_weight.py`

修改下列内容时，建议优先补或跑测试：

- `core/services/fish_weight_service.py`
- `utils.py`
- 输入解析逻辑
- 税收、交易所、借贷、背包结算逻辑

如果改动依赖 AstrBot 运行时行为，单元测试之外还应结合插件实际加载路径检查命令是否能被框架识别。

## 提交与协作约定

- 参考 `CONTRIBUTING.md`
- 如需发起 PR，目标分支应为 `develop`，不是 `main`
- 提交信息建议使用中文，并带上清晰类型前缀：`feat` / `fix` / `refactor` / `test` / `docs`

## 对 AI 最重要的一句话

在这个仓库里，**先判断需求属于 handler、service、repo、migration、manager 中哪一层，再动手修改**。优先做贴合现有结构的增量开发，而不是跨层堆逻辑或一次性大改。
