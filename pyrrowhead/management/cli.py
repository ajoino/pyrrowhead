import json
from pathlib import Path
from typing import Optional, Tuple

import typer
from rich import box
from rich.console import RenderGroup
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.management.common import AccessPolicy
from pyrrowhead.management import(
    authorization,
    common,
    deviceregistry,
    orchestrator,
    serviceregistry,
    systemregistry,
    utils,
)

sr_app = typer.Typer(name='services')


@sr_app.command(name='list')
def services_list_cli(
        service_definition: Optional[str] = typer.Option(None, show_default=False, metavar='SERVICE_DEFINITION',
                                                         help='Filter services by SERVICE_DEFINITION'),
        system_name: Optional[str] = typer.Option(None, show_default=False, metavar='SYSTEM_NAME',
                                                  help='Filter services by SYSTEM_NAME'),
        system_id: Optional[int] = typer.Option(None, show_default=False, metavar='SYSTEM_ID',
                                                help='Filter services by SYSTEM_ID'),
        show_service_uri: bool = typer.Option(False, '--show-service-uri', '-u', show_default=False,
                                              help='Show service uri'),
        show_access_policy: bool = typer.Option(False, '--show-access-policy', '-c', show_default=False,
                                                help='Show access policy'),
        show_provider: bool = typer.Option(None, '--show-provider', '-s', help='Show provider system'),
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False,
                                        help='Show information as json'),
        indent: Optional[int] = typer.Option(None, '--raw-indent', metavar='NUM_SPACES',
                                             help='Print json with NUM_SPACES spaces of indentation')
):
    """
    List services registered in the active local cloud, sorted by id. Services shown can
    be filtered by service definition or system. More information about the
    services can be seen with the -usc flags. The raw json data is accessed by the -r flag.
    """
    exclusive_options = (service_definition, system_name, system_id)
    if len(list(option for option in exclusive_options if option is not None)) > 1:
        raise RuntimeError('Only one of the options <--service-definition, --system-name, --system-id> may be used.')

    try:
        list_data = serviceregistry.list_services(
                service_definition,
                system_name,
                system_id,
        )
    except RuntimeError as e:
        rich_console.print(e)
        raise typer.Exit(code=-1)

    if raw_output:
        rich_console.print(Syntax(json.dumps(list_data, indent=indent), 'json'))
        raise typer.Exit()

    service_table = serviceregistry.create_service_table(list_data, show_provider, show_access_policy, show_service_uri)

    rich_console.print(service_table)


@sr_app.command(name='inspect')
def inspect_service_cli(
        service_id: int,
        raw_output: Optional[bool] = None,
        indent: Optional[int] = None,
):
    """
    Show all information regarding specific service.
    """
    response_data = serviceregistry.inspect_service(service_id)

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=indent), 'json'))
        raise typer.Exit()

    tab_break = "\n\t"
    provider = response_data["provider"]
    render_group = RenderGroup(
            (f'Service URI: {response_data["serviceUri"]}'),
            (f'Interfaces: [bright_yellow]\n\t{tab_break.join(interface["interfaceName"] for interface in response_data["interfaces"])}[/bright_yellow]'),
            (f'Access policy: [orange3]{response_data["secure"]}[/orange3]'),
            (f'Version: {response_data["version"]}'),
            (
                    f'Provider:'
                    f'{tab_break}Id: {provider["id"]}'
                    f'{tab_break}System name: [blue]{provider["systemName"]}[/blue]'
                    f'{tab_break}Address: {provider["address"]}'
                    f'{tab_break}Port: {provider["port"]}'
            ),
            # TODO: "Always valid" should be printed in green and not red
            ( f'End of validity: [red]{response_data.get("endOfValidity", "[green]Always valid[/green]")}[/red]'),
    )
    if (metadata := response_data.get("metadata")):
        render_group.renderables.append(f'Metadata: {tab_break} {tab_break.join(f"{name}: {value}" for name, value in metadata.items())}')
    rich_console.print(
            (f' Service "{response_data["serviceDefinition"]["serviceDefinition"]}" (id: {service_id})'),
            Panel(render_group, box=box.HORIZONTALS, expand=False)
    )


@sr_app.command(name='add')
def add_service_cli(
        service_definition: str,
        uri: str,
        interface: str,
        access_policy: AccessPolicy = typer.Argument(AccessPolicy.CERTIFICATE),
        system: Optional[Tuple[str, str, int]] = typer.Option((None, None, None), show_default=False),
        system_id: Optional[int] = typer.Option(None, help='Not yet supported'),
):
    # TODO: Implement system_id option
    if all((all(system), system_id)):
        rich_console.print('System and system-id are mutually exclusive options.')
        raise typer.Exit()
    elif not any((all(system), system_id)):
        rich_console.print('One option of --system or --system-id must be set.')
        raise typer.Exit()

    try:
        response_data, response_code = serviceregistry.add_service(
                service_definition,
                uri,
                interface,
                access_policy,
                system,
        )
    except IOError as e:
        rich_console.print(e)
        raise typer.Exit(-1)

    # Add service code
    if response_code in {400, 401, 500}:
        rich_console.print(Text(f'Service registration failed: {response_data["errorMessage"]}'))
        raise typer.Exit(-1)


