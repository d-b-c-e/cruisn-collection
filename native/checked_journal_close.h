// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstdio>

namespace cruisn {
// Retire the owner even on failure. Earlier buffered-write errors can survive
// a successful fclose, so both the stream error flag and final flush matter.
inline bool close_journal(FILE *&owner) {
    FILE *file=owner;owner=nullptr;
    if(!file)return true;
    const bool clean=std::ferror(file)==0;
    const int closed=std::fclose(file);
    return clean && closed==0;
}
}
