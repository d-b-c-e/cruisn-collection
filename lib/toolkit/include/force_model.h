// force_model.h - header-only force model and output conditioning (C++11).
//
// The C++ counterpart of Dbce.Wheel.Ffb's ForceModel and ForceShaper, for
// native mods (dinput8 proxies, emulator forks). Same terms, same order, same
// constants; a conformance test drives both with one profile and the same input
// sequence and requires identical output, so the two cannot drift.
//
// The split that matters: this file decides how a force FEELS. Working out what
// the car is doing - reading the car struct, a surface lookup table, collision
// flags - stays in the game's own mod, because that part really is per game.
// Fill a ForceInputs from whatever the game exposes, leave the has* flags false
// for what it does not, and the model uses what it has.
//
//   dbce::force::Profile p;
//   dbce::force::load_profile_dir(gameDir, "arcade-outrun@1", p);   // force_profile.h
//   dbce::force::Model  model(p.model);
//   dbce::force::Shaper shaper(p.shaper);
//   ...
//   dbce::force::Inputs in;
//   in.steer = steer; in.has_steer = true;
//   in.speed_mps = speed; in.lateral_g = lat; in.has_lateral_g = true;
//   float f = shaper.shape(model.compute(in, dt), speed * 3.6f, dt, model.last_was_event);
//   ffb.SetDeviceForcesXY((int)(f * 10000.f), 0);
//
// Sign convention: a positive output pushes the wheel toward positive steer,
// so the model returns a NEGATIVE force for a positive steer, which is
// centring. Which DirectInput sign that maps to is a per-wheel fact - measure
// it and set shaper.invert.
//
// Lineage: OutRun2006Tweaks-FFB (the centre-out structure, the conditioning
// chain and its order), art-of-sim-rally (lateral force x trail, low-speed
// fade), cruisn-collection (slew and peak clamp as the instability ladder).
#pragma once
#include <cmath>
#include <cstring>
#include <deque>

namespace dbce { namespace force {

// A source-signal rise candidate, not proof of a collision. Feed every sample,
// including unchanged values and zero, in PRE-GAIN units. A steady plateau must
// not retrigger, and changing wheel strength must not change recognition.
class RiseDetector {
public:
    float arrival = 0.80f, rise = 0.40f;
    double window_seconds = 0.25, cooldown_seconds = 0.25;
    float last_arrival = 0.f, last_rise = 0.f;

    void reset() {
        minima_.clear(); last_time_ = -1.0; last_event_ = -1e30;
        last_arrival = last_rise = 0.f;
    }

    bool observe(float normalised, double seconds) {
        if (!std::isfinite(normalised) || !std::isfinite(seconds) || seconds < 0.0) {
            reset(); return false;
        }
        if (seconds < last_time_) reset();
        if (seconds == last_time_) return false;
        last_time_ = seconds;
        float level = std::fabs(normalised);
        if (level > 1.f) level = 1.f;
        while (!minima_.empty() && minima_.front().time < seconds - window_seconds)
            minima_.pop_front();
        while (!minima_.empty() && minima_.back().value >= level)
            minima_.pop_back();
        minima_.push_back(Sample{seconds, level});
        last_arrival = level;
        last_rise = level - minima_.front().value;
        if (level >= arrival && last_rise >= rise && seconds - last_event_ >= cooldown_seconds) {
            last_event_ = seconds;
            return true;
        }
        return false;
    }

private:
    struct Sample { double time; float value; };
    std::deque<Sample> minima_;
    double last_time_ = -1.0, last_event_ = -1e30;
};

// ---------------------------------------------------------------- inputs
struct Inputs {
    float steer;              // -1..1, left negative
    float steer_rate;         // full travel per second
    bool  has_steer, has_steer_rate;

    float speed_mps;          // absolute

    float front_lateral_force;// newtons on the steered axle
    bool  has_front_lateral_force;
    float lateral_g;          // when tyre forces are not available
    bool  has_lateral_g;
    float longitudinal_g;     // positive accelerating
    bool  has_longitudinal_g;

    float front_slip_angle_deg, ideal_slip_angle_deg;
    bool  has_slip;
    float drift_amount;       // 0..1
    bool  has_drift;

    float texture;            // 0..1 surface texture this tick
    float impact;             // >0 for one tick on a collision
    float impact_direction;   // -1 left, +1 right, 0 unknown
    bool  gear_shift;         // true for one tick

