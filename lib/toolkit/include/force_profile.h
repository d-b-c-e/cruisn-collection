// force_profile.h - reads the versioned force-feedback profiles (C++11).
//
// The C++ counterpart of Dbce.Wheel.Ffb.ForceProfile, parsing the same
// profiles/force-profiles.ini. A conformance test loads every shipped profile
// through both readers and requires identical settings, so the two cannot
// drift; if you add a key here you must add it there.
//
//   dbce::force::Profile p;
//   std::string why;
//   if (!dbce::force::load_profile_dir(gameFolder, "arcade-outrun@1", p, &why))
//       log("force profile: %s - using built-in defaults", why.c_str());
//
// load_profile_dir reads force-profiles.ini and then force-profiles.user.ini
// from the same folder, so a player's own tunes survive an update of the mod
// and a profile of the same id in the user file wins outright.
//
// A profile that fails to load must NOT disable force feedback: fall back to
// the built-in defaults and say so in the log. A tuning file is the last thing
// that should be able to break a game.
#pragma once
#include "force_model.h"

#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <cctype>

namespace dbce { namespace force {

struct Profile {
    std::string name;          // "arcade-outrun"
    int         version;       // 1
    std::string description;
    ModelSettings  model;
    ShaperSettings shaper;
    std::vector<std::string> unknown_keys;   // reported, never silently dropped

