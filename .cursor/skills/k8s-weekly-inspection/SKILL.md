---
name: k8s-weekly-inspection
description: >-
  对内网 Kubernetes 集群做只读巡检，并严格按照维护周报模板生成周报 Markdown 与 PDF。
  在用户要求周报巡检、进行巡检、巡检、维护周报、巡检周报、Kubeflow 周报，或定时任务调用本技能时使用。
---

# Kubernetes 维护周报巡检

只执行「执行步骤」。按 S 编号顺序做，不得重排、跳步，也不得把「约束」「输出」「参考」或 [reference.md](reference.md) 里的编号当成步骤。每步做完，在回复里勾掉对应项，再进入下一步。

对内网 Kubernetes 集群做只读巡检。统计周期为 `PERIOD_START` 当天 00:00 至 `PERIOD_END` 当天 23:59（Asia/Shanghai）。模板里的历史数字只说明排版和口径，不得抄进新报告。

## 输入

| 名称 | 必填 | 未提供时 |
| --- | --- | --- |
| `PERIOD_START` | 是 | 停在 S2，向用户索取开始日，不得猜成「本周」 |
| `PERIOD_END` | 是 | 停在 S2，向用户索取结束日，不得猜成「本周」 |
| 用户确认或「直接开始」 | 人工调用时必填 | 停在 S3 |
| `K8S_WEEKLY_UNATTENDED` | 否 | 未设为 `1` 时按人工调用处理 |

固定路径：

- 模板：`/home/storage/k8s-weekly-inspection/template/维护周报.pdf`
- PDF 设计语言：`/home/storage/k8s-weekly-inspection/template/design-language.yaml`
- 正文：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md`
- PDF：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf`
- 证据目录：`/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD/`
- `YYYYMMDD` 用周期结束日。运维负责人沿用模板中的 `unix`，除非用户另行指定。
- 下文 `$EVID` 就是上面的证据目录。

## 执行步骤

- [ ] S1 读取 reference.md
- [ ] S2 核对周期
- [ ] S3 判断是否开工
- [ ] S4 分析模板
- [ ] S5 确认集群连接
- [ ] S6 巡检节点状态及资源使用率
- [ ] S7 巡检 Pod、Deployment、StatefulSet、DaemonSet
- [ ] S8 巡检异常重启、Pending、Failed、Evicted、OOMKilled
- [ ] S9 巡检 CPU、内存、磁盘及文件系统
- [ ] S10 巡检 Events 和关键错误日志
- [ ] S11 巡检命名空间及核心业务服务
- [ ] S12 巡检 PVC/PV 和存储容量
- [ ] S13 巡检网络、Ingress、Service 和证书有效期
- [ ] S14 巡检本周期告警、故障、变更及处理
- [ ] S15 写 Markdown
- [ ] S16 渲染 PDF
- [ ] S17 说明交付结果

### S1 — 读取 reference.md

- 动作：读完 [reference.md](reference.md)
- 命令：无
- 读取：`/home/storage/.cursor/skills/k8s-weekly-inspection/reference.md`
- 写入：无
- 完成：已读完「写作契约」「章节」「口径」「上期落实与下周计划」「内容对应关系」「交付检查」
- 失败：文件读不到则停在本步。不得进入 S2

### S2 — 核对周期

- 动作：确认 `PERIOD_START` 和 `PERIOD_END` 都是 `YYYY-MM-DD`，且开始日不晚于结束日
- 命令：无
- 读取：调用方给出的周期。定时任务写在提示词里
- 写入：无
- 完成：两个日期都已确定，时区按 Asia/Shanghai，开始日 00:00，结束日 23:59
- 失败：缺任一日期，或格式不对，或开始日晚于结束日，则停在本步并向用户索取。不得改成「本周大概」，不得进入 S3

### S3 — 判断是否开工