    Inputs() { std::memset(this, 0, sizeof(*this)); }
};

// ---------------------------------------------------------------- settings
// Defaults match Dbce.Wheel.Ffb.ForceModelSettings exactly.
struct ModelSettings {
    float spring_strength;
    float spring_full_speed_mps;
    float damper_strength;
    float damper_static_fraction;
    float lateral_weight;            // ForceModelSettings.SteeringWeight
    float lateral_force_reference;
    float lateral_g_reference;
    float trail_floor;
    float trail_slip_span;
    float grip_loss;
    float weight_transfer;
    float weight_transfer_min, weight_transfer_max;
    float texture_strength;
    float texture_hz;
    float impact_strength;
    float impact_seconds;
    float shift_strength;
    float shift_seconds;

    ModelSettings()
        : spring_strength(0.f), spring_full_speed_mps(30.f),
          damper_strength(0.f), damper_static_fraction(0.4f),
          lateral_weight(1.f), lateral_force_reference(11500.f), lateral_g_reference(1.2f),
          trail_floor(0.6f), trail_slip_span(2.f), grip_loss(0.f),
          weight_transfer(0.f), weight_transfer_min(-0.20f), weight_transfer_max(0.30f),
          texture_strength(0.f), texture_hz(12.f),
          impact_strength(0.f), impact_seconds(0.12f),
          shift_strength(0.f), shift_seconds(0.04f) {}
};

// Defaults match Dbce.Wheel.Ffb.ForceShaper exactly.
struct ShaperSettings {
    int   strength;            // 0..100, 50 = unity
    bool  invert;
    float deadzone;
    float attack_smoothing, decay_smoothing;
    float soft_saturation;
    float slew_per_second;
    float output_deadband;
    float fade_start_kmh, fade_full_kmh;
    float ramp_seconds;
    float peak_limit;

    // ---- from Cruis'n (mvffb). All default to off, so existing profiles
    // behave exactly as before. See ForceShaper.cs for why each exists.
    float smoothing_ms;       // frame-rate independent low-pass time constant, ms
    float impulse_bypass;     // an input jump this big is an event by itself
    float settle_below;       // input 0 and |out| under this -> snap to 0
    float releveling;         // hold the last value until it moves this far

    ShaperSettings()
        : strength(50), invert(false), deadzone(0.0015f),
          attack_smoothing(0.2f), decay_smoothing(0.2f), soft_saturation(0.f),
          slew_per_second(0.f), output_deadband(0.0015f),
          fade_start_kmh(3.f), fade_full_kmh(12.f), ramp_seconds(0.25f), peak_limit(1.f),
          smoothing_ms(0.f), impulse_bypass(0.f), settle_below(0.f), releveling(0.f) {}
};

// ---------------------------------------------------------------- helpers
inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
inline float signf(float v) { return v > 0.f ? 1.f : (v < 0.f ? -1.f : 0.f); }

// ---------------------------------------------------------------- model
class Model {
public:
    explicit Model(const ModelSettings& s) : settings(s) { reset(); }

    ModelSettings settings;

    // True when the last compute() carried an impulse that must bypass
    // smoothing and slew. Pass it to Shaper::shape.
    bool  last_was_event;
    // Last structural (non-event) force, for traces.
    float last_structural;

    void reset() {
        shift_t_ = -1.f; shift_emitted_ = 0.f;
        impact_t_ = -1.f; impact_sign_ = 0.f; impact_mag_ = 0.f;
        texture_phase_ = 0.f;
        last_was_event = false; last_structural = 0.f;
    }