    Profile() : version(0) {}
    std::string id() const {
        std::ostringstream o; o << name << '@' << version; return o.str();
    }
};

namespace detail {

inline std::string trim(const std::string& s) {
    size_t a = 0, b = s.size();
    while (a < b && std::isspace((unsigned char)s[a])) ++a;
    while (b > a && std::isspace((unsigned char)s[b - 1])) --b;
    return s.substr(a, b - a);
}

// Strips a trailing # or ; comment, then whitespace.
inline std::string strip(const std::string& line) {
    size_t cut = line.find_first_of("#;");
    return trim(cut == std::string::npos ? line : line.substr(0, cut));
}

inline bool is_section(const std::string& t, std::string& id) {
    if (t.size() > 2 && t[0] == '[' && t[t.size() - 1] == ']') {
        id = trim(t.substr(1, t.size() - 2));
        return true;
    }
    return false;
}

inline bool iequals(const std::string& a, const std::string& b) {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i)
        if (std::tolower((unsigned char)a[i]) != std::tolower((unsigned char)b[i])) return false;
    return true;
}

inline float to_f(const std::string& v) { return (float)std::atof(v.c_str()); }
inline bool to_b(const std::string& v) {
    std::string t = trim(v);
    return iequals(t, "true") || t == "1" || iequals(t, "yes");
}

// The vocabulary. Keep in step with ForceProfile.KeyNames.
inline bool set_key(Profile& p, const std::string& key, const std::string& value) {
    ModelSettings&  m = p.model;
    ShaperSettings& s = p.shaper;
    if (key == "model.spring.strength")        { m.spring_strength = to_f(value); return true; }
    if (key == "model.spring.fullSpeedMps")    { m.spring_full_speed_mps = to_f(value); return true; }
    if (key == "model.damper.strength")        { m.damper_strength = to_f(value); return true; }
    if (key == "model.damper.staticFraction")  { m.damper_static_fraction = to_f(value); return true; }
    if (key == "model.lateral.weight")         { m.lateral_weight = to_f(value); return true; }
    if (key == "model.lateral.forceReference") { m.lateral_force_reference = to_f(value); return true; }
    if (key == "model.lateral.gReference")     { m.lateral_g_reference = to_f(value); return true; }
    if (key == "model.lateral.trailFloor")     { m.trail_floor = to_f(value); return true; }
    if (key == "model.lateral.trailSlipSpan")  { m.trail_slip_span = to_f(value); return true; }
    if (key == "model.lateral.gripLoss")       { m.grip_loss = to_f(value); return true; }
    if (key == "model.load.weightTransfer")    { m.weight_transfer = to_f(value); return true; }
    if (key == "model.load.transferMin")       { m.weight_transfer_min = to_f(value); return true; }
    if (key == "model.load.transferMax")       { m.weight_transfer_max = to_f(value); return true; }
    if (key == "model.texture.strength")       { m.texture_strength = to_f(value); return true; }
    if (key == "model.texture.hz")             { m.texture_hz = to_f(value); return true; }
    if (key == "model.impact.strength")        { m.impact_strength = to_f(value); return true; }
    if (key == "model.impact.seconds")         { m.impact_seconds = to_f(value); return true; }
    if (key == "model.shift.strength")         { m.shift_strength = to_f(value); return true; }
    if (key == "model.shift.seconds")          { m.shift_seconds = to_f(value); return true; }
    if (key == "shaper.strength")              { s.strength = (int)(to_f(value) + 0.5f); return true; }
    if (key == "shaper.invert")                { s.invert = to_b(value); return true; }
    if (key == "shaper.deadzone")              { s.deadzone = to_f(value); return true; }
    if (key == "shaper.attackSmoothing")       { s.attack_smoothing = to_f(value); return true; }
    if (key == "shaper.decaySmoothing")        { s.decay_smoothing = to_f(value); return true; }
    if (key == "shaper.softSaturation")        { s.soft_saturation = to_f(value); return true; }
    if (key == "shaper.slewPerSecond")         { s.slew_per_second = to_f(value); return true; }
    if (key == "shaper.outputDeadband")        { s.output_deadband = to_f(value); return true; }
    if (key == "shaper.fadeStartKmh")          { s.fade_start_kmh = to_f(value); return true; }
    if (key == "shaper.fadeFullKmh")           { s.fade_full_kmh = to_f(value); return true; }
    if (key == "shaper.rampSeconds")           { s.ramp_seconds = to_f(value); return true; }
    if (key == "shaper.peakLimit")             { s.peak_limit = to_f(value); return true; }
    if (key == "shaper.smoothingMs")           { s.smoothing_ms = to_f(value); return true; }
    if (key == "shaper.impulseBypass")         { s.impulse_bypass = to_f(value); return true; }
    if (key == "shaper.settleBelow")           { s.settle_below = to_f(value); return true; }
    if (key == "shaper.releveling")            { s.releveling = to_f(value); return true; }
    return false;
}

// Body of the LAST section with this id, so a user file appended to the shipped
// one overrides it. Returns false when the id is absent.
inline bool section_body(const std::string& text, const std::string& id, std::vector<std::string>& out) {
    std::istringstream in(text);
    std::string line, here;
    std::vector<std::string> found, body;
    bool collecting = false, any = false;
    while (std::getline(in, line)) {
        std::string t = strip(line);
        if (is_section(t, here)) {
            if (collecting) { found = body; any = true; }
            body.clear();
            collecting = iequals(here, id);
            continue;
        }
        if (collecting) body.push_back(line);
    }
    if (collecting) { out = body; return true; }
    if (any) { out = found; return true; }
    return false;
}

inline bool apply_section(const std::string& text, const std::string& id,
                          Profile& into, std::vector<std::string>& seen, std::string* why) {
    for (size_t i = 0; i < seen.size(); ++i)
        if (iequals(seen[i], id)) { if (why) *why = "profile inherits itself: " + id; return false; }
    seen.push_back(id);

    std::vector<std::string> body;
    if (!section_body(text, id, body)) { if (why) *why = "no such profile: " + id; return false; }

    // Resolve the parent before our own keys, so ours win.
    std::string parent, description;
    std::vector<std::pair<std::string, std::string> > pairs;
    for (size_t i = 0; i < body.size(); ++i) {
        std::string t = strip(body[i]);
        if (t.empty()) continue;
        size_t eq = t.find('=');
        if (eq == std::string::npos || eq == 0) continue;
        std::string key = trim(t.substr(0, eq)), val = trim(t.substr(eq + 1));
        if (iequals(key, "inherits")) { parent = val; continue; }
        if (iequals(key, "description")) { description = val; continue; }
        pairs.push_back(std::make_pair(key, val));
    }

    if (!parent.empty() && !apply_section(text, parent, into, seen, why)) return false;
    if (!description.empty()) into.description = description;
    for (size_t i = 0; i < pairs.size(); ++i) {
        if (!set_key(into, pairs[i].first, pairs[i].second)) {
            bool known = false;
            for (size_t j = 0; j < into.unknown_keys.size(); ++j)
                if (into.unknown_keys[j] == pairs[i].first) { known = true; break; }
            if (!known) into.unknown_keys.push_back(pairs[i].first);
        }
    }
    return true;
}

inline bool read_file(const std::string& path, std::string& out) {
    std::ifstream f(path.c_str(), std::ios::binary);
    if (!f) return false;
    std::ostringstream ss; ss << f.rdbuf(); out = ss.str();
    return true;
}

} // namespace detail

// Every profile id defined in the text, in file order.
inline std::vector<std::string> list_profile_ids(const std::string& text) {
    std::vector<std::string> ids;
    std::istringstream in(text);
    std::string line, id;
    while (std::getline(in, line))
        if (detail::is_section(detail::strip(line), id)) ids.push_back(id);
    return ids;
}

// Parses one profile out of `text`. Returns false with a reason in `why`.
inline bool parse_profile(const std::string& text, const std::string& id, Profile& out, std::string* why = 0) {
    Profile p;
    std::vector<std::string> seen;
    if (!detail::apply_section(text, id, p, seen, why)) return false;

    size_t at = id.rfind('@');
    if (at == std::string::npos || at == 0) { if (why) *why = "profile id must be name@version: " + id; return false; }
    p.name = id.substr(0, at);
    p.version = std::atoi(id.c_str() + at + 1);
    if (p.version <= 0) { if (why) *why = "profile version must be a positive integer: " + id; return false; }
    out = p;
    return true;
}

inline const char* shipped_profile_file() { return "force-profiles.ini"; }
inline const char* user_profile_file()    { return "force-profiles.user.ini"; }

// Reads `id` from force-profiles.ini in `directory`, with
// force-profiles.user.ini layered on top when present.
inline bool load_profile_dir(const std::string& directory, const std::string& id,
                             Profile& out, std::string* why = 0) {
    std::string sep = (!directory.empty() && directory[directory.size() - 1] != '\\' &&
                       directory[directory.size() - 1] != '/') ? "/" : "";
    std::string text, chunk;
    if (detail::read_file(directory + sep + shipped_profile_file(), chunk)) text += chunk + "\n";
    if (detail::read_file(directory + sep + user_profile_file(), chunk))    text += chunk + "\n";
    if (text.empty()) {
        if (why) *why = std::string("no ") + shipped_profile_file() + " in " + directory;
        return false;
    }
    return parse_profile(text, id, out, why);
}

}} // namespace dbce::force
