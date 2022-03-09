import json
from typing import Optional, Tuple

import typer
from rich.syntax import Syntax
from rich.text import Text

from pyrrowhead.management import common, serviceregistry
from pyrrowhead.management.common import AccessPolicy
from pyrrowhead import rich_console

sr_app = typer.Typer(
    name="services", help="Service related commands. See list for further information."
)


@sr_app.command(name="list")
def services_list_cli(
    service_definition: Optional[str] = typer.Option(
        None,
        show_default=False,
        metavar="SERVICE_DEFINITION",
        help="Filter services by SERVICE_DEFINITION",
    ),
    system_name: Optional[str] = typer.Option(
        None,
        show_default=False,
        metavar="SYSTEM_NAME",
        help="Filter services by SYSTEM_NAME",
    ),
    system_id: Optional[int] = typer.Option(
        None,
        show_default=False,
        metavar="SYSTEM_ID",
        help="Filter services by SYSTEM_ID",
    ),
    show_service_uri: bool = typer.Option(
        False, "--show-service-uri", "-u", show_default=False, help="Show service uri"
    ),
    show_access_policy: bool = typer.Option(
        False,
        "--show-access-policy",
        "-c",
        show_default=False,
        help="Show access policy",
    ),
    show_provider: bool = typer.Option(
        None, "--show-provider", "-s", help="Show provider system"
    ),
    raw_output: bool = common.OPT_RAW_OUTPUT,
    indent: Optional[int] = common.OPT_RAW_INDENT,
):
    """
    List services registered in the active local cloud, sorted by ID.

    Services shown can be filtered by service definition or system. More information about the
    services can be seen with the -usc flags. The raw json data is accessed by the -r flag.
    """  # noqa
    exclusive_options = (service_definition, system_name, system_id)
    if len(list(option for option in exclusive_options if option is not None)) > 1:
        raise RuntimeError(
            "Only one of the options <--service-definition, --system-name, --system-id>"
            " may be used."
        )

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
        rich_console.print(Syntax(json.dumps(list_data, indent=indent), "json"))
        raise typer.Exit()

    service_table = serviceregistry.create_service_table(
        list_data, show_provider, show_access_policy, show_service_uri
    )

    rich_console.print(service_table)


@sr_app.command(name="inspect")
def inspect_service_cli(
    service_id: int = typer.Argument(
        ..., metavar="SERVICE_ID", help="ID of service to inspect."
    ),
    raw_output: Optional[bool] = common.OPT_RAW_OUTPUT,
    raw_indent: Optional[int] = common.OPT_RAW_INDENT,
):
    """
    Show information about service given by ID.
    """
    response_data, status = serviceregistry.inspect_service(service_id)

    if status >= 400:
        rich_console.print(
            f"Error occured when trying to inspect service with id {service_id} due to:"
            f' {response_data["exceptionType"]}, {response_data["errorMessage"]}'
        )
        raise typer.Exit(-1)

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=raw_indent), "json"))
        raise typer.Exit()

    serviceregistry.render_service(response_data)


@sr_app.command(name="add")
def add_service_cli(
    service_definition: str = common.ARG_SERVICE_DEFINITION,
    uri: str = common.ARG_SERVICE_URI,
    interface: str = common.ARG_SERVICE_INTERFACE,
    access_policy: AccessPolicy = typer.Option(
        AccessPolicy.CERTIFICATE,
        metavar="ACCESS_POLICY",
        help='Must be one of three values: "NOT_SECURE", ' '"CERTIFICATE", or "TOKEN"',
    ),
    system: Tuple[str, str, int] = typer.Option(
        ...,
        show_default=False,
        metavar="SYSTEM_NAME ADDRESS PORT",
        help="Provider system definition.",
    ),
    system_id: Optional[int] = typer.Option(None, help="Not yet supported"),
):
    """
    Add service to service registry
    """
    # TODO: Implement system_id option
    if all((all(system), system_id)):
        rich_console.print("--System and --system-id are mutually exclusive options.")
        raise typer.Exit()
    elif not any((all(system), system_id)):
        rich_console.print("One option of --system or --system-id must be set.")
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
        rich_console.print(
            Text(f'Service registration failed: {response_data["errorMessage"]}')
        )
        raise typer.Exit(-1)

    serviceregistry.render_service(response_data)


@sr_app.command(name="remove")
def remove_service_cli(
    id: int = typer.Argument(..., metavar="SERVICE_ID", help="Id of service to remove"),
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
        rich_console.print(
            Text(f'Service unregistration failed: {response_data["errorMessage"]}')
        )
        raise typer.Exit(-1)
