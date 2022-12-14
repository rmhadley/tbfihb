from __future__ import annotations

import os

import color
import render_functions
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union
from components.crafting import CraftingTrees

import tcod.event
import numpy as np  # type: ignore
import tcod

import actions
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction,
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent

class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state

        quest_complete = False
        # Check if we're on a quest and if the quest is complete
        if self.engine.quest != None:
            if self.engine.quest.quest_type == "catch":
                caught = 0
                for fish in self.engine.caught:
                    if fish.name == self.engine.quest.quest_target:
                        caught += 1
                if caught >= self.engine.quest.quest_count:
                    quest_complete = True

        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            elif self.engine.npc:
                return NPCEventHandler(self.engine, self.engine.npc)
            elif self.engine.player.skills.hooked != None:
                return SkillActivateHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.

        if quest_complete:
            quest_complete = False
            return QuestCompleteEventHandler(self.engine)

        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False
 
        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

class MainGameEventHandler(EventHandler):
    def on_render(self, console: tcod.Consle) -> None:
        super().on_render(console)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        mod = event.mod

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif (key == tcod.event.K_PERIOD) and (mod & tcod.event.Modifier.SHIFT):
            return actions.DownStairsAction(player)
        elif (key == tcod.event.K_COMMA) and (mod & tcod.event.Modifier.SHIFT):
            return actions.UpStairsAction(player)
        elif (key == tcod.event.K_s) and (mod & tcod.event.Modifier.SHIFT):
            raise SystemExit()
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_a:
            return SkillActivateHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)
        elif key == tcod.event.K_p:
            return PartsEventHandler(self.engine)
        elif key == tcod.event.K_q:
            return QuestScreenEventHandler(self.engine)

        return action

class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "???Message history???", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None

class GameWinHandler(HistoryViewer):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.engine.message_log.add_message("You won! You killed the dragon, woo.", color.impossible)

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()

class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)

class SkillEventHandler(AskUserEventHandler):
    """This handler lets the user select a skill.

    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        number_of_abilities = len(self.engine.player.skills.known)

        height = number_of_abilities + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0
        width = len(self.TITLE) + 10

        if self.engine.player.skills.hooked != None:
            fish = self.engine.player.skills.hooked
            y = y + 5

            console.draw_frame(
                x=x,
                y=0,
                width=width,
                height=5,
                title="Hooked Fish",
                clear=True,
                fg=(255, 255, 255),
                bg=(0, 0, 0),
            )

            console.print(x + 1, 1, f"Fish: {fish.name}", fg=color.white)

            fish_strength = 100 - fish.fighter.fatigue

            render_functions.render_bar(
                console=console,
                current_value=fish_strength,
                maximum_value=100,
                total_width=20,
                text="Strength",
                color_filled=color.hp_bar_filled,
                color_empty=color.hp_bar_empty,
                x=x + 1,
                y=2,
            )

            render_functions.render_bar(
                console=console,
                current_value=fish.fighter.hooked,
                maximum_value=100,
                total_width=20,
                text="Hook",
                color_filled=color.hp_bar_filled,
                color_empty=color.hp_bar_empty,
                x=x + 1,
                y=3,
            )

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_abilities > 0:
            for i, skill in enumerate(self.engine.player.skills.known):
                skill_key = chr(ord("a") + i)

                skill_string = f"({skill_key}) {skill.name} - {skill.level}"
                fg_color = color.white

                console.print(x + 1, y + i + 1, skill_string, fg=fg_color)
        else:
            console.print(x + 1, y + 1, "(None)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_skill = player.skills.known[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_ability_selected(selected_skill)
        return super().ev_keydown(event)

    def on_ability_selected(self, ability: Enchant) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid ability."""
        raise NotImplementedError()

class SkillActivateHandler(SkillEventHandler):
    """Handle using an ability."""

    TITLE = "Select an ability to use"

    def on_ability_selected(self, ability: Enchant) -> Optional[ActionOrHandler]:
        """Return the action for the selected ability."""
        return ability.get_action(self.engine.player)