- 动作：按调用方式选择唯一分支
- 命令：`kubectl config current-context`
- 读取：环境变量 `K8S_WEEKLY_UNATTENDED`，以及用户是否已确认或已说「直接开始」
- `K8S_WEEKLY_UNATTENDED=1`：创建 `$EVID`，把周期、当前上下文、以及 S4 至 S16 的只读命令写入 `$EVID/plan.txt`，然后进入 S4
- 用户已确认，或已说「直接开始」：进入 S4
- 其余人工调用：在回复中列出巡检计划、当前 kubeconfig 上下文和 S4 至 S16 的只读命令，然后停在本步
- 完成：继续分支已进入 S4；停止分支已把计划发给用户且未进入 S4
- 失败：上下文命令失败时，把失败原因写入计划并停在本步。不得进入 S4

### S4 — 分析模板

- 动作：用模板正文核对章节、表格和措辞；样式只读取设计语言，不从 PDF 提取
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
pdftotext -layout /home/storage/k8s-weekly-inspection/template/维护周报.pdf - > "$EVID/template.txt"
cp /home/storage/k8s-weekly-inspection/template/design-language.yaml "$EVID/design-language.yaml"
```

- 读取：`$EVID/template.txt` 对照 reference.md「章节」。`$EVID/design-language.yaml` 是页面、字体、字号、颜色、表格和波浪线的唯一样式来源
- 写入：`$EVID/template.txt`、`$EVID/design-language.yaml`
- 完成：`template.txt` 已对照七节顺序、表格列和措辞。样式文件已复制到证据目录。不根据 `template.txt` 判断颜色、字号、加粗、底色或下划线
- 失败：任一命令失败则停在本步。不得进入 S5

### S5 — 确认集群连接

- 动作：通过现有 kubeconfig 确认只读连接可用
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl config current-context > "$EVID/context.txt" 2>&1
kubectl auth can-i get nodes > "$EVID/can-i-nodes.txt" 2>&1
```

- 读取：无
- 写入：`$EVID/context.txt`、`$EVID/can-i-nodes.txt`
- 完成：`context.txt` 是当前上下文，且 `can-i-nodes.txt` 为 `yes`
- 失败：任一命令失败，或权限不是 `yes`，则停在本步。不得进入 S6

### S6 — 巡检节点状态及资源使用率

- 动作：采集节点状态、资源使用率和 GPU 只读结果
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get nodes -o wide > "$EVID/nodes.txt" 2>&1
kubectl top nodes > "$EVID/top-nodes.txt" 2>&1
kubectl get nodes -o json > "$EVID/nodes.json" 2>&1
kubectl get pods -A -l app=nvidia-dcgm-exporter -o wide > "$EVID/gpu.txt" 2>&1
: > "$EVID/gpu-smi.txt"
kubectl get pods -A -l app=nvidia-dcgm-exporter --no-headers 2>>"$EVID/gpu-smi.txt" | while read -r ns name _; do
  {
    echo "--- ${ns}/${name} ---"
    kubectl exec -n "$ns" "$name" -- nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,temperature.gpu,power.draw,memory.used,utilization.gpu --format=csv,noheader
    echo "-- apps --"
    kubectl exec -n "$ns" "$name" -- nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv,noheader
  } >> "$EVID/gpu-smi.txt" 2>&1
done
if ! grep -q '[0-9]' "$EVID/gpu-smi.txt"; then
  echo '未采集：没有可用的已有 dcgm-exporter Pod，或 nvidia-smi 失败' >> "$EVID/gpu-smi.txt"
fi
```

- 读取：无
- 写入：`$EVID/nodes.txt`、`$EVID/top-nodes.txt`、`$EVID/nodes.json`、`$EVID/gpu.txt`、`$EVID/gpu-smi.txt`
- 完成：五个文件都存在。`kubectl top` 只作对照，不拿来填「内存使用」。GPU 带载只使用已有 dcgm-exporter Pod 的 `nvidia-smi`
- 失败：采集失败。把退出码和错误留在对应文件中，记入缺失项，然后进入 S7。禁止创建 Pod，禁止对其他 Pod 执行 `exec`

### S7 — 巡检工作负载

- 动作：采集 Pod、Deployment、StatefulSet、DaemonSet 运行状态
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get pods -A -o wide > "$EVID/pods.txt" 2>&1
kubectl get deploy,sts,ds -A > "$EVID/workloads.txt" 2>&1
kubectl get pods -A -o json > "$EVID/pods.json" 2>&1
```

