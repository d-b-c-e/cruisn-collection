"""Resolve optional impact cues consistently for game cards and ROM revisions."""
from graphics_options import GAMES, family


def card_rom(card, world_rom="crusnwld24"):
    return world_rom if card == "crusnwld" else card


def impact_enabled(get, rom):
    # An explicit revision override (including OFF) wins over the family/global.
    for key in dict.fromkeys((f"ffb_impact_{rom}", f"ffb_impact_{family(rom)}", "ffb_impact")):
        value = str(get(key, "")).strip()
        if value:
            return value == "1"
    return False


def load(section, world_rom="crusnwld24"):
    return {card: impact_enabled(section.get, card_rom(card, world_rom)) for card in GAMES}


def serialize(selected, world_rom="crusnwld24"):
    return {f"ffb_impact_{card_rom(card, world_rom)}": "1" if selected[card] else "0"
            for card in GAMES if card in selected}
