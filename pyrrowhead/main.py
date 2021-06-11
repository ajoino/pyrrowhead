import typer

from pyrrowhead.management.authorization import auth_app
from pyrrowhead.management.orchestrator import orch_app
from pyrrowhead.management.serviceregistry import sr_app
from pyrrowhead.management.systemregistry import sys_app
from pyrrowhead.cloud.main import cloud_app

app = typer.Typer()
app.add_typer(sr_app)
app.add_typer(orch_app)
app.add_typer(auth_app)
app.add_typer(sys_app)
app.add_typer(cloud_app)

if __name__ == '__main__':
    app()