- 读取：无
- 写入：`$EVID/pods.txt`、`$EVID/workloads.txt`、`$EVID/pods.json`
- 完成：三个文件都存在，且没有写入 Secret data
- 失败：采集失败。记录退出码和缺失影响，然后进入 S8

### S8 — 巡检异常 Pod

- 动作：从已采集的 Pod 数据中列出异常重启、Pending、Failed、Evicted、OOMKilled
- 命令：无集群命令。只本地筛选 `$EVID/pods.json`
- 读取：`$EVID/pods.json`
- 写入：`$EVID/pod-anomalies.txt`
- 完成：文件列出上述五类对象；一类都没有时写明「未发现」及对应类别
- 失败：`pods.json` 不可用时，写入 `未采集：` 和原因，然后进入 S9

### S9 — 巡检 CPU、内存、磁盘及文件系统

- 动作：用 Prometheus 采集资源汇总、节点内存、根分区和告警，并用 configz 采集磁盘阈值。查完结束本地 port-forward
- 命令：`PERIOD_START`、`PERIOD_END` 使用已核对的日期。PromQL 与 reference.md「口径」一致，不得改写

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
START=$(TZ=Asia/Shanghai date -d "$PERIOD_START 00:00:00" +%s)
END=$(TZ=Asia/Shanghai date -d "$PERIOD_END 23:59:59" +%s)
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 19093:9090 >"$EVID/port-forward.txt" 2>&1 &
PF=$!
cleanup() { kill "$PF" 2>/dev/null || true; wait "$PF" 2>/dev/null || true; }
trap cleanup EXIT
ready=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -sf http://127.0.0.1:19093/-/ready >/dev/null && ready=1 && break
  sleep 1
done
prom() {
  if [ "$ready" -ne 1 ]; then
    echo '未采集：Prometheus 未就绪' > "$EVID/$1"
    return
  fi
  curl -sS -G http://127.0.0.1:19093/api/v1/query_range \
    --data-urlencode "query=$2" \
    --data-urlencode "start=$START" \
    --data-urlencode "end=$END" \
    --data-urlencode "step=300" \
    -o "$EVID/$1" || echo "未采集：$1" > "$EVID/$1"
}
prom cpu.json '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])))'
prom mem-cluster.json '100 * (1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))'
prom mem-nodes.json '100 * (1 - (max by (nodename) (node_memory_MemAvailable_bytes * on(instance) group_left(nodename) node_uname_info) / max by (nodename) (node_memory_MemTotal_bytes * on(instance) group_left(nodename) node_uname_info)))'
prom rootfs.json '100 * (1 - (max by (nodename) (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay|squashfs|ramfs"} * on(instance) group_left(nodename) node_uname_info) / max by (nodename) (node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay|squashfs|ramfs"} * on(instance) group_left(nodename) node_uname_info)))'
prom gpu-util.json 'DCGM_FI_DEV_GPU_UTIL'
prom storage.json '100 * sum(kubelet_volume_stats_used_bytes) / sum(kubelet_volume_stats_capacity_bytes)'
prom alerts.json 'ALERTS{alertstate="firing"}'
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' > "$EVID/node-names.txt"
while read -r name; do
  [ -n "$name" ] || continue
  kubectl get --raw "/api/v1/nodes/${name}/proxy/configz" > "$EVID/configz-${name}.json" 2>"$EVID/configz-${name}.err" || echo "未采集：${name}" > "$EVID/configz-${name}.json"