class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)

class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

class BeamRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback
        self.player = self.engine.player
        self.beem_path = []

        closest = 200
        # let's find the closest enemy and default to them
        for entity in set(self.engine.game_map.actors) - {self.player}:
          if self.engine.game_map.visible[entity.x, entity.y]:
            dx = entity.x - self.player.x
            dy = entity.y - self.player.y
            distance = max(abs(dx), abs(dy))
            if distance < closest:
                closest = distance
                self.engine.mouse_location = entity.x, entity.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location

        if self.player.gamemap.visible[x, y]:
            cost = np.array(self.player.gamemap.tiles["walkable"], dtype=np.int8)
            graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)

            pathfinder.add_root((self.player.x, self.player.y))  # Start position.

            # Compute the path to the destination and remove the starting point.
            path: List[List[int]] = pathfinder.path_to((x, y))[1:].tolist()

            # Convert from List[List[int]] to List[Tuple[int, int]].
            path = [(index[0], index[1]) for index in path]
            for xy in path:
                console.tiles_rgb["bg"][xy[0], xy[1]] = color.white
                console.tiles_rgb["fg"][xy[0], xy[1]] = color.black

            self.beem_path = path

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback(self.beem_path)

class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

class AreaMeleeAttackHandler(SelectIndexHandler):
    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback
        self.target_area = []

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        center_x = self.engine.player.x
        center_y = self.engine.player.y
        start_x = center_x - self.radius
        stop_x = center_x + self.radius
        start_y = center_y - self.radius
        stop_y = center_y + self.radius

        for x in range(start_x, stop_x + 1):
            for y in range(start_y, stop_y + 1):
                console.tiles_rgb["bg"][x, y] = color.white
                console.tiles_rgb["fg"][x, y] = color.black
                self.target_area.append([x, y])

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback(self.target_area)

class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=40,
            height=10,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x + 1,
            y=4,
            string=f"a) Strength (+1 STR, from {self.engine.player.fighter.strength})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Intelligence (+1 INT, from {self.engine.player.fighter.intelligence})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Dexterity (+1 DEX, from {self.engine.player.fighter.dexterity})",
        )
        console.print(
            x=x + 1,
            y=7,
            string=f"d) Constitution (+1 CON, from {self.engine.player.fighter.constitution})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 3:
            if index == 0:
                player.level.increase_str()
            elif index == 1:
                player.level.increase_int()
            elif index == 2:
                player.level.increase_dex()
            elif index == 3:
                player.level.increase_con()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None

class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 8

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=10,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1, y=y + 5, string=f"Defense: {self.engine.player.fighter.defense}"
        )
        console.print(
            x=x +1, y=y + 6, string=f"Attack: {self.engine.player.equipment.min_damage}-{self.engine.player.equipment.max_damage}"
        )

        console.print(
            x=x +1, y=y + 8, string=f"STR: {self.engine.player.fighter.strength} INT:{self.engine.player.fighter.intelligence} DEX:{self.engine.player.fighter.dexterity} CON:{self.engine.player.fighter.constitution}"
        )