    // One tick. Normalised against the profile's references, but NOT bounded:
    // a force past full scale is real information. Shaper::shape bounds the
    // output at the device edge.
    float compute(const Inputs& i, float dt) {
        const ModelSettings& s = settings;
        dt = clampf(dt, 0.f, 0.1f);
        const float pi = 3.14159265358979323846f;
        float speed_norm = std::fabs(i.speed_mps) / (s.spring_full_speed_mps > 0.1f ? s.spring_full_speed_mps : 0.1f);
        if (speed_norm > 1.f) speed_norm = 1.f;

        // --- lateral load: tyre force if we have it, lateral g otherwise ---
        float lateral = 0.f;
        if (i.has_front_lateral_force)
            lateral = i.front_lateral_force / (s.lateral_force_reference > 1.f ? s.lateral_force_reference : 1.f);
        else if (i.has_lateral_g)
            lateral = i.lateral_g / (s.lateral_g_reference > 0.05f ? s.lateral_g_reference : 0.05f);
        // Trail: lightens toward the limit instead of reversing like a Pacejka Mz.
        if (i.has_slip && s.trail_floor < 1.f) {
            float ideal = i.ideal_slip_angle_deg > 0.5f ? i.ideal_slip_angle_deg : 0.5f;
            float span = s.trail_slip_span * ideal;
            if (span < 0.1f) span = 0.1f;
            float t = std::fabs(i.front_slip_angle_deg) / span;
            if (t > 1.f) t = 1.f;
            lateral *= 1.f - (1.f - s.trail_floor) * t;
        }
        if (i.has_drift && s.grip_loss > 0.f)
            lateral *= 1.f - s.grip_loss * clampf(i.drift_amount, 0.f, 1.f);
        // The road pushes back against the direction the tyre is loaded.
        float f_lat = -lateral * s.lateral_weight;

        // --- spring and damper (arcade) ---
        float f_spring = i.has_steer ? -i.steer * s.spring_strength * speed_norm : 0.f;
        float k = clampf(s.damper_static_fraction, 0.f, 1.f);
        float f_damper = i.has_steer_rate ? -i.steer_rate * s.damper_strength * (k + (1.f - k) * speed_norm) : 0.f;

        float load_mod = 1.f;
        if (i.has_longitudinal_g && s.weight_transfer != 0.f)
            load_mod = 1.f + clampf(-i.longitudinal_g * s.weight_transfer, s.weight_transfer_min, s.weight_transfer_max);

        float structural = (f_spring + f_lat) * load_mod + f_damper;
        last_structural = structural;

        // --- texture ---
        float texture = 0.f;
        if (s.texture_strength > 0.f && i.texture > 0.f && dt > 0.f) {
            float hz = s.texture_hz > 0.1f ? s.texture_hz : 0.1f;
            texture_phase_ += dt * hz * pi * 2.f;
            float lvl = i.texture > 1.f ? 1.f : i.texture;
            texture = std::sin(texture_phase_) * s.texture_strength * lvl;
        }

        // --- events ---
        bool is_event = false;
        float ev = 0.f;
        if (i.impact > 0.f) {
            impact_t_ = 0.f;
            impact_mag_ = i.impact > 1.f ? 1.f : i.impact;
            impact_sign_ = i.impact_direction != 0.f ? signf(i.impact_direction)
                             : (i.has_steer && i.steer != 0.f ? -signf(i.steer) : 1.f);
        }
        if (impact_t_ >= 0.f) {
            float span = s.impact_seconds > 0.001f ? s.impact_seconds : 0.001f;
            float decay = 1.f - impact_t_ / span;
            if (decay < 0.f) decay = 0.f;
            ev += impact_sign_ * impact_mag_ * s.impact_strength * decay;
            impact_t_ += dt;
            if (impact_t_ > span) impact_t_ = -1.f;
            is_event = true;
        }
        if (i.gear_shift && s.shift_strength > 0.f) { shift_t_ = 0.f; shift_emitted_ = 0.f; }
        if (shift_t_ >= 0.f) {
            // Symmetric double pulse: what went out positive comes back negative,
            // so it nets to zero at any tick rate and reads as a jolt rather than
            // the game yanking the wheel sideways.
            float half = s.shift_seconds > 0.001f ? s.shift_seconds : 0.001f;
            if (shift_t_ < half) { ev += s.shift_strength; shift_emitted_ += s.shift_strength; }
            else if (shift_emitted_ > 0.f) {
                float back = s.shift_strength < shift_emitted_ ? s.shift_strength : shift_emitted_;
                ev -= back; shift_emitted_ -= back;
            }
            shift_t_ += dt;
            if (shift_t_ >= half && shift_emitted_ <= 0.f) shift_t_ = -1.f;
            is_event = true;
        }

        last_was_event = is_event;
        // Deliberately NOT clamped; see the note on the C# ForceModel.Compute.
        // The clamp is a device limit and belongs at the edge, in Shaper::shape.
        // Applied here it also defeated the soft saturation, which received an
        // already-clamped value and so had nothing left to compress.
        return structural + texture + ev;
    }

private:
    float shift_t_, shift_emitted_;
    float impact_t_, impact_sign_, impact_mag_;
    float texture_phase_;
};

// ---------------------------------------------------------------- shaper
// Deadzone -> EMA -> GAIN/INVERT -> soft saturation -> slew -> fade -> ramp ->
// clamp -> deadband. The order is fixed; see knowledge/FFB-SIGNAL-DESIGN.md.
// Gain and invert are the boundary between model units and true output units
// and sign; every stage after them is a device-side limit. They moved there in
// 0.8.0, because the slew limiter compares against last_ and could not be
// correct while last_ and the value being limited disagreed on scale or sign.
// An event bypasses the EMA and the slew so it arrives as a pulse, not a shove.
class Shaper {
public:
    explicit Shaper(const ShaperSettings& s) : settings(s) { reset(); }