done < "$EVID/node-names.txt"
cleanup
trap - EXIT
```

- 读取：reference.md「口径」的资源汇总查询、节点 PromQL、磁盘阈值
- 写入：`$EVID/cpu.json`、`$EVID/mem-cluster.json`、`$EVID/mem-nodes.json`、`$EVID/rootfs.json`、`$EVID/gpu-util.json`、`$EVID/storage.json`、`$EVID/alerts.json`、`$EVID/node-names.txt`、每个节点的 `$EVID/configz-<节点名>.json`。由 `mem-nodes.json` 和 `rootfs.json` 本地算出周期最大、最小和峰值时间，写入 `$EVID/node-usage-period.json`
- 完成：上述文件都存在，且 port-forward 进程已结束。没采到的序列在对应文件中以 `未采集：` 开头
- 失败：采集失败。确认 port-forward 已结束，然后进入 S10。禁止用 `kubectl debug`、`kubectl exec` 或节点上的 `df` 补根分区

### S10 — 巡检 Events 和关键错误日志

- 动作：采集 Warning Events。不额外读取节点或组件日志
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get events -A --field-selector type=Warning > "$EVID/warning-events.txt" 2>&1
kubectl get events -A -o json > "$EVID/events.json" 2>&1
```

- 读取：无
- 写入：`$EVID/warning-events.txt`、`$EVID/events.json`
- 完成：两个文件都存在。结论只使用落在本周期内的事件，周期外事件必须标明
- 失败：采集失败。记录后进入 S11

### S11 — 巡检命名空间及核心业务服务

- 动作：采集 Notebook、KServe、Pipeline，并对照 Pod 证据核对核心组件
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get notebooks.kubeflow.org -A > "$EVID/notebooks.txt" 2>&1
kubectl get inferenceservices.serving.kserve.io -A > "$EVID/kserve.txt" 2>&1
kubectl get workflows.argoproj.io -A > "$EVID/workflows.txt" 2>&1
kubectl get pods -n kyverno -o wide > "$EVID/kyverno.txt" 2>&1
python3 - "$EVID/pods.json" "$EVID/image-pull.txt" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
try:
    items = json.load(open(src)).get("items", [])
except Exception as exc:
    open(dst, "w").write(f"未采集：{exc}\n")
    raise SystemExit(0)
rows = []
for pod in items:
    ns = pod.get("metadata", {}).get("namespace", "")
    name = pod.get("metadata", {}).get("name", "")
    statuses = pod.get("status", {}).get("containerStatuses") or []
    for st in statuses:
        waiting = (st.get("state") or {}).get("waiting") or {}
        reason = waiting.get("reason") or ""
        if reason in ("ImagePullBackOff", "ErrImagePull"):
            rows.append(f"{ns}/{name} {st.get('name','')} {reason} {waiting.get('message','')}")
open(dst, "w").write("\n".join(rows) + ("\n" if rows else "未发现 ImagePullBackOff 或 ErrImagePull\n"))
PY
kubectl -n harbor port-forward svc/harbor-core 19080:80 >"$EVID/harbor-port-forward.txt" 2>&1 &
HP=$!
cleanup() { kill "$HP" 2>/dev/null || true; wait "$HP" 2>/dev/null || true; }
trap cleanup EXIT
ok=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -sf http://127.0.0.1:19080/api/v2.0/health -o "$EVID/harbor-health.json" && ok=1 && break
  sleep 1
done
if [ "$ok" -ne 1 ]; then
  echo '未采集：Harbor /api/v2.0/health 失败' > "$EVID/harbor-health.json"
