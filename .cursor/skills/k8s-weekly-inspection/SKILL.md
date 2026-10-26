---
name: k8s-weekly-inspection
description: >-
  对内网 Kubernetes 集群做只读巡检，并严格按照维护周报模板生成周报 Markdown 与 PDF。
  在用户要求巡检、维护周报、巡检周报、Kubeflow 周报，或定时任务调用本技能时使用。
---

# Kubernetes 维护周报巡检

先读取 [reference.md](reference.md)。模板里的历史数字只说明排版和口径，不得抄进新报告。

## 调用参数

周期由调用方传入。未传入时不要自行改成“本周大概”，先向用户要开始日和结束日。

- 开始：`PERIOD_START`，当天 `00:00`（Asia/Shanghai）
- 结束：`PERIOD_END`，当天 `23:59`（Asia/Shanghai）
- 模板：`/home/storage/k8s-weekly-inspection/template/维护周报.pdf`
- PDF 设计语言（强制）：`/home/storage/k8s-weekly-inspection/template/design-language.yaml`
- 正文：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md`
- PDF：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf`
- 命令证据：`/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD/`

`YYYYMMDD` 用周期结束日。运维负责人沿用模板中的 `unix`，除非用户另行指定。

定时触发器会设置 `K8S_WEEKLY_UNATTENDED=1`，并在提示词里写明周期。此时触发脚本已经做过 `kubectl` 只读连通性检查：把巡检计划写进证据目录后直接开始，不要停下来等人工确认。

人工调用且未声明“直接开始”时：先列出巡检计划、连接方式（当前 kubeconfig 上下文）和预计只读命令；用户确认，或明确说直接开始之后，再执行巡检。

## 固定任务要求

请读取并参考以下维护周报模板：

`/home/storage/k8s-weekly-inspection/template/维护周报.pdf`

任务目标：
对内网环境中的 Kubernetes 集群执行巡检，巡检统计周期为调用参数给出的开始日 00:00 至结束日 23:59（Asia/Shanghai）。

执行要求：
1. 先分析模板的章节结构、表格字段、指标口径和写作风格。
2. 通过现有的内网访问方式连接目标 Kubernetes 集群。
3. 巡检过程以只读操作为主，不得修改、重启或删除任何集群资源。
4. 巡检范围至少包括：
   - 集群节点状态及资源使用率
   - Pod、Deployment、StatefulSet、DaemonSet 运行状态
   - 异常重启、Pending、Failed、Evicted、OOMKilled 等情况
   - CPU、内存、磁盘及文件系统使用情况
   - Kubernetes Events 和关键错误日志
   - 命名空间及核心业务服务健康状态
   - PVC/PV、存储容量及异常状态
   - 网络、Ingress、Service 和证书有效期
   - 巡检周期内的告警、故障、变更及处理情况
5. 所有结论必须基于实际命令输出或监控数据，不得猜测或补造数据。
6. 如果缺少访问权限、历史监控数据或必要信息，应明确列出缺失项及影响，不要用虚构内容填充。
7. 对发现的问题按照“严重、警告、提示”分级，并提供处理建议。
8. 保留关键巡检命令和数据来源，确保结果可以复核。

输出要求：
1. 严格参照模板生成维护周报。章节顺序、表格列和写作口吻以模板为准；下面的内容清单写进对应章节，不要另起一套标题。
2. 报告中包含：
   - 巡检概况
   - 集群运行状态
   - 资源使用情况
   - 异常与告警汇总
   - 故障及变更记录
   - 风险分析
   - 处理建议和后续计划
   - 巡检结论
3. 对敏感信息进行脱敏，不得写入密码、Token、私钥或完整凭据。
4. 最终生成可交付的维护周报文件，并说明文件保存路径。
5. 人工调用时，在执行前先列出巡检计划、需要的连接信息和预计使用的只读命令；确认具备访问条件后再开始巡检。定时无人值守调用见上文。

## 执行顺序

1. 用 `pdftotext -layout` 阅读模板，对照 [reference.md](reference.md) 的章节。
2. 确认 `kubectl config current-context` 可用。只使用只读命令。禁止 `apply`、`delete`、`patch`、`scale`、`rollout restart`、`cordon`、`drain`、`debug`，以及任何会创建 Pod 或修改资源的命令。本机 `kubectl port-forward` 只用于读取 Prometheus，用完结束该本地进程。
3. 把关键命令的原始输出保存到证据目录。周报正文不粘贴完整日志，只引用能复核的结论。
4. 先写 Markdown，再用渲染脚本生成 PDF。脚本必须读取 `template/design-language.yaml`，禁止在脚本里临时改色/改字号/去掉 emoji 回退：

```bash
python3 /home/storage/k8s-weekly-inspection/scripts/render_weekly_report.py \
  /home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md \
  /home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf
```

Markdown 状态符约定（与设计语言一致）：正常用 `✅`，警告用 `⚠️`，失败用 `❌`；渲染后分别为绿色 `[OK]`、琥珀色 `[!]`、红色 `[X]`。

5. 结束后说明 Markdown 与 PDF 的保存路径、周期、数据来源，以及缺失项。