class NPCEventHandler(AskUserEventHandler):
    def __init__(self, engine: Engine, npc: Entity):
        super().__init__(engine)
        self.npc = npc
        self.TITLE = self.npc.name

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = 40

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=12,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=self.npc.HELLO
        )

        i = 0
        if len(self.npc.quests) > 0:
            for i, quest in enumerate(self.npc.quests):
                quest_key = chr(ord("a") + i)

                quest_string = f"({quest_key}) {quest.name}"
                fg_color = color.white

                console.print(x + 1, y + i + 3, quest_string, fg=fg_color)
        elif self.npc.menu != None:
            for i, option in enumerate(self.npc.menu.options):
                option_key = chr(ord("a") + i)

                option_string = f"({option_key}) {option.text}"
                fg_color = color.white

                console.print(x + 1, y + i + 3, option_string, fg=fg_color)

        quest_key = chr(ord("a") + i + 1)
        console.print(x + 1, y + i + 4, f"({quest_key}) No thanks")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        self.engine.npc = None

        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            if len(self.npc.quests) > 0:
                try:
                    self.engine.quest = self.npc.quests[index]
                    self.engine.message_log.add_message("Quest accepted.")
                    return super().ev_keydown(event)
                except IndexError:
                    if index == len(self.npc.quests):
                        return super().ev_keydown(event)
                    else:
                        self.engine.message_log.add_message("Invalid entry.", color.invalid)
                        return None
            elif self.npc.menu != None:
                try:
                    return self.npc.menu.options[index].action(self.engine)
                except IndexError:
                    if index == len(self.npc.menu.options):
                        return super().ev_keydown(event)
                    else:
                        self.engine.message_log.add_message("Invalid entry.", color.invalid)
                        return None

class QuestScreenEventHandler(AskUserEventHandler):
    TITLE = "Quest"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 35

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=11,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if self.engine.quest == None:
            console.print(
                x=x + 1, y=y + 1, string=f"No Quest Accepted.\n\nTalk to people in town."
            )
        else:
            quest = self.engine.quest
            if not quest.embarked:
                console.print(
                    x=x + 1, y=y + 1, string=f"{quest.name}\n{quest.description}\n\nMap: {quest.quest_map}\nGoal: {quest.quest_type} {quest.quest_count} {quest.quest_target}\n\n(a): Embark\n(b): Not ready"
                )
            else:
                progress = ""
                if quest.quest_type == "catch":
                    caught = 0
                    for fish in self.engine.caught:
                        if fish.name == quest.quest_target:
                            caught += 1
                    progress = f"\nProgress: {caught}/{quest.quest_count}"

                console.print(
                    x=x + 1, y=y + 1, string=f"{quest.name}\n{quest.description}\n\nMap: {quest.quest_map}\nGoal: {quest.quest_type} {quest.quest_count} {quest.quest_target}{progress}\n\n(a): Abandon\n(b): Continue"
                )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if self.engine.quest == None:
            return super().ev_keydown(event)

        key = event.sym
        index = key - tcod.event.K_a

        if not self.engine.quest.embarked:
            if index == 0:
                return actions.EmbarkAction(self.engine.player)
                return super().ev_keydown(event)
            elif index == 1 or key == tcod.event.K_ESCAPE:
                return super().ev_keydown(event)
            else:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
        else:
            if index == 0:
                return actions.ReturnAction(self.engine.player)
            elif index == 1 or key == tcod.event.K_ESCAPE:
                return super().ev_keydown(event)
            else:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None