fi
cleanup
trap - EXIT
```

- 读取：`$EVID/pods.txt`。核心组件为 Kubernetes 控制平面、Kubeflow Dashboard、Istio 网关、Prometheus/Grafana、local-path-provisioner、Harbor 代理缓存、GPU 驱动
- 写入：上述命令的文件，以及 `$EVID/core-services.txt`。每个核心组件一行，写明状态或 `未采集：` 和原因。Harbor 行必须引用 `harbor-health.json`
- 完成：`notebooks.txt`、`kserve.txt`、`workflows.txt`、`kyverno.txt`、`image-pull.txt`、`harbor-health.json`、`core-services.txt` 都存在，且 harbor 的 port-forward 已结束
- 失败：采集失败。确认 port-forward 已结束，记录后进入 S12。禁止触发 Harbor 漏洞扫描

### S12 — 巡检 PVC/PV 和存储容量

- 动作：采集 PVC、PV 和存储状态
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get pvc,pv -A > "$EVID/storage.txt" 2>&1
kubectl get pvc,pv -A -o json > "$EVID/storage.json" 2>&1
python3 - "$EVID/storage.json" "$EVID/pvc-created.txt" "$PERIOD_START" "$PERIOD_END" <<'PY'
import json, sys
from datetime import datetime, timezone, timedelta
src, dst, start, end = sys.argv[1:]
tz = timezone(timedelta(hours=8))
try:
    items = json.load(open(src)).get("items", [])
except Exception as exc:
    open(dst, "w").write(f"未采集：{exc}\n")
    raise SystemExit
begin = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=tz)
until = datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=tz)
rows = []
for item in items:
    if item.get("kind") != "PersistentVolumeClaim":
        continue
    meta = item.get("metadata", {})
    created = meta.get("creationTimestamp")
    if not created:
        continue
    stamp = datetime.fromisoformat(created.replace("Z", "+00:00")).astimezone(tz)
    if begin <= stamp <= until:
        rows.append(f"{meta.get('namespace')}/{meta.get('name')} {stamp.isoformat()}")
open(dst, "w").write("\n".join(rows) + ("\n" if rows else "本周期无新增业务数据卷\n"))
PY
```

- 读取：无
- 写入：`$EVID/storage.txt`、`$EVID/storage.json`、`$EVID/pvc-created.txt`
- 完成：三个文件都存在。PVC 用途只写名称、命名空间、创建时间能够证明的信息；证明不了写「未证实」
- 失败：采集失败。记录后进入 S13

### S13 — 巡检网络、Ingress、Service 和证书有效期

