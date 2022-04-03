import typer

from pyrrowhead.management.cli import sr_app, orch_app, auth_app, sys_app
from pyrrowhead.cloud.cli import cloud_app

# from pyrrowhead.org.cli import org_app
from pyrrowhead._setup import _setup_pyrrowhead
from pyrrowhead.tui import TuiApp

app = typer.Typer(callback=_setup_pyrrowhead)
app.add_typer(sr_app)
app.add_typer(orch_app)
app.add_typer(auth_app)
app.add_typer(sys_app)
app.add_typer(cloud_app)
# The org command is work in progress
# app.add_typer(org_app)
@app.command("interactive")
def run_tui():
    TuiApp.run()


if __name__ == "__main__":
    app()
