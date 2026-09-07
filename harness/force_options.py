"""Resolve optional impact cues consistently for game cards and ROM revisions."""
from graphics_options import GAMES, family


def card_rom(card, world_rom="crusnwld24"):
    return world_rom if card == "crusnwld" else card


def apply_game_defaults(environment, rom):
    """Apply Exotica's steering correction and output trim without editing preferences."""
    if rom != 'crusnexo':
        return
    # The DIP controls motor/shifter polarity. Mirroring ADC input as well
    # reverses vehicle steering; retain only an explicit diagnostic override.
    environment.setdefault('MIDZ_WHEEL_INVERT', '0')
    if environment.get('MIDV_FFB') == '1':
        requested=max(0,min(100,int(environment.get('MIDV_FFB_STRENGTH','100'))))
        environment['MIDV_FFB_REQUESTED_STRENGTH']=str(requested)
        environment['MIDV_FFB_STRENGTH']=str((requested*80+50)//100)


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
