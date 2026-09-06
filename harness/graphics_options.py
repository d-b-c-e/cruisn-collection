"""Per-game graphics experiments shared by the shell and every launch path."""
from pathlib import Path

from game_patch import combine_patches

GAMES = ("crusnusa", "crusnwld", "offroadc", "crusnexo")
OPTIONS = ("seam_alignment", "terrain_visibility", "scenery_distance", "detail_distance", "far_distance")
PATCHES = {
    "terrain_visibility": "crusnwld-terrain-visibility-experimental.txt",
    "detail_distance": "crusnusa-lod-experiment.txt",
    "far_distance": "crusnusa-farplane-experiment.txt",
}


def family(rom):
    return next((game for game in GAMES if rom.startswith(game)), rom)


def supported(rom, option):
    if option == "scenery_distance":
        return rom == "crusnwld24"
    if option == "terrain_visibility":
        return rom in ("crusnwld", "crusnwld24")
    if option == "seam_alignment":
        return family(rom) in GAMES[:3]
    # These instruction addresses are verified only for USA v4.5, not its clones.
    return option in ("detail_distance", "far_distance") and rom == "crusnusa"


def for_game(section, rom):
    return {option: supported(rom, option) and
            str(section.get(f"{option}_{family(rom)}", "0")).strip() == "1"
            for option in OPTIONS}


def load(section):
    # Store the family preference even when another revision is selected; the
    # actual revision is checked separately by both menu and launch resolution.
    return {game: for_game(section, "crusnwld24" if game == "crusnwld" else game) for game in GAMES}


def serialize(options):
    return {f"{option}_{game}": "1" if options.get(game, {}).get(option, False) else "0"
            for game in GAMES for option in OPTIONS
            if supported("crusnwld24" if game == "crusnwld" else game, option)}


def toggle(options, game, option, rom=None):
    if not supported(rom or game, option):
        return False
    settings = options.setdefault(game, {})
    settings[option] = not settings.get(option, False)
    return True


def rows(game, options, rom=None):
    selected = options.get(game, {})
    descriptions = (
        ("seam_alignment", "SEAM ALIGNMENT",
         "EXPERIMENTAL: CLOSES SOME TERRAIN SEAMS; MAY SHIFT TEXTURES. NEXT LAUNCH."),
        ("terrain_visibility", "WIDESCREEN TERRAIN",
         "RESTORES SOME MISSING EDGE TERRAIN; DOES NOT EXTEND DRAW DISTANCE. NEXT LAUNCH."),
        ("scenery_distance", "DISTANT SCENERY",
         "EXPERIMENTAL: DRAWS VERIFIED GERMANY MOUNTAINS AND TREES EARLIER. NEXT LAUNCH."),
        ("detail_distance", "DETAIL DISTANCE",
         "EXPERIMENTAL: KEEPS DETAILED MODELS FARTHER AWAY; MORE RENDERING WORK. NEXT LAUNCH."),
        ("far_distance", "DRAW LIMIT",
         "EXPERIMENTAL: HIGHER DRAW LIMIT; NO VISIBLE GAIN IN THE TESTED SCENE. NEXT LAUNCH."),
    )
    result = []
    for option, label, hint in descriptions:
        if not supported(rom or game, option):
            value = "UNAVAILABLE"
            hint = ("AVAILABLE FOR WORLD 2.4; TESTED ON GERMANY. USE WIDESCREEN AND SCALE 2X OR HIGHER."
                    if option == "scenery_distance" else "AVAILABLE FOR USA, WORLD AND OFF ROAD." if option == "seam_alignment"
                    else "AVAILABLE FOR CRUIS'N WORLD ONLY." if option == "terrain_visibility"
                    else "AVAILABLE FOR CRUIS'N USA ONLY.")
        else:
            value = (("ON" if selected.get(option) else "OFF") if option in ("seam_alignment", "terrain_visibility", "scenery_distance")
                     else ("EXTENDED" if selected.get(option) else "STANDARD"))
        result.append((option, label, value, hint))
    return result


def launch_overrides(root, rig, rom, margin, scale, section, environment):
    """Resolve settings without launching hardware; compose guarded patches atomically.

    An explicit MIDV_PATCH replaces the configured patch group, as before.
    Old marginfill INI values are deliberately not read. The legacy shader
    experiment remains available only through an explicit developer environment.
    """
    root, rig = Path(root), Path(rig)
    selected = for_game(section, rom)
    env = {"MIDV_GL_TJUNCTIONS": environment.get("MIDV_GL_TJUNCTIONS",
           "1" if selected["seam_alignment"] and scale > 1 else "0")}
    env["MIDV_SCENERY"] = environment.get("MIDV_SCENERY",
        "all" if selected["scenery_distance"] and margin >= 80 and scale > 1 else "off")
    if "MIDV_PATCH" in environment:
        return env
    paths = []
    widescreen = root / "patch" / "game" / f"{rom}-widescreen.txt"
    if margin >= 80 and widescreen.is_file():
        paths.append(widescreen)
    for option, filename in PATCHES.items():
        if selected[option] and (option != "terrain_visibility" or margin >= 80):
            path = root / "patch" / "game" / filename
            if not path.is_file():
                raise FileNotFoundError(f"Selected graphics experiment is missing: {path}")
            paths.append(path)
    custom = str(section.get(f"gamepatch_{family(rom)}", "")).strip()
    if custom:
        path = root / custom
        if not path.is_file():
            raise FileNotFoundError(f"Configured game patch is missing: {path}")
        if path not in paths:
            paths.append(path)
    if paths:
        env["MIDV_PATCH"] = (str(paths[0]) if len(paths) == 1 else
                             combine_patches(paths, rig / f"gamepatch-{rom}.txt"))
    return env
