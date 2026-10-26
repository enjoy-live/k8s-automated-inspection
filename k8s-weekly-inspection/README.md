# Kubernetes 维护周报自动巡检

## 目的

每周一 08:00（Asia/Shanghai）自动对当前 Kubernetes 集群做只读巡检，并按固定模板生成维护周报。也可以手工指定周期后立即生成。

## 前置条件

- 当前用户可以执行 `kubectl` 只读命令，kubeconfig 为 `kubernetes-admin@kubernetes`。
- 已安装 `python3`、`reportlab`、`pdftotext`。
- Cursor Agent 位于 `/home/storage/.local/bin/agent`。
- Agent 已登录，或在 `/home/storage/k8s-weekly-inspection/cursor.env` 中设置 `CURSOR_API_KEY`。该文件权限应为 `600`，不要写入周报。

## 核心步骤

模板与设计语言：

- 章节样例 PDF：`/home/storage/k8s-weekly-inspection/template/维护周报.pdf`
- PDF 视觉定稿：`/home/storage/k8s-weekly-inspection/template/design-language.yaml`（色板、字号、表格、状态符回退；改样式只改此文件）

技能文件：

- `/home/storage/.cursor/skills/k8s-weekly-inspection/SKILL.md`
- `/home/storage/.cursor/skills/k8s-weekly-inspection/reference.md`

定时触发脚本：

`/home/storage/k8s-weekly-inspection/scripts/trigger.sh`

未传日期时，脚本取“最近一个已经结束的自然周”：周一 00:00 至周日 23:59。每周一早上运行时，这个区间就是上一周。

安装定时任务：

```bash
bash /home/storage/k8s-weekly-inspection/scripts/install-cron.sh
```

对应 crontab 为 `0 8 * * 1`，时区跟随服务器的 Asia/Shanghai。

手工指定周期：

```bash
bash /home/storage/k8s-weekly-inspection/scripts/trigger.sh \
  --start 2026-09-21 --end 2026-09-30
```

在 Cursor 对话中手工调用时，只需说明周期，不必重复巡检限制：

```text
使用 k8s-weekly-inspection 技能，巡检周期 2026-09-21 至 2026-09-30，直接开始。
```

周报输出：

- `/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.md`
- `/home/storage/k8s-weekly-inspection/output/维护周报-YYYYMMDD.pdf`

`YYYYMMDD` 是周期结束日。命令证据在同目录的 `evidence-YYYYMMDD/`。运行日志在 `/home/storage/k8s-weekly-inspection/logs/`。

PDF 由 `/home/storage/k8s-weekly-inspection/scripts/render_weekly_report.py` 读取 `design-language.yaml` 生成。页边距、字体、表头蓝底沿用 09-21 / 09-30 / 10-12 交付版；本周重点、严重核心行、警告整行，以及含「异常」「复发」的行，按该文件里的强调色渲染。

## 验证方法

```bash
bash /home/storage/k8s-weekly-inspection/scripts/trigger.sh --dry-run
crontab -l | grep k8s-weekly-inspection
kubectl auth can-i get nodes
/home/storage/.local/bin/agent status
```

`--dry-run` 只打印周期和提示词路径，不连接模型。Agent 显示已登录后，去掉 `--dry-run` 才会真正巡检。

## 结果

- 模板、技能、触发脚本和周一 08:00 定时任务已安装在本项目内。
- 当前服务器上的 Agent 尚未登录。完成 `agent login` 或写好 `cursor.env` 之前，定时任务会记录失败并退出，不会改动集群。