- 动作：采集 Service、Ingress 和 cert-manager 证书
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get svc,ingress -A > "$EVID/network.txt" 2>&1
kubectl get certificates.cert-manager.io -A -o json > "$EVID/certificates.json" 2>&1
server=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
server=${server#https://}
server=${server%/}
echo | openssl s_client -connect "$server" -servername kubernetes 2>/dev/null | openssl x509 -noout -dates -subject -issuer > "$EVID/apiserver-cert.txt" 2>&1 || echo '未采集：无法读取 kube-apiserver 证书' > "$EVID/apiserver-cert.txt"
```

- 读取：无
- 写入：`$EVID/network.txt`、`$EVID/certificates.json`、`$EVID/apiserver-cert.txt`
- 完成：三个文件都存在。证书结论只写剩余有效期；资源不存在时文件中保留错误原文
- 失败：采集失败。记录后进入 S14。禁止创建工作负载补采证书

### S14 — 巡检告警、故障、变更及处理

- 动作：整理本周期告警、故障、变更、处理记录和 Velero 备份
- 命令：

```bash
EVID=/home/storage/k8s-weekly-inspection/output/evidence-YYYYMMDD
mkdir -p "$EVID"
kubectl get backups.velero.io -A > "$EVID/velero.txt" 2>&1
kubectl get backups.velero.io -A -o json > "$EVID/velero.json" 2>&1
kubectl get schedules.velero.io -A > "$EVID/velero-schedules.txt" 2>&1
kubectl get schedules.velero.io -A -o json > "$EVID/velero-schedules.json" 2>&1
```

- 读取：`$EVID/warning-events.txt`、`$EVID/events.json`、`$EVID/pod-anomalies.txt`、`$EVID/alerts.json`、`$EVID/velero.json`、`$EVID/velero-schedules.json`
- 写入：`$EVID/incidents.txt`。按时间写出本周期告警、故障、变更和处理；没有则写「本周期未发现」，并列出仍缺的数据。名称含 `minio` 的 Schedule 和 Backup 单独标出，供第 5 节「MinIO 模型数据备份」使用
- 完成：`velero.txt`、`velero.json`、`velero-schedules.txt`、`velero-schedules.json`、`incidents.txt` 都存在。备份计划的周期只取 Schedule 的 cron。Watchdog、InfoInhibitor 不计入告警结论
- 失败：采集失败。记录后进入 S15

### S15 — 写 Markdown

- 动作：按参考材料把本周期证据写进周报，不另起一套标题
- 命令：无
- 读取：reference.md 的「写作契约」「章节」「口径」「上期落实与下周计划」「内容对应关系」「交付检查」，以及 `$EVID` 中本周期证据。上一份周报只按「上期落实与下周计划」选取
- 写入：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md`
- 完成：文件已保存，七节顺序未改，且「交付检查」每一条都满足。缺失项写明缺什么、影响哪一节
- 失败：停在本步并改正，直到「交付检查」通过。不得进入 S16，不得用模板旧数字填空

### S16 — 渲染 PDF

- 动作：用渲染脚本生成 PDF。脚本自行读取设计语言，不在脚本里改色、改字号或去掉 emoji 回退
- 命令：

```bash
python3 /home/storage/k8s-weekly-inspection/scripts/render_weekly_report.py \
  /home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md \
  /home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf
```

- 读取：`template/design-language.yaml`
- 写入：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf`
- 完成：PDF 文件存在且非空
- 失败：停在本步并报告脚本输出。不得手写一套 PDF，不得进入 S17

### S17 — 说明交付结果

- 动作：向用户说明本次交付
- 命令：无
- 读取：Markdown、PDF 和 `$EVID`
- 写入：无
- 完成：回复中写明 Markdown 路径、PDF 路径、周期、数据来源、缺失项
- 失败：路径对不上实际文件时停在本步，先纠正路径再说明

## 约束

以下各项约束全部步骤，本身不是步骤：

- 巡检过程以只读操作为主，不得修改、重启或删除任何集群资源。
- 禁止 `apply`、`delete`、`patch`、`scale`、`rollout restart`、`cordon`、`drain`、`debug`，以及任何会创建 Pod 或修改资源的命令。
- `kubectl port-forward` 只允许出现在写明该命令的步骤中，用完必须在离开该步前结束本地进程。
- `kubectl exec` 只允许 S6 对已有 `app=nvidia-dcgm-exporter` Pod 执行列出的 `nvidia-smi`。禁止其他 `exec`。
- 采集只执行各步代码块里的命令。代码块没有的查询不要另做；失败就写 `未采集：` 和原因。
- 所有结论必须基于实际命令输出或监控数据，不得猜测或补造数据。
- 如果缺少访问权限、历史监控数据或必要信息，应明确列出缺失项及影响，不要用虚构内容填充。
- 对发现的问题按照「严重、警告、提示」分级，并提供处理建议。
- 保留关键巡检命令和数据来源，确保结果可以复核。证据目录保留原始输出；周报正文不粘贴完整日志。
- 不得写入密码、Token、私钥、Secret data 或完整凭据。
- 不要手写 HTML 颜色或色值。颜色只来自 `design-language.yaml`。
- 状态符只使用 `✅`、`⚠️`、`❌`。渲染后分别为绿色 `[OK]`、琥珀色 `[!]`、红色 `[X]`。本周重点、严重核心行、异常行和复发行的红色由 reference.md「写作契约」触发。
- 采集失败不等于阻断失败。S6 至 S14 的采集失败记录后继续；S1、S2、S3、S4、S5、S15、S16、S17 的失败停在该步。

## 输出

- Markdown：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md`
- PDF：`/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf`
- `YYYYMMDD` 用周期结束日。
- 七节标题、表格列和固定导语以 reference.md「章节」为准，不另起标题。
- 巡检概况、集群运行状态、资源使用、异常与告警、故障及变更、风险、处理建议、巡检结论分别写入哪一节，见 reference.md「内容对应关系」。
- S17 的回复写明上面两个路径、周期、数据来源和缺失项。

## 参考

- [reference.md](reference.md) 只提供写法、章节骨架、口径、上期计划规则、内容对应关系和交付检查。
- 该文件里的序号是周报条目或核对项，不是本技能的执行步骤。
- 渲染脚本：`/home/storage/k8s-weekly-inspection/scripts/render_weekly_report.py`
