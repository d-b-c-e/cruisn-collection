// Versioned scalar provenance, independent of any outbound packet layout.
#pragma once
#include <cmath>
#include <cstdint>
namespace dbce { namespace telemetry {
enum class Source : uint8_t { unavailable = 0, hud_ocr = 1, numeric_hud = 2, game_memory = 3, derived = 4 };
enum class Quality : uint8_t { invalid = 0, fresh = 1, held = 2 };
enum class Unit : uint8_t { unknown = 0, metres_per_second = 1, rpm = 2, normalized_force = 3, radians = 4 };
struct SignalSample {
    static constexpr unsigned schema = 1;
    double value = 0, seconds = 0;
    uint64_t frame = 0;
    Source source = Source::unavailable;
    Quality quality = Quality::invalid;
    Unit unit = Unit::unknown;
    bool usable(double now, double max_age) const {
        return (quality == Quality::fresh || quality == Quality::held) &&
            source >= Source::hud_ocr && source <= Source::derived &&
            unit >= Unit::metres_per_second && unit <= Unit::radians &&
            std::isfinite(value) && std::isfinite(seconds) && seconds >= 0 &&
            std::isfinite(now) && now >= seconds && std::isfinite(max_age) &&
            max_age >= 0 && now - seconds <= max_age;
    }
};
}}
