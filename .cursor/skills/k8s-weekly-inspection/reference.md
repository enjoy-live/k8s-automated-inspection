# 周报写法与口径

S15 写 Markdown 时读本文件。采集命令只在 SKILL.md 的执行步骤里。本文件的序号是周报条目或核对项，不是技能步骤。

颜色、字号、字体和波浪线只来自 `template/design-language.yaml`。否定句判定用该文件的 `wave_negations` 和 `alert_negations`。不要在 Markdown 里写 `<font>`、HTML 或色值。

## 写作契约

- **本周重点**写成引用块中的有序列表，一条事实一行，通常 2 到 4 条。没有计划外故障时只写一条：`本周期无计划外故障`。

```markdown
> **本周重点：**
> 1. 第一条最重要的事实
> 2. 第二条事实
```

- **并列项**用 `1. 2. 3.`：名单、证据、建议、缺失项、组件状态子项。字段定义仍用 `- **字段：**`，不要改成序号。
- **严重**小节标题含 `【严重】`。核心行只以 `现象：`、`结论：`、`影响：` 开头。没有判定就删掉「结论」行。证据和操作步骤保持正文色，除非该行同时触发异常或复发。
- **警告**的级别格只写 `警告`，不写 `warning`。列表写成 `1. 【警告】...`。`提示` 不上色，也不画波浪线。
- **异常、复发**：去掉 `alert_negations` 后行内仍有这两个词才标红。同一行既有否定又有肯定时标红，例如「上期无复发，本期复发」。
- 严重是已经造成中断、数据风险，或硬件故障仍未根除。警告是持续告警、临近阈值、多期未执行，但本周期没有新的中断。两个标记不要互换。
- **第 7 节始终保留。** 有动作、对象、完成标准时用表，列是「序号、计划事项、对象、完成标准」；没有则只写 `1. 暂无安排`。
- **上期落实**有可执行事项时用表；没有则写一句话，不要造空表。

## 章节（顺序不得改）

固定导语随对应章节原样保留。骨架表里的「告警名」「问题」「动作」「对象」「时间段」「事件」「原因」「后果」「建议」是示例，正式周报不要原样留下这些词。

```markdown
# 维护周报-YYYYMMDD

## Kubeflow AI 平台运行周报

- **报告周期：** YYYY 年 MM 月 DD 日 - YYYY 年 MM 月 DD 日
- **运维负责人：** unix

> **本周重点：**
> 1. 本周期最重要的事实

## 1. 集群健康度概览 (Cluster Health Summary)

本模块用于给领导层快速浏览，展示系统整体稳定性。

- 集群可用率 (SLA)：
- 节点状态：
- 核心组件状态：
  1. Kubernetes 控制平面：
  2. Kubeflow Dashboard：
  3. Istio 网关：
  4. 监控系统 (Prometheus/Grafana)：
  5. 存储供给 (local-path-provisioner)：
  6. 镜像仓库 (Harbor 代理缓存)：
  7. GPU 驱动：

## 2. 资源消耗统计 (Resource Utilization)

展示硬件利用率，帮助客户判断是否需要扩容。

| 资源类型 | 峰值利用率 | 周期平均利用率 | 峰值时剩余可用量 |
|---|---:|---:|---:|
| CPU |  |  |  |
| 内存 |  |  |  |
| GPU (NVIDIA) |  |  |  |
| 存储 (PV) |  |  |  |

节点详情：

| 节点 | 角色 | CPU | 内存使用 | GPU | 当前 Pod 数 | 根分区 |
|---|---|---:|---:|---|---:|---:|

GPU 实际带载情况：

| 节点 | GPU | 显存占用 | 温度 | 功耗 | 带载业务 |
|---|---|---:|---:|---:|---|

PV 状态：

| PV 状态 | 数量 | 容量 | 较上期 |
|---|---:|---:|---|

## 3. AI 业务运行数据 (AI Workflow Stats)

体现 Kubeflow 平台的实际产出。

- Notebook 运行数：
  1. 每个活跃 Notebook 一条，写命名空间/名称和节点
- Pipeline 运行数：
  1. 成功、失败、运行中的条数
- KServe 模型推理：
  1. 每个在线模型一条

有新增 PVC 时加表，没有就写「本周期无新增业务数据卷」：

| PVC 名称 | 命名空间 | 创建时间 | 用途 |
|---|---|---|---|

## 4. 故障处理与告警记录 (Incidents & Alerts)

小节顺序固定：具体故障（严重在前，警告在后）、告警汇总、遗留问题跟踪、镜像源治理复核。某一类没有内容就写一句「本周期无」，不删标题。上述四类之外的事项不要另开小节。

### 4.1 【严重】用一句话写出故障

**现象：** 发生了什么、何时、影响多久。

**结论：** 有判定才写。没有判定就删掉这一行。

**影响：** 对平台或业务的后果。

**证据：**

1. 写清命令或指标名称

核查项用表，不改成散文：

| 核查项 | 核查方法 | 结果 |
|---|---|---|

**建议：**

1. 动作、对象、完成标准

### 4.x 【警告】用一句话写出问题

1. 【警告】写明对象、时间和后果

### 4.x 告警汇总

只收有实际风险的告警。Watchdog、InfoInhibitor 不列入。内存超卖告警在同期 MemAvailable 没有接近 kubelet 的 `memory.available` 硬阈值时不列入，并在表前写明排除原因。

| 告警名称 | 级别 | 对象 | 时段 (CST) | 关联事件 | 原因 | 后果 |
|---|---|---|---|---|---|---|
| 告警名 | 警告 | 对象 | 时间段 | 事件 | 原因（数据超出，单元格要换行显示） | 后果（数据超出，单元格要换行显示） |

### 4.x 遗留问题跟踪

| 分级 | 问题 | 持续时长 | 较上期变化 | 建议 |
|---|---|---|---|---|
| 警告 | 问题 |  |  | 建议 |
| 提示 | 问题 |  |  | 建议 |

分级只写 `严重`、`警告` 或 `提示`。

### 4.x 镜像源治理复核

1. helper 镜像、Kyverno、Harbor 代理、本周期是否还有外网镜像拉取失败等等

## 5. 数据备份与安全巡检 (Backup & Security)

让客户对数据资产放心。

- Velero 集群备份：
- MinIO 模型数据备份：
- K8s 证书检查：
- 镜像扫描：

| 备份计划 | 周期 (UTC) | 保留策略 | 本周期执行 |
|---|---|---|---:|

证书写剩余天数。磁盘写本周期使用率。只有某个节点达到 configz 阈值时，用一句话写该档后果；没达到就不写阈值说明。

## 6. 上期落实

| 上期计划事项 | 状态 | 核查依据 |
|---|---|---|
| 上期原文，可压缩 | ✅ 已完成 | 本周期证据 |

状态只允许 `✅ 已完成`、`⚠️ 部分`、`❌ 未执行`、`— 不适用`。不适用要写原因。

## 7. 下周计划 (Next Week's Plan)

| 序号 | 计划事项 | 对象 | 完成标准 |
|---|---|---|---|
| 1 | 动作 | 对象 | 怎样算做完 |

没有可执行事项时，这一节只保留：`1. 暂无安排`

---

- 报告生成时间：
- 数据来源：
- 证据目录：
- 缺失项：
    1. 缺什么、影响哪一节
```

