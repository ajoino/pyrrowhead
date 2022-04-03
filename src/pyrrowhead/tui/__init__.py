from typing import cast
import json

import rich.console
from rich.panel import Panel
from rich.text import Text
from textual.app import App
from textual.message import Message
from textual.reactive import Reactive
from textual.widgets import Static, Header, Footer
from textual_inputs import TextInput, IntegerInput

from pyrrowhead.utils import get_active_cloud_directory, validate_cloud_config_file
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME


def render_system_info(
    system_name: str = "", address: str = "", port: int = -1
) -> rich.console.RenderableType:
    string = f"System name: {system_name}\nAddress: {address}\nPort: {port if port > 0 else ''}"
    return Panel(string, title="System info", height=8)


class NarrowTextInput(TextInput):
    def render(self) -> rich.console.RenderableType:
        """
        Produce a Panel object containing placeholder text or value
        and cursor.
        """
        if self.has_focus:
            segments = self._render_text_with_cursor()
        else:
            if len(self.value) == 0:
                if self.title and not self.placeholder:
                    segments = [""]
                else:
                    segments = [self.placeholder]
            else:
                segments = [self._modify_text(self.value)]

        text = Text.assemble(
            *segments,
            style=self.style or "",
        )

        return text


class TuiApp(App):
    current_index = Reactive(-1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tab_index = ("system_name", "address", "port")

    async def on_load(self):
        await self.bind("q", "quit", "Quit")
        await self.bind("enter", "submit", "Submit")
        await self.bind("escape", "reset_focus", show=False)
        await self.bind("ctrl+i", "next_tab_index", show=False)
        await self.bind("shift+tab", "previous_tab_index", show=False)

    async def action_submit(self) -> None:
        if self.port.value is None:
            p = -1
        else:
            p = self.port.value
        await self.output.update(
            render_system_info(self.system_name.value, self.address.value, p)
        )

    async def on_mount(self, event):
        self.header = Header()
        await self.view.dock(self.header, edge="top")
        await self.view.dock(Footer(), edge="bottom")

        grid = await self.view.dock_grid()
        grid.add_column("col", max_size=40, repeat=2)
        grid.add_row("row", max_size=1, repeat=20)
        grid.add_areas(
            result="col1,row1-start|row20-end",
            system_name="col2,row1-start|row2-end",
            address="col2,row3",
            port="col2,row4-start|row5-end",
        )

        self.system_name = NarrowTextInput(
            name="system_name",
            placeholder="System name",
            border=None,
        )
        self.system_name.on_change_handler_name = "handle_system_name_on_change"

        self.address = NarrowTextInput(
            name="address",
            placeholder="Address",
        )
        self.address.on_change_handler_name = "handle_address_on_change"

        self.port = IntegerInput(
            name="port",
            placeholder="port",
        )
        self.port.on_change_handler_name = "handle_port_on_change"

        self.output = Static(render_system_info())
        grid.place(
            result=self.output,
            system_name=self.system_name,
            address=self.address,
            port=self.port,
        )

    async def action_next_tab_index(self) -> None:
        """Changes the focus to the next form field"""
        if self.current_index < len(self.tab_index) - 1:
            self.current_index += 1
            await getattr(self, self.tab_index[self.current_index]).focus()

    async def action_previous_tab_index(self) -> None:
        """Changes the focus to the previous form field"""
        if self.current_index > 0:
            self.current_index -= 1
            await getattr(self, self.tab_index[self.current_index]).focus()

    async def action_reset_focus(self) -> None:
        self.current_index = -1
        await self.header.focus()

    async def handle_system_name_on_change(self, message: Message) -> None:
        self.log(f"System Name Field Contains: {message.sender.value}")

    async def handle_address_on_change(self, message: Message) -> None:
        self.log(f"Address Field Contains: {message.sender.value}")

    async def handle_port_on_change(self, message: Message) -> None:
        self.log(f"Port Field Contains: {message.sender.value}")

    async def handle_input_on_focus(self, message: Message) -> None:
        self.current_index = self.tab_index.index(message.sender.name)


def run_tui():
    TuiApp.run()
