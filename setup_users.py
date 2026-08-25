import argparse
from src.auth import init_db, create_user

p = argparse.ArgumentParser()
p.add_argument("--username", required=True)
p.add_argument("--password", required=True)
p.add_argument("--role", choices=["admin","analyst","viewer"], default="admin")
args = p.parse_args()

init_db()
create_user(args.username, args.password, args.role)
print(f"Created {args.role} user: {args.username}")
