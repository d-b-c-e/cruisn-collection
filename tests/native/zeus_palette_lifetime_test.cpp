#include "zeus_palette_lifetime.h"
#include <cassert>

int main() {
    cruisn::zeus_palette_lifetime life;
    // Sparse references: wrapping a counter alone must not flush unused rows.
    life.use(33); life.use(65);
    for (unsigned n=0;n<256;++n) assert(life.conflicts(n)==(n==33 || n==65));
    life.clear(); for (unsigned n=0;n<256;++n) assert(!life.conflicts(n));
    // Each texture load has a dependent draw. One flush per 256 used slots,
    // independent of the initial slot or external consumer chunk boundaries.
    for (unsigned initial=0;initial<256;++initial) {
        life.clear(); unsigned flushes=0;
        for (unsigned load=1;load<=1025;++load) {
            const unsigned slot=(initial+load)&255;
            if (life.conflicts(slot)) { ++flushes; life.clear(); }
            assert(!life.conflicts(slot)); life.use(slot);
        }
        assert(flushes==4);
    }
    // An earlier draw clears only lifetime metadata; the selected palette row
    // remains reusable by later quads, which must mark a fresh reference.
    life.clear();life.use(7);life.clear();assert(!life.conflicts(7));
    life.use(7);assert(life.conflicts(7));
}