class QuestCompleteEventHandler(AskUserEventHandler):
    TITLE = "Quest Complete!"
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.loot = []

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 30
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 35

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=11,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        quest = self.engine.quest
        progress = f"\nProgress: {quest.quest_count}/{quest.quest_count}"

        console.print(
            x=x + 1, y=y + 1, string=f"{quest.name}\n{quest.description}\n\nMap: {quest.quest_map}\nGoal: {quest.quest_type} {quest.quest_count} {quest.quest_target}{progress}\n\n(a): Return"
        )

        if len(self.loot) == 0:
            for fish in self.engine.caught:
                self.loot.extend(fish.inventory.get_loot())

        unique_parts = []
        for part in self.loot:
            if part not in unique_parts:
                unique_parts.append(part)
        unique_parts.sort()

        number_parts = len(unique_parts)
        height = number_parts + 2

        y = y + 11

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title="Loot",
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_parts > 0:
            for i, part in enumerate(unique_parts):
                count = self.loot.count(part)
                part_string = f"{count} {part}"

                console.print(x + 1, y + i + 1, part_string, fg=color.white)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if index == 0:
            self.engine.caught = []
            self.engine.parts.extend(self.loot)
            return actions.ReturnAction(self.engine.player)
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class PartsEventHandler(AskUserEventHandler):
    TITLE = "Parts Inventory"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        unique_parts = []
        for part in self.engine.parts:
            if part not in unique_parts:
                unique_parts.append(part)
        unique_parts.sort()

        number_parts = len(unique_parts)

        height = number_parts + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 10

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_parts > 0:
            for i, part in enumerate(unique_parts):
                count = self.engine.parts.count(part)
                part_string = f"{count} {part}"

                console.print(x + 1, y + i + 1, part_string, fg=color.white)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_ESCAPE:
            return super().ev_keydown(event)
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class MyEquipmentEventHandler(AskUserEventHandler):
    TITLE = "My Equipment"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        equipment = self.engine.player.equipment
        number_slots = len(equipment.slots)
        height = number_slots + 2

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = 40

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        for i, slot in enumerate(equipment.slots):
            item = getattr(equipment, slot)
            if item != None:
                console.print(x + 1, y + 1 + i, f"{slot}: {item.name}")
            else:
                console.print(x + 1, y + 1 + i, f"{slot}: None")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_ESCAPE:
            return super().ev_keydown(event)
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class ChangeEquipmentEventHandler(AskUserEventHandler):
    TITLE = "Change Equipment"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        equipment = self.engine.player.equipment

        number_slots = len(equipment.slots)

        height = number_slots + 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = 20

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        for i, slot in enumerate(equipment.slots):
            key = chr(ord("a") + i)
            menu_string = f"({key}) {slot}"

            console.print(x + 1, y + i + 1, menu_string, fg=color.white)

        key = chr(ord("a") + i + 1)
        i += 1
        console.print(x + 1, y + i + 1, f"({key}) Exit")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_ESCAPE:
            return super().ev_keydown(event)

        equipment = self.engine.player.equipment
        if 0 <= index <= 26:
            try:
                return EquipSlotEventHandler(self.engine, equipment.slots[index])
            except IndexError:
                if index == len(equipment.slots):
                    return super().ev_keydown(event)
                else:
                    self.engine.message_log.add_message("Invalid entry.", color.invalid)
                    return None
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class EquipSlotEventHandler(AskUserEventHandler):
    def __init__(self, engine: Engine, slot: str):
        super().__init__(engine)
        self.slot = slot
        self.TITLE = f"Equip {slot}"
        self.items = []
        for item in self.engine.stash:
            if item.slot == self.slot:
                self.items.append(item)
        self.number_items = len(self.items)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        height = self.number_items + 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = 40

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        equipped_item = getattr(self.engine.player.equipment, self.slot)

        if self.number_items > 0:
            for i, item in enumerate(self.items):
                key = chr(ord("a") + i)
                menu_string = f"({key}) {item.name}"

                fg_color = color.white

                if type(equipped_item) == type(item):
                    menu_string += " (E)"
                    fg_color = (255, 0, 0)

                console.print(x + 1, y + i + 1, menu_string, fg=fg_color)

            key = chr(ord("a") + i + 1)
            i += 1
            console.print(x + 1, y + i + 1, f"({key}) Exit")
        else:
            console.print(x + 1, y + 1, f"(a) Exit")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_ESCAPE:
            return super().ev_keydown(event)

        if 0 <= index <= 26:
            try:
                self.engine.player.equipment.equip(self.slot, self.items[index])
                return None
            except IndexError:
                if index == self.number_items:
                    return super().ev_keydown(event)
                else:
                    self.engine.message_log.add_message("Invalid entry.", color.invalid)
                    return None
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class CraftEquipmentEventHandler(AskUserEventHandler):
    def __init__(self, engine: Engine, slot: str):
        super().__init__(engine)
        self.slot = slot
        self.TITLE = f"{slot} Trees"
        self.number_options = len(CraftingTrees)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        height = self.number_options + 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = 40

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        for i, tree in enumerate(CraftingTrees):
            if tree.visible:
                key = chr(ord("a") + i)
                menu_string = f"({key}) {tree.name}"

                fg_color = color.white

                console.print(x + 1, y + i + 1, menu_string, fg=fg_color)

        key = chr(ord("a") + i + 1)
        i += 1
        console.print(x + 1, y + i + 1, f"({key}) Exit")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_ESCAPE:
            return super().ev_keydown(event)

        if 0 <= index <= 26:
            try:
                return CraftTreeEventHandler(self.engine, self.slot, CraftingTrees[index])
            except IndexError:
                if index == self.number_options:
                    return super().ev_keydown(event)
                else:
                    self.engine.message_log.add_message("Invalid entry.", color.invalid)
                    return None
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class CraftRodsEventHandler(CraftEquipmentEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, slot="Rod")

