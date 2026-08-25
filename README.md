# EpiFlow v2

EpiFlow v2 upgrades the Streamlit surveillance-intelligence prototype with:

- authentication and role-based access control;
- Admin, Analyst and Viewer roles;
- audit logging;
- explicit Person, Place and Time views;
- analyst-only record-level mapping;
- an aggregated briefing map;
- a decision-oriented surveillance dashboard;
- optional Claude interpretation using aggregated evidence;
- controlled exports.

## Roles

| Capability | Admin | Analyst | Viewer |
|---|---:|---:|---:|
| Upload / raw data | Yes | Yes | No |
| Schema mapping | Yes | Yes | No |
| Quality / cleaning | Yes | Yes | No |
| Person / Place / Time | Yes | Yes | No |
| Internal record-level map | Yes | Yes | No |
| Briefing map | Yes | Yes | Yes |
| Dashboard | Yes | Yes | Yes |
| AI interpretation | Yes | Yes | No |
| Analysis-ready export | Yes | Yes | No |
| Brief export | Yes | Yes | Yes |
| Users / audit log | Yes | No | No |

## Local start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python setup_users.py --username admin --password 'CHANGE_THIS' --role admin
python setup_users.py --username epi01 --password 'CHANGE_THIS' --role analyst
python setup_users.py --username im01 --password 'CHANGE_THIS' --role viewer

export ANTHROPIC_API_KEY='YOUR_KEY'   # optional
streamlit run app.py
```

The application database defaults to `data/epiflow.db`.

## Important v2 boundary

This is still a single-instance Streamlit prototype. Authentication and audit data persist in SQLite, but uploaded surveillance data are held in the Streamlit application session rather than a shared managed data store.

That means v2 is appropriate for a governed demo / controlled prototype, but persistent shared datasets, managed identity, HTTPS termination and cloud storage belong in v3.