    ShaperSettings settings;

    void reset() { smoothed_ = 0.f; last_ = 0.f; ramp_t_ = 0.f; started_ = false;
                   prev_in_ = 0.f; have_prev_in_ = false; }
    // Start the ramp again, e.g. after the native layer recreated the effect.
    void restart_ramp() { ramp_t_ = 0.f; started_ = false; }

    float last() const { return last_; }
    bool started() const { return started_; }
    float gain() const { return (settings.strength > 0 ? settings.strength : 0) / 50.f; }

    float shape(float normalised, float speed_kmh, float dt, bool is_event = false) {
        const ShaperSettings& s = settings;
        if (!(normalised == normalised)) normalised = 0.f;               // NaN
        if (normalised > 1e30f || normalised < -1e30f) normalised = 0.f; // inf
        dt = clampf(dt, 0.f, 0.1f);
        float v = normalised;

        // 1. subtractive deadzone
        if (std::fabs(v) <= s.deadzone) v = 0.f; else v -= signf(v) * s.deadzone;

        // 1b. automatic impulse detection: a big enough jump IS an event even
        //     when the caller had no way to tell us so.
        if (s.impulse_bypass > 0.f && have_prev_in_ && std::fabs(v - prev_in_) >= s.impulse_bypass)
            is_event = true;
        prev_in_ = v; have_prev_in_ = true;
        float const target = v;

        // 2. smoothing (structural only). smoothing_ms, when set, is a
        //    frame-rate independent time constant and wins over the coefficients.
        if (!is_event) {
            if (s.smoothing_ms > 0.f) {
                float const a = 1.f - std::exp(-(dt * 1000.f) / s.smoothing_ms);
                smoothed_ = smoothed_ + (v - smoothed_) * a;
            } else {
                float a = std::fabs(v) > std::fabs(smoothed_) ? s.attack_smoothing : s.decay_smoothing;
                a = clampf(a, 0.f, 0.95f);
                smoothed_ = smoothed_ + (v - smoothed_) * (1.f - a);
            }
            v = smoothed_;
        } else {
            smoothed_ = v;
        }

        // 3. gain. The line between the two halves of the chain: above it the
        //    value is in model units, below it in output units, and everything
        //    below is a device-side limit. Applied last (as it was before 0.8.0)
        //    Strength re-inflated an already-saturated value into the hard clamp.
        //    Invert moves with it: the slew limiter below compares against last_,
        //    the value actually sent, and with invert applied at the end those two
        //    had opposite signs - a steady input then oscillated near zero and no
        //    force ever arrived.
        v *= gain();
        if (s.invert) v = -v;

        // 4. soft saturation
        if (s.soft_saturation > 0.f) {
            float k = s.soft_saturation;
            v = (1.f - k) * v + k * std::tanh(v);
        }

        // 5. slew (structural only). Now in output units.
        if (!is_event && s.slew_per_second > 0.f && dt > 0.f) {
            float step = s.slew_per_second * dt;
            v = clampf(v, last_ - step, last_ + step);
        }

        // 6. low-speed fade
        if (s.fade_full_kmh > s.fade_start_kmh) {
            float t = (speed_kmh - s.fade_start_kmh) / (s.fade_full_kmh - s.fade_start_kmh);
            t = clampf(t, 0.f, 1.f);
            v *= t * t * (3.f - 2.f * t);   // smoothstep
        }

        // 7. warm-up / restart ramp
        if (s.ramp_seconds > 0.f && ramp_t_ < s.ramp_seconds) {
            ramp_t_ += dt; started_ = true;
            float r = ramp_t_ / s.ramp_seconds;
            v *= r > 1.f ? 1.f : r;
        }

        // 8. clamp, peak limit, deadband
        float limit = clampf(s.peak_limit, 0.f, 1.f);
        v = clampf(v, -limit, limit);
        if (std::fabs(v) < s.output_deadband) v = 0.f;

        // 9. settle: the game asked for nothing and what is left is a dying tail.
        if (s.settle_below > 0.f && target == 0.f && std::fabs(v) < s.settle_below) {
            smoothed_ = 0.f;
            v = 0.f;
        }

        // 10. re-level hysteresis: hold until it has moved far enough to send.
        if (s.releveling > 0.f && ((v != 0.f) == (last_ != 0.f)) &&
                std::fabs(v - last_) < s.releveling)
            v = last_;

        last_ = v;
        return v;
    }

private:
    float smoothed_, last_, ramp_t_, prev_in_;
    bool  have_prev_in_;
    bool  started_;
};

}} // namespace dbce::force