class CraftHatsEventHandler(CraftEquipmentEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, slot="Hat")

class CraftVestsEventHandler(CraftEquipmentEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, slot="Vest")

class CraftPantsEventHandler(CraftEquipmentEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, slot="Pants")

class CraftBootsEventHandler(CraftEquipmentEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, slot="Boots")

class CraftGlovesEventHandler(CraftEquipmentEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, slot="Gloves")

class CraftTreeEventHandler(AskUserEventHandler):
    def __init__(self, engine: Engine, slot: str, tree: str):
        super().__init__(engine)
        self.slot = slot
        self.tree = tree
        self.TITLE = f"{tree.name} {slot} Tree"

        self.options = getattr(self.tree, self.slot)
        self.number_options = len(self.options)

        self.parts = {}
        unique_parts = []
        for part in self.engine.parts:
            if part not in unique_parts:
                unique_parts.append(part)
        unique_parts.sort()

        if len(unique_parts) > 0:
            for i, part in enumerate(unique_parts):
                count = self.engine.parts.count(part)
                self.parts[part] = count

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        height = self.number_options + 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = 40

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        for i, item in self.options.items():
            key = chr(ord("a") + i)
            menu_string = f"({key}) {item.name}"

            fg_color = (66, 66, 66)
            if item.can_craft(self.parts):
                fg_color = color.white

            console.print(x + 1, y + i + 1, menu_string, fg=fg_color)

        key = chr(ord("a") + i + 1)
        i += 1
        console.print(x + 1, y + i + 1, f"({key}) Exit")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_ESCAPE:
            return super().ev_keydown(event)

        if 0 <= index <= 26:
            try:
                return CraftDetailsEventHandler(self, self.options[index], self.parts)
            except KeyError:
                if index == self.number_options:
                    return super().ev_keydown(event)
                else:
                    self.engine.message_log.add_message("Invalid entry.", color.invalid)
                    return None
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

class CraftDetailsEventHandler(AskUserEventHandler):
    def __init__(self, parent_handler: BaseEventHandler, item: Equippable, parts: {}):
        self.engine = parent_handler.engine
        self.parent = parent_handler
        self.item = item
        self.parts = parts

    def on_render(self, console: tcod.Console) -> None:
        self.parent.on_render(console)

        height = 20
        x = 20
        y = 10
        width = 40
        title = f"Craft {self.item.name}"

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=title,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x + 1, y + 1, self.item.crafting_description(self.parts))

        option_text = ""
        if self.item.can_craft(self.parts):
            option_text = "(C)raft - "

        console.print(x + 1, y + 19, f"{option_text}(B)ack")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        mod = event.mod

        if key == tcod.event.K_b:
            return self.parent
        elif key == tcod.event.K_c and self.item.can_craft(self.parts):
            self.item.craft(self.engine.parts, self.engine.stash)
            return super().ev_keydown(event)

        self.engine.message_log.add_message("Invalid entry.", color.invalid)
        return None
