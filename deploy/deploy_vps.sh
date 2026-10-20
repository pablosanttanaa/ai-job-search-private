#!/usr/bin/env bash
# Sube el proyecto al VPS y (re)instala los servicios del dashboard.
#
#   bash deploy/deploy_vps.sh            # usa el alias SSH "oracle-madrid" (~/.ssh/config)
#   SSH_HOST=otro-alias bash deploy/deploy_vps.sh
#
# Nunca sube claves (*.key, *.pem), .git ni node_modules. El estado del scraper
# en el VPS (seen_jobs.json, runs.json, settings.json) es la fuente de verdad del dashboard:
# solo se copia el local si en el VPS todavía no existe.
set -euo pipefail

HOST="${SSH_HOST:-oracle-madrid}"
DEST=/opt/ai-job-search
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Empaquetando y subiendo a $HOST:$DEST"
tar czf - \
  --exclude=.git --exclude=node_modules --exclude='*.key' --exclude='*.pem' \
  --exclude='.env' --exclude='*.lockb' --exclude=__pycache__ \
  --exclude=job_scraper/seen_jobs.json --exclude=job_scraper/runs.json \
  --exclude=job_scraper/scrape.lock --exclude=job_scraper/last_run.log \
  --exclude=job_scraper/settings.json \
  . | ssh "$HOST" "sudo mkdir -p $DEST && sudo chown ubuntu:ubuntu $DEST && tar xzf - -C $DEST"

if ! ssh "$HOST" "test -f $DEST/job_scraper/seen_jobs.json"; then
  echo "==> Primer despliegue: copio seen_jobs.json local"
  ssh "$HOST" "mkdir -p $DEST/job_scraper"
  scp job_scraper/seen_jobs.json "$HOST:$DEST/job_scraper/seen_jobs.json"
fi

echo "==> Instalando servicios systemd"
ssh "$HOST" "sudo cp $DEST/deploy/ai-job-dashboard.service $DEST/deploy/ai-job-scrape.service $DEST/deploy/ai-job-scrape.timer /etc/systemd/system/ \
  && sudo systemctl daemon-reload \
  && sudo systemctl enable --now ai-job-scrape.timer \
  && sudo systemctl enable ai-job-dashboard.service \
  && sudo systemctl restart ai-job-dashboard.service \
  && systemctl is-active ai-job-dashboard.service \
  && systemctl list-timers ai-job-scrape.timer --no-pager | head -3"
echo "==> Listo"
