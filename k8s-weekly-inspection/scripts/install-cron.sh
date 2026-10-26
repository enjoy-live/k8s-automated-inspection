#!/usr/bin/env bash
# 安装每周一 08:00（Asia/Shanghai）的巡检定时任务。
set -euo pipefail

TRIGGER=/home/storage/k8s-weekly-inspection/scripts/trigger.sh
MARK="# k8s-weekly-inspection"
LINE="0 8 * * 1 ${TRIGGER} ${MARK}"

current="$(crontab -l 2>/dev/null || true)"
filtered="$(printf '%s\n' "${current}" | grep -v 'k8s-weekly-inspection' || true)"
{
  printf '%s\n' "${filtered}" | sed '/^$/d'
  printf '%s\n' "${LINE}"
} | crontab -

echo "已安装定时任务:"
crontab -l | grep 'k8s-weekly-inspection'
