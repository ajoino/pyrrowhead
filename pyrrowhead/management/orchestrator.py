import typer

orch_app = typer.Typer(name='orchestration')

@orch_app.command(name='list')
def list_orchestration_rules():
    pass

@orch_app.command(name='add')
def add_orchestration_rule():
    pass

@orch_app.command(name='remove')
def remove_orchestration_rule():
    pass