from components.base_component import BaseComponent

class Quest(BaseComponent):
    def __init__(
            self, name: str,
            description: str,
            quest_map: str,
            quest_type: str,
            quest_target: str,
            quest_count: int,
        ) -> None:
        self.name = name
        self.description = description
        self.quest_map = quest_map
        self.quest_type = quest_type
        self.quest_target = quest_target
        self.quest_count = quest_count
        self.embarked = False

class OceanQuest(Quest):
    def __init__(self) -> None:
        super().__init__(
            name="Ocean Quest",
            description="Stocks running low, help replenish.",
            quest_map="ocean",
            quest_type="catch",
            quest_target="Goldfish",
            quest_count=4,
        )

class CloudsQuest(Quest):
    def __init__(self) -> None:
        super().__init__(
            name="Clouds Quest",
            description="Stocks running low, help replenish.",
            quest_map="clouds",
            quest_type="catch",
            quest_target="Goldfish",
            quest_count=4,
        )
