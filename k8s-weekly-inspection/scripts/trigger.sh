#!/usr/bin/env bash
# 生成巡检周期并调用 k8s-weekly-inspection 技能。
# 用法：
#   trigger.sh
#   trigger.sh --start 2026-09-21 --end 2026-09-30
#   trigger.sh --dry-run
set -euo pipefail

export HOME=/home/storage
export TZ=Asia/Shanghai
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

ROOT=/home/storage/k8s-weekly-inspection
SKILL=/home/storage/.cursor/skills/k8s-weekly-inspection/SKILL.md
TEMPLATE="${ROOT}/template/维护周报.pdf"
ENV_FILE="${ROOT}/cursor.env"
LOG_DIR="${ROOT}/logs"
LOCK_FILE="${ROOT}/logs/trigger.lock"
AGENT_BIN="${HOME}/.local/bin/agent"

START_DATE=""
END_DATE=""
DRY_RUN=0

usage() {
  echo "用法: $0 [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--dry-run]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START_DATE="${2:-}"
      shift 2
      ;;
    --end)
      END_DATE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${ENV_FILE}"
  set +a
fi

if ! PERIOD_LINE="$(python3 - "${START_DATE}" "${END_DATE}" <<'PY'
import datetime
import sys

def parse(value):
    if not value:
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        print(f"日期格式必须是 YYYY-MM-DD: {value}", file=sys.stderr)
        raise SystemExit(2)

start = parse(sys.argv[1])
end = parse(sys.argv[2])
if (start is None) != (end is None):
    print("开始日期和结束日期必须同时提供", file=sys.stderr)
    raise SystemExit(2)
if start is None:
    today = datetime.date.today()
    days_since_sunday = today.isoweekday() % 7
    if days_since_sunday == 0:
        days_since_sunday = 7
    end = today - datetime.timedelta(days=days_since_sunday)
    start = end - datetime.timedelta(days=6)
if start > end:
    print("开始日期不能晚于结束日期", file=sys.stderr)
    raise SystemExit(2)

def cn(day):
    return f"{day.year}年{day.month:02d}月{day.day:02d}日"

print(start.isoformat(), end.isoformat(), cn(start), cn(end), end.strftime("%Y%m%d"))
PY
)"; then
  exit 2
fi
read -r START_DATE END_DATE START_CN END_CN END_STAMP <<< "${PERIOD_LINE}"

mkdir -p "${LOG_DIR}" "${ROOT}/output"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="${LOG_DIR}/trigger-${STAMP}.log"
PROMPT_FILE="${LOG_DIR}/prompt-${END_STAMP}-${STAMP}.txt"

cat > "${PROMPT_FILE}" <<EOF
请使用 k8s-weekly-inspection 技能。先读取并严格遵守 ${SKILL}。

巡检统计周期：${START_CN} 00:00 至 ${END_CN} 23:59（Asia/Shanghai）。
PERIOD_START=${START_DATE}
PERIOD_END=${END_DATE}
模板文件：${TEMPLATE}
周报 Markdown：${ROOT}/output/维护周报-${END_STAMP}.md
周报 PDF：${ROOT}/output/维护周报-${END_STAMP}.pdf
证据目录：${ROOT}/output/evidence-${END_STAMP}/

本次由定时触发器调用，K8S_WEEKLY_UNATTENDED=1。kubectl 只读连通性已由触发脚本检查。不要等待人工确认，直接开始只读巡检。不得修改、重启或删除任何集群资源。
EOF

{
  echo "周期: ${START_DATE} 00:00 至 ${END_DATE} 23:59"
  echo "提示词: ${PROMPT_FILE}"
} | tee -a "${LOG_FILE}"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "dry-run：未调用巡检技能"
  exit 0
fi

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "已有巡检任务在运行，本次退出" | tee -a "${LOG_FILE}" >&2
  exit 1
fi

if [[ ! -f "${TEMPLATE}" ]]; then
  echo "缺少模板: ${TEMPLATE}" | tee -a "${LOG_FILE}" >&2
  exit 1
fi
if [[ ! -x "${AGENT_BIN}" ]]; then
  echo "未找到 Cursor Agent: ${AGENT_BIN}" | tee -a "${LOG_FILE}" >&2
  exit 1
fi
if ! kubectl auth can-i get nodes >/dev/null 2>&1; then
  echo "当前账号不能只读访问 Kubernetes 节点，已停止" | tee -a "${LOG_FILE}" >&2
  exit 1
fi
if [[ -z "${CURSOR_API_KEY:-}" ]] && "${AGENT_BIN}" status 2>&1 | tee -a "${LOG_FILE}" | grep -q "Not logged in"; then
  echo "Cursor Agent 未登录。请先执行 agent login，或在 ${ENV_FILE} 中设置 CURSOR_API_KEY 后重试。" | tee -a "${LOG_FILE}" >&2
  exit 1
fi

export K8S_WEEKLY_UNATTENDED=1
set +e
"${AGENT_BIN}" --print --force --trust --sandbox disabled \
  --workspace /home/storage \
  --output-format text \
  "$(cat "${PROMPT_FILE}")" 2>&1 | tee -a "${LOG_FILE}"
AGENT_STATUS=${PIPESTATUS[0]}
set -e

if [[ "${AGENT_STATUS}" -ne 0 ]]; then
  echo "巡检技能执行失败，退出码 ${AGENT_STATUS}" | tee -a "${LOG_FILE}" >&2
  exit "${AGENT_STATUS}"
fi
if [[ ! -f "${ROOT}/output/维护周报-${END_STAMP}.pdf" ]]; then
  echo "技能已返回，但未生成 ${ROOT}/output/维护周报-${END_STAMP}.pdf" | tee -a "${LOG_FILE}" >&2
  exit 1
fi
echo "周报已生成: ${ROOT}/output/维护周报-${END_STAMP}.pdf" | tee -a "${LOG_FILE}"
