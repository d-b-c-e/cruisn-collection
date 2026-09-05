#include "hud_speed_filter.h"
#include <cstdio>
#define CHECK(x) do { if (!(x)) { std::printf("FAIL line %d: %s\n", __LINE__, #x); return 1; } } while (0)
int main() {
    cruisn::HudSpeedFilter f;
    CHECK(f.status() == 0);
    CHECK(f.observe(0) == 0 && f.status() == 1);
    CHECK(f.observe(100) == 0); CHECK(f.observe(101) == 101);
    for (int n = 0; n < 1000; ++n) {
        CHECK(f.observe(-1) == 101 && f.status() == 2);
        CHECK(f.observe(101) == 101 && f.missing == 0);
    }
    for (int n = 0; n < 179; ++n) CHECK(f.observe(-1) == 101);
    CHECK(f.observe(-1) == 0 && f.status() == 0);
    f.reset(); f.observe(100); f.observe(-1);
    CHECK(f.observe(100) == 0 && f.status() == 0); // not two consecutive readings
    CHECK(f.observe(100) == 100 && f.fresh && f.age_frames == 0);
    CHECK(f.observe(500) == 100 && f.missing == 1 && f.age_frames == 1);
    std::puts("HUD speed hold: consecutive misses, recovery, outliers and validity passed");
    return 0;
}
