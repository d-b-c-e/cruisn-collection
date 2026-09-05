#include <cstdio>
#include <string>
#include "dbce/force_model.h"
#include "dbce/force_profile.h"
int main(int argc, char** argv) {
    std::string dir = argc > 1 ? argv[1] : ".";
    std::string id  = argc > 2 ? argv[2] : "cruisn-vunit@1";
    dbce::force::Profile p; std::string why;
    if (!dbce::force::load_profile_dir(dir, id, p, &why)) {
        std::printf("FAILED to load '%s' from %s: %s\n", id.c_str(), dir.c_str(), why.c_str());
        return 1;
    }
    const dbce::force::ShaperSettings& s = p.shaper;
    std::printf("loaded %s from %s\n  %s\n", p.id().c_str(), dir.c_str(), p.description.c_str());
    std::printf("  strength=%d invert=%d deadzone=%g\n", s.strength, (int)s.invert, s.deadzone);
    std::printf("  smoothingMs=%g impulseBypass=%g settleBelow=%g releveling=%g\n",
                s.smoothing_ms, s.impulse_bypass, s.settle_below, s.releveling);
    std::printf("  softSat=%g slew=%g fade=%g..%g ramp=%g peak=%g\n",
                s.soft_saturation, s.slew_per_second, s.fade_start_kmh, s.fade_full_kmh,
                s.ramp_seconds, s.peak_limit);
    return 0;
}