@sr_app.command(name='remove')
def remove_service_cli(
        id: int,
):
    try:
        response_data, status = serviceregistry.delete_service(id)
    except IOError as e:
        rich_console.print(e)
        raise typer.Exit(-1)


    if status in {400, 401, 500}:
        rich_console.print(Text(f'Service unregistration failed: {response_data["errorMessage"]}'))
        raise typer.Exit(-1)


orch_app = typer.Typer(name='orchestration')


@orch_app.command(name='add')
def add_orchestration_rule_cli(
        service_definition: str,
        service_interface: str = typer.Option(..., '--interface'),
        provider_system: Tuple[str, str, int] = typer.Option(..., '--provider'),
        consumer_id: Optional[int] = typer.Option(None), #Union[int, str, Tuple[str, str, int]] = typer.Option(...),
        consumer_name: Optional[str] = typer.Option(None),
        consumer_address: Optional[str] = typer.Option(None),
        consumer_port: Optional[int] = typer.Option(None),
        priority: int = typer.Option(1),
        metadata: Optional[int] = None,
        add_auth_rule: Optional[bool] = typer.Option(None, '--add-authentication', '-A')
):
    if consumer_id is not None:
        pass
    elif consumer_name is not None and consumer_address is None and consumer_port is None:
        consumer_id = serviceregistry.get_system_id_from_name(consumer_name)
    elif consumer_name is not None and consumer_address is not None and consumer_port is not None:
        consumer_id = serviceregistry.get_system_id_from_name(consumer_name, consumer_address, consumer_port)
    else:
        rich_console.print(
                "No consumer information given, you must provide Pyrrowhead with either the "
                "consumer id (--consumer-id), consumer name (--consumer-name) or full consumer "
                "information (--consumer-system).")

    if consumer_id == -1:
        rich_console.print(f'No consumer systems found for consumer {consumer_name}')
        raise typer.Exit()
    if consumer_id == -2:
        rich_console.print(
                f'Multiple candidate systems found for consumer {consumer_name}, please specify address and port')
        raise typer.Exit()

    orchestrator.add_orchestration_rule(
            service_definition,
            service_interface,
            provider_system,
            consumer_id,
            priority,
            metadata,
            add_auth_rule,
    )


@orch_app.command(name='list')
def list_orchestration_cli(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
        sort_by: orchestrator.SortbyChoices = typer.Option('id'),
        raw_output: bool = typer.Option(False),
        raw_indent: Optional[int] = typer.Option(None),
):
    response_data, status = orchestrator.list_orchestration_rules()

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=raw_indent), 'json'))
        raise typer.Exit()

    table = orchestrator.create_orchestration_table(
            response_data,
            service_definition,
            consumer_id,
            consumer_name,
            provider_id,
            provider_name,
            sort_by,
    )

    rich_console.print(table)


@orch_app.command(name='remove')
def remove_orchestration_cli(
        orchestration_id: int
):
    response_data, status = orchestrator.remove_orchestration_rule(orchestration_id)


auth_app = typer.Typer(name='authorization')


@auth_app.command(name='list')
def list_authorization_cli(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
):
    response_data, status = authorization.list_authorization_rules()

    rich_console.print(Syntax(json.dumps(response_data, indent=2), 'json'))


@auth_app.command(name='add')
def add_authorization_cli(
        consumer_id: int = typer.Option(...),
        provider_id: int = typer.Option(...),
        interface_id: int = typer.Option(...),
        service_definition_id: int = typer.Option(...),
):
    authorization.add_authorization_rule(consumer_id, provider_id, interface_id, service_definition_id)


@auth_app.command(name='remove')
def remove_authorization_cli():
    authorization.remove_authorization_rule()


sys_app = typer.Typer(name='systems')


@sys_app.command(name='list')
def list_systems_cli(
        system_name: Optional[str] = typer.Argument('', show_default=False),
        # show_provider: bool = typer.Option(None, '--show-provider', '-s'),
        # show_access_policy: bool = typer.Option(False, '--show-access-policy', '-c', show_default=False),
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False),
        indent: Optional[int] = typer.Option(None, '--raw-indent')
):
    response_data, status = systemregistry.list_systems()

    if raw_output:
        if status >= 400:
            rich_console.print(f'Error code {status}.')
        rich_console.print(Syntax(json.dumps(response_data, indent=indent), 'json'))
        raise typer.Exit()

    table = systemregistry.create_system_table(response_data)

    rich_console.print(table)


@sys_app.command(name='add')
def add_system_cli(
        system_name: str,
        # Add a callback to verify ip
        system_address: str = typer.Argument(..., metavar='ADDRESS'),
        system_port: int = typer.Argument(..., metavar='PORT'),
        certificate_file: Optional[Path] = None
):
    response_data = systemregistry.add_system(system_name, system_address, system_port, certificate_file)

    rich_console.print(Syntax(json.dumps(response_data, indent=2), 'json'))


@sys_app.command(name='remove')
def remove_system_cli(
        system_id: int
):
    response_data, status = systemregistry.remove_system(system_id)