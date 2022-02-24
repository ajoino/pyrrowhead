import json
from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.syntax import Syntax
from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.management.common import AccessPolicy
from pyrrowhead.management import(
    authorization,
    orchestrator,
    serviceregistry,
    systemregistry,
    common,
)

sr_app = typer.Typer(name='services', help='Service related commands. See list for further information.')


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
        raw_output: bool = common.OPT_RAW_OUTPUT,
        indent: Optional[int] = common.OPT_RAW_INDENT,
):
    """
    List services registered in the active local cloud, sorted by ID.

    Services shown can be filtered by service definition or system. More information about the
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
        service_id: int = typer.Argument(..., metavar='SERVICE_ID',
                                         help='ID of service to inspect.'),
        raw_output: Optional[bool] = common.OPT_RAW_OUTPUT,
        raw_indent: Optional[int] = common.OPT_RAW_INDENT,
):
    """
    Show information about service given by ID.
    """
    response_data, status = serviceregistry.inspect_service(service_id)

    if status >= 400:
        rich_console.print(
                f'Error occured when trying to inspect service with id {service_id} due to: '
                f'{response_data["exceptionType"]}, {response_data["errorMessage"]}'
        )
        raise typer.Exit(-1)

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=raw_indent), 'json'))
        raise typer.Exit()

    serviceregistry.render_service(response_data)


@sr_app.command(name='add')
def add_service_cli(
        service_definition: str = common.ARG_SERVICE_DEFINITION,
        uri: str = common.ARG_SERVICE_URI,
        interface: str = common.ARG_SERVICE_INTERFACE,
        access_policy: AccessPolicy = typer.Option(
        AccessPolicy.CERTIFICATE, metavar='ACCESS_POLICY',
        help='Must be one of three values: "NOT_SECURE", '
             '"CERTIFICATE", or "TOKEN"'
        ),
        system: Optional[Tuple[str, str, int]] = typer.Option(
            (None, None, None),
            show_default=False,
            metavar='SYSTEM_NAME ADDRESS PORT',
            help='Provider system definition.'
        ),
        system_id: Optional[int] = typer.Option(None, help='Not yet supported'),
):
    """
    Add service to service registry
    """
    # TODO: Implement system_id option
    if all((all(system), system_id)):
        rich_console.print('--System and --system-id are mutually exclusive options.')
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
    if response_code >= 400:
        rich_console.print(Text(f'Service registration failed: {response_data["errorMessage"]}'))
        raise typer.Exit(-1)

    serviceregistry.render_service(response_data)

@sr_app.command(name='remove')
def remove_service_cli(
        id: int = typer.Argument(..., metavar='SERVICE_ID',
                                 help='Id of service to remove'),
):
    """
    Remove service from service registry by ID.
    """
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
        service_definition: str = common.ARG_SERVICE_DEFINITION,
        service_interface: str = common.ARG_SERVICE_INTERFACE,
        provider: Tuple[str, str, int] = typer.Option(
            ...,
            show_default=False,
            metavar='SYSTEM_NAME ADDRESS PORT',
            help='Provider system definition.'
        ),
        consumer_id: Optional[int] = typer.Option(None, metavar='CONSUMER_ID',
                                                  help='Incompatible with '
                                                       'CONSUMER option'), #Union[int, str, Tuple[str, str, int]] = typer.Option(...),
        consumer: Tuple[str, str, int] = typer.Option(
            (None, None, None),
            show_default=False,
            metavar='SYSTEM_NAME ADDRESS PORT',
            help='Consumer system definition, '
                 'incompatible with CONSUMER_ID option.'
        ),
        priority: int = typer.Option(1),
        add_auth_rule: Optional[bool] = typer.Option(None, '--add-authentication', '-A',
                                                     help='Add authentication rule in together '
                                                          'with the authentication rule'
        ),
):
    if consumer_id is not None:
        pass
    elif not all(consumer):
        consumer_id = serviceregistry.get_system_id_from_name(*consumer)
    elif all(consumer):
        consumer_id = serviceregistry.get_system_id_from_name(*consumer)
    else:
        rich_console.print(
                "No consumer information given, you must provide Pyrrowhead with either the "
                "consumer id (--consumer-id), consumer name (--consumer-name) or full consumer "
                "information (--consumer-system).")

    if consumer_id == -1:
        rich_console.print(f'No consumer systems found for consumer {consumer[0]}')
        raise typer.Exit()
    if consumer_id == -2:
        rich_console.print(
                f'Multiple candidate systems found for consumer {consumer[0]}, please specify address and port')
        raise typer.Exit()

    response_data, status = orchestrator.add_orchestration_rule(
            service_definition=service_definition,
            service_interface=service_interface,
            provider_system=provider,
            consumer_id=consumer_id,
            priority=priority,
            add_auth_rule=add_auth_rule,
    )

    if status >= 400:
        print(response_data["errorMessage"], status)


@orch_app.command(name='list')
def list_orchestration_cli(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
        sort_by: orchestrator.SortbyChoices = typer.Option('id'),
        raw_output: bool = common.OPT_RAW_OUTPUT,
        raw_indent: Optional[int] = common.OPT_RAW_INDENT,
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
    """
    Prints all orchestration rules, no filters or sorting options are implemented yet.
    """
    response_data, status = authorization.list_authorization_rules()

    rich_console.print(authorization.create_authorization_table(response_data))


@auth_app.command(name='add')
def add_authorization_cli(
        consumer_id: int = typer.Option(...),
        provider_id: int = typer.Option(...),
        interface_id: int = typer.Option(...),
        service_definition_id: int = typer.Option(...),
):
    """
    Add authorization rule by ids.
    """
    authorization.add_authorization_rule(consumer_id, provider_id, interface_id, service_definition_id)


@auth_app.command(name='remove')
def remove_authorization_cli():
    """Not implemented."""
    rich_console.print("Not implemented.")
    raise typer.Exit(-1)
    authorization.remove_authorization_rule()


sys_app = typer.Typer(name='systems')


@sys_app.command(name='list')
def list_systems_cli(
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False),
        indent: Optional[int] = typer.Option(None, '--raw-indent')
):
    """List systems registered in the local cloud"""
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
    """Remove system by id."""
    response_data, status = systemregistry.remove_system(system_id)