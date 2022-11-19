import asyncio

from rich.console import RenderableType, Console
from rich.panel import Panel
from textual.app import App
from textual.reactive import Reactive
from textual.widgets import Placeholder

from textual_extensions import Input
from textual_extensions import Logger
from textual_extensions import Widget, ListBox
from textual_extensions import log
# from .cli import CommandLineInterface


class MainApp(App):
    inputbar: Input
    sidebar: 'Sidebar'
    
    # def __init__(self, cli: CommandLineInterface):
    #     super().__init__()
    #     self.cli = cli
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.console = Console(height=40)
    
    async def on_load(self):
        await self.bind('tab,ctrl+i', 'toggle_sidebar')
        await self.bind('enter', 'activate_input')
    
    async def action_activate_input(self):
        await self.inputbar.gain_focus()
    
    async def action_toggle_sidebar(self):
        self.sidebar.toggle()
    
    async def on_mount(self) -> None:
        self.inputbar = Input(
            placeholder='Press ENTER to start searching command, '
                        'support fuzzy search and auto completion.',
            # placeholder='Search command here, support :two_hearts:[magenta]'
            #             'fuzzy search[/] and :star2:[yellow]auto completion[/].'
            show_border=True,
        )
        self.sidebar = Sidebar()
        
        await self.view.dock(
            self.sidebar, edge='left', size=len(self.sidebar), z=1
        )
        
        # await self.view.dock(Logger(), edge='bottom', size=3)
        await self.view.dock(self.inputbar, edge='bottom', size=3)

        await self.view.dock(
            MyListBox('one', 'two', 'three'), edge='left', size=20
        )
        await self.view.dock(Placeholder(), edge='top', size=5)
        await self.view.dock(
            MyPanel(name='arguments'),
            MyPanel(name='options'),
            MyPanel(name='other', border_style='dim'),
            edge='top',
        )

        # await self.inputbar.gain_focus()


class MyPanel(Widget):
    def __init__(self, name: str, border_style: str = 'none'):
        super().__init__(name=name)
        self._border_style = border_style
        
    def render(self) -> RenderableType:
        return Panel(
            '', title=self.name, title_align='left',
            border_style=self._border_style,
        )


class MyListBox(ListBox):
    
    def render(self):
        return Panel(super().render())


class Sidebar(Widget):
    WIDTH = 40
    show_bar = Reactive(False)
    
    def __init__(self):
        super().__init__()
        self.layout_offset_x = -self.WIDTH  # noqa
    
    def __len__(self):
        return self.WIDTH
    
    def toggle(self):
        self.show_bar = not self.show_bar
    
    async def watch_show_bar(self, value: bool):
        self.animate('layout_offset_x', 0 if value else -self.WIDTH)


# async def run_app():
#     app = MainApp(console=Console(height=40))
#     await app.process_messages()

# asyncio.run(run_app())
MainApp.run()