## 口径

这一节只告诉 Agent 怎么算、怎么填。不要把本节的 PromQL、步长、configz 字段、`kubectl top` 原理或「为什么不用瞬时值」写进周报。

| 资源汇总列 | 怎么填 |
|---|---|
| 峰值利用率 | 周期内 Prometheus 最大值 |
| 周期平均利用率 | 周期内平均值。列名写「周期平均」，不写「高峰期平均」 |
| 峰值时剩余可用量 | 峰值时刻剩余量。存储行写 Bound 容量，并注明 Released 待回收量 |

| 节点详情列 | 怎么填 |
|---|---|
| CPU | 节点容量，如 `56c`。不填利用率 |
| 内存使用 | 周期内 `100 * (1 - MemAvailable / MemTotal)` 的最大值，如 `36.5%` |
| GPU | 型号、数量和显存。不填利用率 |
| 当前 Pod 数 | 巡检时刻该节点 Running Pod 数 |
| 根分区 | 根文件系统使用率的周期最大值，如 `75.0%` |

内存使用和根分区保留 1 位小数，取周期内最大值。没采到填 `未采集`，不留空，不编百分比。

`kubectl top nodes` 不能填「内存使用」。它只留在 `top-nodes.txt`，不写入周报。

`node_uname_info.nodename` 与 kubectl 节点名可能只差大小写。对照时忽略大小写；对不上就用 instance 和节点 InternalIP。对照过程写入证据，不写入周报。

内存 PromQL：

```promql
100 * (
  1 - (
    max by (nodename) (
      node_memory_MemAvailable_bytes
      * on(instance) group_left(nodename) node_uname_info
    )
    /
    max by (nodename) (
      node_memory_MemTotal_bytes
      * on(instance) group_left(nodename) node_uname_info
    )
  )
)
```

根分区 PromQL。原始结果写入 `rootfs.json`，周期最大、最小和峰值时间写入 `node-usage-period.json`。

```promql
100 * (
  1 - (
    max by (nodename) (
      node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay|squashfs|ramfs"}
      * on(instance) group_left(nodename) node_uname_info
    )
    /
    max by (nodename) (
      node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay|squashfs|ramfs"}
      * on(instance) group_left(nodename) node_uname_info
    )
  )
)
```

资源汇总另做这些 `query_range`，步长 5 分钟，窗口与节点查询相同。原始 JSON 按文件名保存：

