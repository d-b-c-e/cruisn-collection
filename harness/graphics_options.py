"""Per-game graphics experiments shared by the shell and every launch path."""
from pathlib import Path
import tempfile
from types import SimpleNamespace

from game_patch import combine_patches
import world_distance

GAMES = ("crusnusa", "crusnwld", "offroadc", "crusnexo")
VUNIT_HEIGHT = {'offroadc':401}  # other V-Unit games use 400 native rows
CHOICES = {"world_distance": (0, 2, 3), "world_lookahead": (0, 8, 12)}
DEFAULTS = {"world_distance": 0, "world_lookahead": 8}
OPTIONS = ("seam_alignment", "terrain_visibility", "world_distance", "world_lookahead",
           "scenery_distance", "detail_distance", "far_distance")
PATCHES = {
    "terrain_visibility": "crusnwld-terrain-visibility-experimental.txt",
    "detail_distance": "crusnusa-lod-experiment.txt",
    "far_distance": "crusnusa-farplane-experiment.txt",
}


def family(rom):
    return next((game for game in GAMES if rom.startswith(game)), rom)


def supported(rom, option):
    if option in ("scenery_distance", "world_distance", "world_lookahead"):
        return rom == "crusnwld24"
    if option == "terrain_visibility":
        return rom in ("crusnwld", "crusnwld24")
    if option == "seam_alignment":
        return family(rom) in GAMES[:3]
    # These instruction addresses are verified only for USA v4.5, not its clones.
    return option in ("detail_distance", "far_distance") and rom == "crusnusa"


def for_game(section, rom):
    selected = {}
    for option in OPTIONS:
        raw = str(section.get(f"{option}_{family(rom)}", DEFAULTS.get(option, "0"))).strip()
        if option in CHOICES:
            value = next((v for v in CHOICES[option] if str(v) == raw), DEFAULTS[option])
            selected[option] = value if supported(rom, option) else 0
        else:
            selected[option] = supported(rom, option) and raw == "1"
    if selected["world_distance"]:
        selected["scenery_distance"] = False
    return selected


def load(section):
    # Store the family preference even when another revision is selected; the
    # actual revision is checked separately by both menu and launch resolution.
    return {game: for_game(section, "crusnwld24" if game == "crusnwld" else game) for game in GAMES}


def serialize(options):
    return {f"{option}_{game}": (str(options.get(game, {}).get(option, DEFAULTS[option]))
            if option in CHOICES else "1" if options.get(game, {}).get(option, False) else "0")
            for game in GAMES for option in OPTIONS
            if supported("crusnwld24" if game == "crusnwld" else game, option)}


def toggle(options, game, option, rom=None, direction=1):
    if not supported(rom or game, option):
        return False
    settings = options.setdefault(game, {})
    if option in CHOICES:
        values = CHOICES[option]
        value = settings.get(option, DEFAULTS[option])
        index = values.index(value) if value in values else values.index(DEFAULTS[option])
        settings[option] = values[(index + direction) % len(values)]
    else:
        settings[option] = not settings.get(option, False)
    # These native paths must never run together. The most recent menu choice wins.
    if option == "world_distance" and settings[option]:
        settings["scenery_distance"] = False
    elif option == "scenery_distance" and settings[option]:
        settings["world_distance"] = 0
    return True


def rows(game, options, rom=None):
    selected = options.get(game, {})
    descriptions = (
        ("seam_alignment", "SEAM ALIGNMENT",
         "EXPERIMENTAL: CLOSES SOME TERRAIN SEAMS; MAY SHIFT TEXTURES. NEXT LAUNCH."),
        ("terrain_visibility", "WIDESCREEN TERRAIN",
         "RESTORES SOME MISSING EDGE TERRAIN; DOES NOT EXTEND DRAW DISTANCE. NEXT LAUNCH."),
        ("world_distance", "WORLD DRAW DISTANCE",
         "WORLD 2.4 / WIDESCREEN / SCALE 2X+: REPLACES DISTANT SCENERY. 3X MAY NOT REDUCE POP-IN."),
        ("world_lookahead", "SCENERY LOOKAHEAD",
         "EXTRA TRACK SECTIONS WITH WORLD DRAW DISTANCE. 8 IS THE TRIAL BASELINE; 12 CAN CHANGE GAMEPLAY."),
        ("scenery_distance", "DISTANT SCENERY",
         "OLDER SELECTIVE MOUNTAIN/TREE TRIAL. ENABLING IT TURNS WORLD DRAW DISTANCE OFF."),
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
                    if option in ("scenery_distance", "world_distance", "world_lookahead") else "AVAILABLE FOR USA, WORLD AND OFF ROAD." if option == "seam_alignment"
                    else "AVAILABLE FOR CRUIS'N WORLD ONLY." if option == "terrain_visibility"
                    else "AVAILABLE FOR CRUIS'N USA ONLY.")
        else:
            if option == "world_distance":
                value = f"< {selected[option]}X >" if selected.get(option) else "< OFF >"
            elif option == "world_lookahead":
                value = f"< +{selected.get(option, DEFAULTS[option])} >"
                if not selected.get("world_distance"):
                    hint = "TAKES EFFECT WHEN WORLD DRAW DISTANCE IS 2X OR 3X. DOES NOT AFFECT THE OLDER SCENERY TRIAL."
            else:
                value = (("ON" if selected.get(option) else "OFF") if option in ("seam_alignment", "terrain_visibility", "scenery_distance")
                         else ("EXTENDED" if selected.get(option) else "STANDARD"))
        result.append((option, label, value, hint))
    return result


def launch_overrides(root, rig, rom, margin, scale, section, environment, *, use_saved_distance=True):
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
    if (use_saved_distance and selected["world_distance"] and margin >= 80 and scale > 1
            and "MIDV_WORLD_FAR" not in environment):
        trial = world_distance.configure(SimpleNamespace(
            world_far=80000 * selected["world_distance"],
            world_lead=selected["world_lookahead"], world_cpu=100), rom, env)
        # compose() protects immutable diagnostic evidence. Generate a fresh
        # temporary patch, then atomically replace the launcher's reusable copy.
        rig.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="world-distance-", dir=rig) as directory:
            patch = world_distance.compose(env.get("MIDV_PATCH"),
                Path(directory) / "global-distance.txt", trial["far"])
            destination = rig / f"gamepatch-{rom}-distance.txt"
            patch.replace(destination)
        env["MIDV_PATCH"] = str(destination)
    return env
