from components.base_component import BaseComponent
from input_handlers import ActionOrHandler, MyEquipmentEventHandler, ChangeEquipmentEventHandler

class Menu(BaseComponent):
    def __init__(
            self,
            name: str,
            options: [],
        ) -> None:
        self.name = name
        self.options = options

class MenuOption(BaseComponent):
    def __init__(
            self,
            text: str,
            action: ActionOrHandler,
        ) -> None:
        self.text = text
        self.action = action

class StashMenu(Menu):
    def __init__(self) -> None:
        super().__init__(
            name="Stash",
            options=[
                MenuOption("My Equipment", MyEquipmentEventHandler),
                MenuOption("Change Equipment", ChangeEquipmentEventHandler),
            ]
        )
