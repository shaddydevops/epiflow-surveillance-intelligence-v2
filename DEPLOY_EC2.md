# EpiFlow v2 — EC2 redeployment

This guide assumes the existing EpiFlow deployment is cloned from GitHub on an Ubuntu EC2 instance and currently runs Streamlit on port 8501.

## 0. Before changing the live app

On EC2:

```bash
cd /app
git status
git rev-parse HEAD
git tag pre-v2
git push origin pre-v2
cp data/epiflow.db ~/epiflow.db.pre-v2.backup 2>/dev/null || true
```

If your repository is not `/app`, use its actual path.

## 1. Push v2 to GitHub from your laptop

Copy the v2 files over the current EpiFlow repository, then:

```bash
git add .
git commit -m "Upgrade EpiFlow to v2: RBAC, Person Place Time, maps and dashboard"
git push origin main
```

## 2. SSH to the EC2 instance

```bash
ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## 3. Pull the new code

```bash
cd /app
git pull origin main
```

## 4. Update Python dependencies

```bash
python3 -m venv .venv   # run only if .venv does not already exist
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Create the EpiFlow administrator

```bash
python setup_users.py \
  --username admin \
  --password 'USE_A_LONG_STRONG_PASSWORD' \
  --role admin
```

Then create other accounts:

```bash
python setup_users.py --username epi01 --password 'STRONG_PASSWORD' --role analyst
python setup_users.py --username im01 --password 'STRONG_PASSWORD' --role viewer
```

Do not use these example passwords.

## 6. Configure Claude securely

Create a server environment file:

```bash
sudo nano /etc/epiflow.env
```

Contents:

```bash
ANTHROPIC_API_KEY=YOUR_REAL_KEY
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

Protect it:

```bash
sudo chown root:root /etc/epiflow.env
sudo chmod 600 /etc/epiflow.env
```

## 7. Test v2 manually before restarting the service

```bash
cd /app
source .venv/bin/activate
export EPIFLOW_DB_PATH=/app/data/epiflow.db
set -a
source /etc/epiflow.env
set +a

streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Open:

```text
http://YOUR_EC2_PUBLIC_IP:8501
```

Test all three roles.

Stop with `Ctrl+C`.

## 8. Run EpiFlow as a systemd service

Create or replace:

```bash
sudo nano /etc/systemd/system/epiflow.service
```

Use:

```ini
[Unit]
Description=EpiFlow v2 Streamlit
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/app
Environment="EPIFLOW_DB_PATH=/app/data/epiflow.db"
EnvironmentFile=-/etc/epiflow.env
ExecStart=/app/.venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable epiflow
sudo systemctl restart epiflow
sudo systemctl status epiflow
```

Watch logs:

```bash
journalctl -u epiflow -f
```

## 9. Smoke-test checklist

Admin:
- can login;
- sees raw data, schema, quality, Person/Place/Time, maps, dashboard, AI, exports and Admin;
- sees audit events.

Analyst:
- can upload and analyse;
- sees record-level map;
- cannot see Admin.

Viewer:
- cannot see raw data, schema or cleaning;
- cannot download analysis-ready CSV;
- sees only briefing-level outputs permitted by v2.

AI:
- works when `ANTHROPIC_API_KEY` is present;
- no key is displayed in the UI or repository.

## 10. Roll back quickly

If v2 fails:

```bash
cd /app
git checkout pre-v2
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart epiflow
```

Return to `main` after fixing:

```bash
git checkout main
```

## Security note

Do not treat port 8501 on a public IP as the final production design for health data.

The next infrastructure step should be:
- HTTPS;
- restricted security-group ingress;
- private/persistent data storage;
- secrets management;
- managed organizational identity where possible;
- backups and retention;
- monitoring and alerting.
