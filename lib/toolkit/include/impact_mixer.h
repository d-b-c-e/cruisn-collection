// Explicit steering-axis impact envelope. No device APIs or game heuristics.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace dbce { namespace force {
class ImpactMixer {
public:
    // Reserve this share of the constant-force budget while enhancement is enabled.
    float headroom = .25f;
    uint64_t rejected_events = 0;

    void reset() { count_ = 0; last_time_ = -1.; }
    bool trigger(float amplitude, float direction, double seconds) {
        if (!std::isfinite(amplitude) || !std::isfinite(direction) ||
            !std::isfinite(seconds) || seconds < 0 || seconds < last_time_) {
            ++rejected_events; return false;
        }
        expire(seconds);
        if (count_ == 8) { ++rejected_events; return false; }
        last_time_ = seconds;
        events_[count_++] = Event{seconds, bounded(amplitude, 0.f, 1.f) * (direction < 0 ? -1.f : 1.f)};
        return true;
    }
    // Positive triangle: 0..20 ms, peak at 5 ms. Return triangle: 20..100 ms,
    // peak at 60 ms and one quarter amplitude. Equal/opposite areas, finite duration.
    static float envelope(double age) {
        if (age < 0 || age >= .100) return 0.f;
        if (age < .005) return float(age / .005);
        if (age < .020) return float((.020 - age) / .015);
        if (age < .060) return float(-.25 * (age - .020) / .040);
        return float(-.25 * (.100 - age) / .040);
    }
    float mix(float structural, double seconds, float strength = 1.f) {
        if (!std::isfinite(seconds) || seconds < 0 || seconds < last_time_ ||
            !std::isfinite(structural) || !std::isfinite(strength) || !std::isfinite(headroom)) {
            reset(); return 0.f;
        }
        last_time_ = seconds;
        expire(seconds);
        float pulse = 0.f;
        for (unsigned i = 0; i < count_; ++i)
            pulse += events_[i].signed_amplitude * envelope(seconds - events_[i].time);
        float reserve = bounded(headroom, 0.f, .5f);
        return bounded(strength, 0.f, 1.f) *
            (bounded(structural, -1.f, 1.f) * (1.f - reserve) + bounded(pulse, -1.f, 1.f) * reserve);
    }
private:
    struct Event { double time; float signed_amplitude; };
    Event events_[8] = {};
    unsigned count_ = 0;
    double last_time_ = -1.;
    static float bounded(float v, float lo, float hi) { return std::max(lo, std::min(v, hi)); }
    void expire(double seconds) {
        unsigned keep = 0;
        for (unsigned i = 0; i < count_; ++i)
            if (seconds - events_[i].time < .100) events_[keep++] = events_[i];
        count_ = keep;
    }
};
}}
