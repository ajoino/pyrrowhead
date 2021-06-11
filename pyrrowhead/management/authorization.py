import typer

auth_app = typer.Typer(name='authorization')

@auth_app.command(name='list')
def list_authorization_rules():
    pass

@auth_app.command(name='add')
def add_authorization_rule():
    pass

@auth_app.command(name='remove')
def remove_authorization_rule():
    pass