| 文件 | PromQL |
|---|---|
| `cpu.json` | `100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])))` |
| `mem-cluster.json` | `100 * (1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))` |
| `gpu-util.json` | `DCGM_FI_DEV_GPU_UTIL` |
| `storage.json` | `100 * sum(kubelet_volume_stats_used_bytes) / sum(kubelet_volume_stats_capacity_bytes)` |
| `alerts.json` | `ALERTS{alertstate="firing"}` |

Watchdog、InfoInhibitor 不写入告警汇总。内存超卖告警只有在同期 MemAvailable 接近 configz 里 `memory.available` 硬阈值时才列入。

磁盘阈值用每个节点的只读 configz，不要抄上一份周报的百分数：

```bash
kubectl get --raw "/api/v1/nodes/<节点名>/proxy/configz"
```

用 configz 判断是否越线：`imageGCHighThresholdPercent`、`imageGCLowThresholdPercent`，以及 `evictionHard` 的 `imagefs.available`、`nodefs.available`、`nodefs.inodesFree`。`node.fs` 与 `runtime.imageFs` 的容量和可用空间一致时，镜像盘就是根分区。没有越线的节点，周报不写这些字段和后果。`/home/data` 与 imageFs 不是同一块盘时，不要套用根分区阈值。configz 读不到就在证据里写 `未采集`，周报该格写 `未采集`，不补百分数。

GPU 带载表和 PV 状态表有数据才建表。没采到就保留小标题，下面写「本周期未采集到」和原因，不留空表，不删标题。

PVC「用途」证明不了就写「未证实」。

## 上期落实与下周计划

上期落实：

- 在 `/home/storage/k8s-weekly-inspection/output/` 找 `维护周报-YYYYMMDD.md` 中结束日早于本期的最新一份。
- 新格式读取「## 7. 下周计划」到下一条 `## ` 或文末 `---`。
- 旧格式没有第 7 节时，读取「## 6. 下周工作计划」。旧版第 6 节是下周计划，不是上期落实。
- 表中每一行是一条计划，忽略表头。
- 忽略「暂无安排」和空条目。
- 找不到上一份周报：第 6 节写「无上一份周报，本期不核查上期计划」，不建表。
- 上期只有「暂无安排」：写「上期无待落实计划」，不建表。
- 其余每一条都进落实表。状态按本周期证据填写，不沿用上期的形容词。

下周计划：

- 只收两类：本期严重或警告建议里，下一周能安排的动作；上期未执行或部分完成、且仍然有效的事项。
- 每条都要有动作、对象、完成标准。
- 「继续观察」不写成计划，观察结论留在第 4 节。
- 一条都没有时，第 7 节只写 `1. 暂无安排`。
- 有事项时用「章节」里的四列表，不写成有序列表。

## 内容对应关系

| 素材 | 写入 |
|---|---|
| 巡检概况、巡检结论 | 「本周重点」和文末数据来源 |
| 集群运行状态 | 第 1 节 |
| 资源使用情况、根分区 | 第 2 节 |
| AI 业务 | 第 3 节 |
| 异常与告警、故障及变更、风险分析、处理建议 | 第 4 节 |
| 备份、证书、镜像安全 | 第 5 节 |
| 上期落实 | 第 6 节 |
| 下周计划 | 第 7 节 |

拿不到的指标写「本周期未采集到」或 `未采集`，并说明缺什么权限或接口。

第 4、5 节用这些证据，不另找数据源：

- 告警汇总：`alerts.json`，时段和关联事件再对照 `events.json`。
- 镜像源治理：`kyverno.txt`、`image-pull.txt`、`harbor-health.json`。
- Velero 集群备份和备份计划：`velero.json`、`velero-schedules.json`。名称含 `minio` 的 Schedule 和 Backup 写入「MinIO 模型数据备份」，不登录 MinIO。
- 证书：`certificates.json` 与 `apiserver-cert.txt`。
- 镜像扫描：`harbor-health.json` 里的 trivy 状态。不触发新的漏洞扫描。

## 交付检查

- 7 个章节标题都在，顺序与「章节」一致，固定导语仍在。
- 本周重点每条都以 `> ` 开头。
- 文末有报告生成时间、数据来源、证据目录、缺失项。缺失项写明缺什么、影响哪一节。
- 上期落实只居其一：无上一份周报、上期无待办、或落实表覆盖每一条。
- 第 7 节是计划表，或只有 `1. 暂无安排`。
- 告警汇总表有时段、关联事件、原因和后果。单元格内容过长时换行，不截断。
- 第 5 节四项都有结论，或该项写明 `未采集` 和原因。备份计划表的周期来自 Schedule，不凭备份名称猜测 cron。
- 正式正文不保留骨架示例词「告警名」「时间段」「事件」「动作」。
- 节点详情的内存使用和根分区是一位小数的周期峰值，或 `未采集`。
- 正文没有 PromQL、`query_range`、configz 字段说明，也没有 `kubectl top` 的原理或「为什么不用瞬时值」。
- Markdown 里没有 HTML 颜色。
