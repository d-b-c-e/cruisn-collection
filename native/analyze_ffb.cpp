// Offline execution of the actual vendored force shaper/detector. No SDL/device APIs.
#include "force_profile.h"
#include "impact_mixer.h"
#include "motor_signal.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Sample { long long ms; int byte; int raw; };
int main(int argc, char **argv) {
    if (argc != 6 && argc != 7) { std::fprintf(stderr, "trace profiles_dir profile_id strength output_csv\n"); return 2; }
    bool enhanced = argc == 7 && std::string(argv[6]) == "--impacts";
    if (argc == 7 && !enhanced) return 2;
    int strength = std::atoi(argv[4]);
    if (strength < 0 || strength > 100) return 2;
    dbce::force::Profile profile; std::string why;
    if (!dbce::force::load_profile_dir(argv[2], argv[3], profile, &why)) {
        std::fprintf(stderr, "profile: %s\n", why.c_str()); return 1;
    }
    std::ifstream input(argv[1]);
    std::vector<Sample> samples; std::string line;
    bool source_columns = false;
    bool motor_columns = false; long long end_ms = 0;
    while (std::getline(input, line)) {
        if (line.empty() || line[0] == '#') continue;
        if (line.find("seconds,frame,raw,adapted") == 0) { source_columns = true; continue; }
        if (line.find("ms,raw,byte") == 0) { motor_columns = true; continue; }
        if (line.find("ms,output,value") == 0) continue;
        std::istringstream row(line); std::string t, name, value;
        if (!std::getline(row, t, ',') || !std::getline(row, name, ',') || !std::getline(row, value)) continue;
        try {
            long long ms = source_columns ? std::llround(std::stod(t) * 1000) : std::stoll(t); end_ms = std::max(end_ms, ms);
            if (!source_columns && !motor_columns && name != "wheel" && name != "wheel_motor") continue;
            int raw = std::stoi(source_columns ? value.substr(value.find(',') + 1) : value);
            if (!motor_columns && !source_columns) { raw &= 255; if (raw >= 128) raw -= 256; }
            if (raw < -128 || raw > 127 || ms < 0) throw std::runtime_error("range");
            int original = source_columns ? std::stoi(value.substr(0, value.find(','))) : (motor_columns ? std::stoi(name) : raw);
            if (original < -128 || original > 127) throw std::runtime_error("raw range");
            samples.push_back(Sample{ms, raw, original});
        } catch (...) { std::fprintf(stderr, "invalid trace row: %s\n", line.c_str()); return 1; }
    }
    if (samples.empty() || end_ms > 24LL * 60 * 60 * 1000) {
        std::fprintf(stderr, "missing motor samples or trace longer than one day\n"); return 1;
    }
    if (!std::is_sorted(samples.begin(), samples.end(), [](const Sample& a, const Sample& b) { return a.ms < b.ms; })) {
        std::fprintf(stderr, "motor timestamps go backwards\n"); return 1;
    }
    // Matches mvffb's percent-to-toolkit conversion, including integer rounding.
    profile.shaper.strength = enhanced ? 50 : strength / 2; profile.shaper.invert = false;
    dbce::force::Shaper shaper(profile.shaper);
    dbce::force::RiseDetector detector;
    dbce::force::ImpactMixer mixer;
    // Arrival reachability is a necessary condition, not a collision label.
    // Measure every source write as well as sampled ticks: a short source peak
    // can fall entirely between this analyzer's idealized 4 ms observations.
    float source_peak = 0.f, sampled_peak = 0.f;
    for (const auto &sample : samples)
        source_peak = std::max(source_peak,
            std::abs(float(cruisn::motor_level(enhanced ? sample.raw : sample.byte)) / 32767.f));
    long long eligible_ticks = 0;
    std::ofstream csv(argv[5]);
    if (!csv) return 1;
    csv << "ms,motor_byte,normalised,shaped,impact_candidate,arrival,rise,rumble_request,mixed,raw_byte,detector_input\n";
    size_t next = 0; int current = 0, raw = 0; long long ticks = 0, full_ticks = 0;
    double sum_squares = 0, peak = 0;
    std::vector<long long> events;
    for (long long ms = 0; ms <= end_ms; ms += 4) {
        while (next < samples.size() && samples[next].ms <= ms) { current = samples[next].byte; raw = samples[next++].raw; }
        float normal = float(cruisn::motor_level(current)) / 32767.f;
        float candidate = enhanced ? float(cruisn::motor_level(raw)) / 32767.f : normal;
        sampled_peak = std::max(sampled_peak, std::abs(candidate));
        if (std::abs(candidate) >= detector.arrival) ++eligible_ticks;
        bool event = detector.observe(candidate, double(ms) / 1000.0);
        float shaped = shaper.shape(normal, 0.f, .004f, false);
        float rumble = event ? detector.last_arrival * strength / 100.f : 0.f;
        if (event) { events.push_back(ms); if (enhanced) mixer.trigger(detector.last_arrival, candidate, double(ms) / 1000.0); }
        float mixed = enhanced ? mixer.mix(shaped, double(ms) / 1000.0, strength / 100.f) : shaped;
        csv << ms << ',' << current << ',' << normal << ',' << shaped << ',' << int(event)
            << ',' << detector.last_arrival << ',' << detector.last_rise << ',' << rumble << ',' << mixed << ',' << raw << ',' << candidate << '\n';
        peak = std::max(peak, std::abs(double(mixed))); sum_squares += mixed * mixed; ++ticks;
        float limit = enhanced ? strength / 100.f : (strength / 2) / 50.f;
        if (limit > 0 && std::abs(mixed) >= limit * .9999f) ++full_ticks;
    }
    csv.close();
    if (!csv) return 1;
    std::printf("{\"tick_ms\":4,\"ticks\":%lld,\"motor_samples\":%zu,\"strength\":%d,"
                "\"peak_abs\":%.9f,\"rms\":%.9f,\"full_strength_fraction\":%.9f,\"events_ms\":[",
                ticks, samples.size(), strength, peak, std::sqrt(sum_squares/ticks), double(full_ticks)/ticks);
    for (size_t n=0; n<events.size(); ++n) std::printf("%s%lld", n ? "," : "", events[n]);
    std::printf("],\"detector\":{\"input\":\"%s\",\"arrival\":%.9f,\"rise\":%.9f,"
                "\"source_peak_abs\":%.9f,\"sampled_peak_abs\":%.9f,"
                "\"source_arrival_reachable\":%s,\"sampled_arrival_ticks\":%lld}}\n",
                enhanced ? "raw_motor" : "adapted_motor", detector.arrival, detector.rise,
                source_peak, sampled_peak, source_peak >= detector.arrival ? "true" : "false", eligible_ticks);
    return 0;
}
