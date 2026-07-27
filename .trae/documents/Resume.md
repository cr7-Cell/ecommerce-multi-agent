# 个人简历

## 基本信息

| 项目 | 内容 |
|------|------|
| 求职意向 | 后端开发工程师 / AI Agent 开发工程师 |
| 技术方向 | 多智能体系统、LLM 应用开发、Python 后端 |

---

## 项目经验

### 跨境电商多智能体系统

**项目周期**: 2026年4月 - 2026年7月
**项目角色**: 核心架构设计与全栈开发
**项目地址**: 私有仓库

#### 项目概述

基于 MCP（Model Context Protocol）协议和 LangGraph 多智能体编排框架，从 0 到 1 设计并实现了一套跨境电商多智能体协作系统。系统包含 11 个专业 Agent（订单管理、物流追踪、客服、选品分析、广告投放、支付处理、库存管理、推荐引擎、营销活动、供应链预测、用户行为分析），通过 Supervisor-Expert 协作模式实现智能任务路由与并行处理，并通过 DeepSeek LLM 驱动自然语言交互。

#### 技术栈

| 层级 | 技术 |
|------|------|
| 多智能体框架 | LangGraph（StateGraph 编译、状态持久化、断点恢复、流式执行） |
| LLM 集成 | DeepSeek API、OpenAI 兼容接口、Ollama 本地部署 |
| 通信协议 | MCP 协议（自研 Server/Client/Router 三层架构） |
| 后端框架 | FastAPI（RESTful API、异步处理、Swagger 文档） |
| 数据库 | SQLite（开发）+ PostgreSQL（生产）、SQLAlchemy ORM（14张核心业务表） |
| 前端 | React 18 + TypeScript + Tailwind CSS + Zustand |
| 容器化 | Docker 多阶段构建、Docker Compose 三服务编排 |
| CI/CD | GitHub Actions（lint → test → demo → build → deploy 五阶段流水线） |
| 监控 | 自研 HealthMonitor（API 响应时间 P50/P95/P99、LLM 调用延迟、工具成功率） |

#### 核心架构设计

**1. Supervisor-Expert 多智能体协作模式**

- 设计并实现了 Supervisor 主控 Agent，负责意图识别、任务分解、路由决策和多 Agent 编排
- 定义了 8 种多 Agent 协作模式（新品上市、下单流程、营销推荐、售后处理等），实现 Agent 间的有序编排
- 通过 LLM 智能路由 + 关键词快速匹配 + 多 Agent 模式匹配的三级路由策略，确保路由准确率
- 使用 ReAct（Reasoning + Acting）模式，每个 Agent 遵循 Thought → Action → Observation → Final Answer 的完整推理链

**2. MCP 协议自研实现**

- 从零设计并实现了 MCP 协议的三层架构：MCPServer（工具注册与调用）、MCPClient（服务发现与并行调用）、MCPRouter（统一路由与调用链追踪）
- 每个 Expert Agent 作为独立 MCP Server，注册领域工具，Supervisor 通过 MCP Client 进行工具发现和调用
- 支持同步/异步 handler 兼容、工具 Schema 自动生成（JSON Schema 格式）、调用历史记录

**3. MCP 外部工具适配器架构**

- 设计了适配器模式，实现了数据库适配器（SQL 查询 → 参数绑定防注入 → 结果展开）和外部 API 适配器（物流追踪、汇率查询、快递预估）
- 实现了 AdapterRegistry 统一注册中心，支持工具名 → 适配器的动态映射和延迟求值
- 自研 PermissionGuard（API Key + 工具白名单双重验证）和 RetryConfig（指数退避 + jitter 防惊群）
- 共对接 10 个外部工具，支持 3 个外部 API 模拟器

**4. LangGraph 状态管理与图编排**

- 设计了 MainGraphState 与 ExpertSubgraphStates 之间的状态映射函数，实现跨子图的数据流转
- 使用 Annotated + reducer 实现 expert_outputs 的累积合并，避免状态覆盖
- 实现了 MemorySaver 状态持久化（8 个 checkpoint），支持 interrupt_before 断点恢复和 stream 流式执行
- 通过条件边实现 Supervisor → Expert → Aggregate 的动态路由

**5. 前端交互界面**

- 独立开发了深色科技风（Dark Tech）单页应用，Orbitron + JetBrains Mono 字体方案
- 实现三栏布局：Agent 导航侧边栏 + 对话交互区 + 历史记录面板
- 内置 API 端点测试面板，支持一键测试 + JSON 响应展示 + 复制功能
- 历史记录通过 localStorage 持久化，支持搜索过滤和回看
- 响应式设计：桌面端三栏、平板端双栏、移动端单栏

#### 主要成果

- 11 个专业 Agent 全部完成 MCP 工具注册，共计 38 个工具
- 14 张数据库核心业务表，含完整 SQLAlchemy ORM 模型
- 4 个 LangGraph Demo 全部通过（基础编译、状态持久化、断点恢复、流式执行）
- 6 个 MCP 工具调用 Demo 全部通过（完整链路、权限控制、重试机制、外部 API、多工具协作、调用链追踪）
- API 服务响应时间 < 200ms，健康检查通过
- Docker 多阶段构建镜像体积优化，CI/CD 五阶段流水线完整

---

## 专业技能

| 类别 | 技能 |
|------|------|
| 编程语言 | Python（精通）、TypeScript（熟练）、SQL |
| AI/LLM | LangChain、LangGraph、DeepSeek API、Ollama、ReAct Agent、Function Calling |
| 后端框架 | FastAPI、SQLAlchemy、Uvicorn |
| 协议与架构 | MCP 协议、RESTful API、多智能体协作模式、适配器模式 |
| 前端技术 | React 18、Tailwind CSS、Zustand、Vite |
| 数据库 | SQLite、PostgreSQL、SQL 设计与优化 |
| DevOps | Docker、Docker Compose、GitHub Actions、CI/CD |
| 工具链 | Git、VS Code、PowerShell |

---

## 自我评价

- 具备从 0 到 1 独立设计并交付复杂系统的能力，能完成从架构设计到编码实现到部署运维的全流程
- 对 AI Agent 和多智能体协作有深入理解，能熟练运用 LangGraph 进行复杂工作流编排
- 注重代码质量和工程规范，善于通过 Demo 和测试验证系统正确性
- 具备良好的技术文档编写能力，能清晰表达技术方案和架构设计