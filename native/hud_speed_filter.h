// Cruis'n OCR hold policy. Source: cruisn-collection/native/hud_speed_filter.h.
// Copied into the MAME patch by harness/sync_native.py; do not edit that copy.
#pragma once
#include <cstdlib>

namespace cruisn {
class HudSpeedFilter {
public:
    int value = 0, raw = -1, missing = 0, age_frames = 0;
    bool has_value = false, fresh = false;

    void reset() { value = 0; raw = -1; missing = age_frames = 0;
                   pending_ = -1; has_value = fresh = false; }

    int observe(int mph) {
        raw = mph; fresh = false;
        if (age_frames < 1000000) ++age_frames;
        if (mph >= 0 && mph < 400) {
            missing = 0; // expiration requires CONSECUTIVE misses
            if (std::abs(mph - value) <= 25 ||
                (pending_ >= 0 && std::abs(mph - pending_) <= 25)) {
                value = mph; pending_ = -1; age_frames = 0;
                fresh = has_value = true;
            } else pending_ = mph;
        } else {
            pending_ = -1; // separated reads cannot confirm an outlier
            if (missing < 180) ++missing;
            if (missing >= 180) { value = 0; has_value = false; }
        }
        return value;
    }
    // A measured zero is fresh/held, not unavailable.
    int status() const { return has_value ? (fresh ? 1 : 2) : 0; }
private:
    int pending_ = -1;
};
}
