import json
from typing import Tuple, Optional

import typer
from rich.syntax import Syntax

from pyrrowhead.management import common, serviceregistry, orchestrator
from pyrrowhead import rich_console

orch_app = typer.Typer(name="orchestration")


@orch_app.command(name="add")
def add_orchestration_rule_cli(
    service_definition: str = common.ARG_SERVICE_DEFINITION,
    service_interface: str = common.ARG_SERVICE_INTERFACE,
    provider: Tuple[str, str, int] = typer.Option(
        ...,
        show_default=False,
        metavar="SYSTEM_NAME ADDRESS PORT",
        help="Provider system definition.",
    ),
    consumer_id: Optional[int] = typer.Option(
        None, metavar="CONSUMER_ID", help="Incompatible with " "CONSUMER option"
    ),  # Union[int, str, Tuple[str, str, int]] = typer.Option(...),
    consumer: Tuple[str, str, int] = typer.Option(
        (None, None, None),
        show_default=False,
        metavar="SYSTEM_NAME ADDRESS PORT",
        help="Consumer system definition, " "incompatible with CONSUMER_ID option.",
    ),
    priority: int = typer.Option(1),
    add_auth_rule: Optional[bool] = typer.Option(
        None,
        "--add-authentication",
        "-A",
        help="Add authentication rule in together " "with the authentication rule",
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
            "No consumer information given, you must provide "
            "Pyrrowhead with either the consumer id (--consumer-id), "
            "consumer name (--consumer-name) or "
            "full consumer information (--consumer-system)."
        )

    if consumer_id == -1:
        rich_console.print(f"No consumer systems found for consumer {consumer[0]}")
        raise typer.Exit()
    if consumer_id == -2:
        rich_console.print(
            f"Multiple candidate systems found for consumer {consumer[0]}, "
            f"please specify address and port"
        )
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


@orch_app.command(name="list")
def list_orchestration_cli(
    service_definition: Optional[str] = typer.Option(
        None, metavar="SERVICE_DEFINITION"
    ),
    provider_id: Optional[int] = typer.Option(None),
    provider_name: Optional[str] = typer.Option(None),
    consumer_id: Optional[int] = typer.Option(None),
    consumer_name: Optional[str] = typer.Option(None),
    sort_by: orchestrator.SortbyChoices = typer.Option("id"),
    raw_output: bool = common.OPT_RAW_OUTPUT,
    raw_indent: Optional[int] = common.OPT_RAW_INDENT,
):
    response_data, status = orchestrator.list_orchestration_rules()

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=raw_indent), "json"))
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


@orch_app.command(name="remove")
def remove_orchestration_cli(orchestration_id: int):
    response_data, status = orchestrator.remove_orchestration_rule(orchestration_id)
