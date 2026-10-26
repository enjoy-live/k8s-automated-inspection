# 维护周报模板结构与只读命令

模板文件：`/home/storage/k8s-weekly-inspection/template/维护周报.pdf`

PDF 设计语言（强制，改样式只改 YAML）：`/home/storage/k8s-weekly-inspection/template/design-language.yaml`

时区一律使用 Asia/Shanghai。周期之外的事件可以用来对比，但必须标明不属于本周期。

## 章节（顺序不得改）

```markdown
# 维护周报-YYYYMMDD

## Kubeflow AI 平台运行周报

- **报告周期：** YYYY 年 MM 月 DD 日 - YYYY 年 MM 月 DD 日
- **运维负责人：** unix

> **本周重点：** 用两三句写本周期最重要的事实。没有突出事项就写“本周期无计划外故障”。

## 1. 集群健康度概览 (Cluster Health Summary)

本模块用于给领导层快速浏览，展示系统整体稳定性。

- 集群可用率 (SLA)：
- 节点状态：
- 核心组件状态：
  - Kubernetes 控制平面：
  - Kubeflow Dashboard：
  - Istio 网关：
  - 监控系统 (Prometheus/Grafana)：
  - 存储供给 (local-path-provisioner)：
  - 镜像仓库 (Harbor 代理缓存)：
  - GPU 驱动：

## 2. 资源消耗统计 (Resource Utilization)

展示硬件利用率，帮助客户判断是否需要扩容。

| 资源类型 | 峰值利用率 | 高峰期平均利用率 | 高峰期剩余可用量 |
|---|---:|---:|---:|
| CPU |  |  |  |
| 内存 |  |  |  |
| GPU (NVIDIA) |  |  |  |
| 存储 (PVC) |  |  |  |

节点详情：

| 节点 | 角色 | CPU | GPU | 当前 Pod 数 | 
|---|---|---:|---|---:|

## 3. AI 业务运行数据 (AI Workflow Stats)

体现 Kubeflow 平台的实际产出。

- Notebook 运行数：
- Pipeline 运行数：
- KServe 模型推理：

## 4. 故障处理与告警记录 (Incidents & Alerts)

展示你的专业性，以及你解决了哪些隐患。

问题分级写在条目前：严重、警告、提示。每条包含现象、证据、影响和建议。

## 5. 数据备份与安全巡检 (Backup & Security)

让客户对数据资产放心。

- Velero 集群备份：
- MinIO 模型数据备份：
- K8s 证书检查：
- 镜像扫描：

## 6. 下周工作计划 (Next Week's Plan)

- 

---

- 报告生成时间：
- 数据来源：
```

内容对应关系：

| 任务要求 | 写入章节 |
|---|---|
| 巡检概况、巡检结论 | 标题下的「本周重点」和文末数据来源 |
| 集群运行状态 | 第 1 节 |
| 资源使用情况 | 第 2 节 |
| AI 业务 | 第 3 节 |
| 异常与告警、故障及变更、风险分析 | 第 4 节 |
| 备份、证书、镜像安全 | 第 5 节 |
| 处理建议和后续计划 | 第 4 节各条建议，以及第 6 节 |

拿不到的指标写“本周期未采集到”，并说明缺什么权限或接口。不要用模板里的旧百分比、旧事件或旧备份名称填空。

## 只读命令

先建证据目录，再把输出重定向进去。下面的 `START` / `END` 换成周期起止的 RFC3339（+08:00）。

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl config current-context > "$EVID/context.txt"
kubectl get nodes -o wide > "$EVID/nodes.txt"
kubectl top nodes > "$EVID/top-nodes.txt"
kubectl get pods -A -o wide > "$EVID/pods.txt"
kubectl get deploy,sts,ds -A > "$EVID/workloads.txt"
kubectl get events -A --field-selector type=Warning > "$EVID/warning-events.txt"
kubectl get pvc,pv -A > "$EVID/storage.txt"
kubectl get svc,ingress -A > "$EVID/network.txt"
kubectl get notebooks.kubeflow.org -A > "$EVID/notebooks.txt"
kubectl get inferenceservices.serving.kserve.io -A > "$EVID/kserve.txt"
kubectl get workflows.argoproj.io -A > "$EVID/workflows.txt"
kubectl get backups.velero.io -A > "$EVID/velero.txt"
```

资源明细用 json，在本地按周期过滤，不要把 Token、Secret data 写进证据文件：

```bash
kubectl get nodes -o json > "$EVID/nodes.json"
kubectl get pods -A -o json > "$EVID/pods.json"
kubectl get events -A -o json > "$EVID/events.json"
kubectl get backups.velero.io -A -o json > "$EVID/velero.json"
```

Prometheus 只读查询沿用现有 Service，不修改监控对象：

```bash
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 19093:9090
```

查询结束后结束这个本地 `port-forward` 进程。查询失败就在周报第 2 节写明缺失，保留 `kubectl top nodes` 的即时值，并注明它不是周期峰值。

证书、GPU、节点日志只有在不创建工作负载的前提下读取。命令失败时记录退出码和缺失影响，不要改用会新建 Pod 的方式补数据。

## 交付检查

- 六个章节标题和两张表的列名与模板一致
- 周期、生成时间、数据来源都在
- 严重 / 警告 / 提示只用于实际发现的问题
- Markdown 和 PDF 都在 `output/` 下，文件名日期是周期结束日
- 证据目录里能找到对应命令输出
