# Agent数据验收标准
## 一、数据基本要求
1. 每条session数据，有效交互轮次≥2轮
2. 首条消息role正常，不得为 assistant/tool
3. 每条session中，至少一次结构化工具调用
4. 所有调用的工具都有明确定义，schema完整
5. 去掉最后一轮后，tool result 和tool call 配对率=100%
6. 机器轮占比< 25%，即(cron+heartbeat+no_reply user 轮) / user 轮 < 25%

## 二、模型要求
1. 支持模型：GPT、GEMINI、CLAUDE
2. 型号门槛：GPT-5 以上、GEMINI-3 以上、CLAUDE-4.5 以上版本

## 三、数据内容要求
### 3.1 数据源优先级
优先接受**真实用户**与Agent系统交互产生的轨迹数据；拒绝roleplay、GUI类场景数据，优先收录代码工程、搜索类高优场景交互轨迹。

### 3.2 合成数据识别特征（含此类内容不予收录）
#### 内容维度
1. 用户提问高度模板化、批量生成（如千篇一律“帮我开发完整XXX系统+功能清单”）
2. 对话无现场感，缺少追问、需求修正、上下文承接
3. 消息格式高度规整、行文风格统一刻板

#### 行为维度
1. 工具调用100%成功，无报错、无权限/路径异常、无重试逻辑
2. 文件路径、URL全部为通用占位符（/home/user/project/file.py、example.com）
3. 单轮消息完全自闭环，不引用前文、无指代省略
4. 任务单向线性推进，无中途改需求、新增问题、任务偏移

## 四、概念与轮次定义
### 4.1 有效轮次（effective turns）
| 交互类型 | 说明 |
| ---- | ---- |
| User ➜ Assistant | 用户提问，Agent直接回复 |
| Assistant ➜ Tool ➜ Tool Result | Agent发起工具调用并接收返回结果 |
| 用户追问与修正 | 用户补充信息、修改需求、针对回复提问 |

### 4.2 机器轮定义
1. heartbeat轮：用户命中固定模板，Agent返回无实质推理的哨兵字符串，无工具调用
2. cron轮：用户命中模板，Agent无工具调用、无推理内容
3. no_reply user轮：
   - 用户侧：空内容、纯标点、重复上一条消息、机械确认，无有效新信息
   - Agent侧：仅返回哨兵/空内容，无工具调用、无推理

### 4.3 Session会话定义
1. 定义：用户围绕单一完整任务与Agent的连续交互，从发起任务至完成/终止
2. 约束规则：
   - 首条消息role不能为assistant、tool
   - 每条会话分配唯一session_id
   - 完整会话必备：System Prompt（角色/能力设定）+ 至少2轮User↔Assistant交互
   - 若A会话是B会话的连续截取片段，仅保留完整版本B
3. 机器轮占比计算规则：
   机器轮 = heartbeat轮 + cron轮 + no_reply user轮
   user轮 = 全部role=user消息，剔除tool_result载体轮、元注入harness轮
   判定标准：机器轮 ÷ user轮 ＜ 25%

## 五、Tool Use工具调用规范
### 5.1 完整组成三要素
#### 1）工具定义 Tool Schema
每个工具必须完整配置：
- name：语义清晰工具名，禁止tool1、helper、action等模糊命名
- description：工具功能说明
- parameters：参数清单（参数名、数据类型、字段说明）

#### 2）结构化工具调用 Tool Call
采用标准tool_use/function_call结构化格式，包含：
- 目标工具名称
- JSON结构化调用参数
*纯自然语言文字描述调用工具，不计入有效工具调用*

#### 3）工具返回结果 Tool Result
每次调用配套对应返回数据：
- 工具执行输出内容
- 执行状态标识（成功/失败/错误详情）

### 5.2 数量与配对要求
1. 单Session最低标准：至少1次合法结构化工具调用
2. 工具合法性：所有被调用工具必须在前置工具列表内定义，禁止调用未声明工具
3. 配对率规则：剔除最后一轮数据后，tool_result与tool_call配对率=100%
   配对率计算公式：匹配到结果的调用数 ÷ 总工具调用数
   尾轮判定：以最后一条other类型消息为准

## 六、标准字段清单
| 分类 | 字段名 | 说明 |
| ---- | ---- | ---- |
| 会话基础 | session_id | 会话唯一标识 |
| 对话轨迹 | messages / conversation / trajectory | 完整交互消息序列 |
| 模型信息 | model / model_name | 模型名称+版本 |
| 消息基础 | role | 角色枚举：system / user / assistant / tool |
|  | content | 消息文本/结构化内容 |
| 系统设定 | System Prompt | Agent角色、能力、行为约束 |
| 工具基础 | Tool definitions / Tool schema | 全量可用工具及参数定义 |
| 调用记录 | tool_call / tool_use / function_call | 工具调用行为（工具名+参数） |
| 返回数据 | tool_result / observation | 工具执行输出结果 |
| 推理过程 | thinking / reasoning | Agent内部思考推理文本 |
| 元数据 | metadata | 时间戳、token消耗、服务商等附加信息 |
| 业务标签 | task_type / domain | 任务类型、所属业务领域 |

## 七、数据集去重标准
1. **精确重复去重**
对比维度：system prompt + 用户全量消息 + Agent回复 + 工具调用 + 工具返回，序列完全一致判定为重复，仅保留一份。
2. **子集片段去重**
若一条会话是另一条完整会话的连续截取片段，仅保留完整版本。

## 八、Token结算计算规则（合作方结算专用）
1. 前置处理：数据集先执行精确去重+子集去重；
2. 有效Token总和 = 全部消息Token + 所有工具定义（tool call definition）Token；
3. Base64图片编码部分直接剔除，不计入Token统计，其余文本正常计算。

## 九、交付文件格式规范
1. 文件格式：JSON / JSONL；编码统一UTF-8；单条JSON必须可正常解析；
2. 压缩包：统一打包为tar.gz；
3. 目录规范：路径层级标准化，复杂目录需配套路径说明文档。

### 标准工具调用示例
```json
{
  "role": "assistant",
  "content": "让我搜索一下相关信息。",
  "tool_calls": [
    {
      "id": "call_001",
      "type": "function",
      "function": {
        "name": "web_search",
        "arguments": "{\"query\": \"Python async best practices\"}"
      }
    }
  ]
}
```

### 标准工具返回示例
```json
{
  "role": "tool",
  "tool_call_id": "call_001",
  "content": "搜索结果:..."
}
```

## 十、严禁行为（数据拒收红线）
1. 伪造工具结果：编造虚假ID、统计数字、无依据工具输出；
2. 内容自相矛盾：Agent声称操作完成，但工具返回执行失败；
3. 模型信息造假：model字段标注型号与实际生成模型不符；
4. 工具幻觉：调用不存在的虚构工具、工具返回内容无依据纯幻觉。


