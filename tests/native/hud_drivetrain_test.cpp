#include "../../native/hud_drivetrain.h"
#include <cassert>
#include <vector>

int main()
{
    using namespace cruisn;
    assert(c31_drivetrain_float(0x80000000)==0);
    assert(c31_drivetrain_float(0)==1); // C31 zero is not IEEE zero
    assert(c31_drivetrain_float(0x00800000)==-2);
    assert(c31_drivetrain_float(0x053c0000)==47);
    std::vector<uint32_t> ram(0x20000);
    ram[0x9e53]=0x0828e8a8;ram[0x9e54]=0x07400039;ram[0x9e55]=0x0a60e6aa;
    ram[0x9e6b]=0x08400038;ram[0x9d87]=0x084a0038;ram[0xe8a8]=0xde76;
    auto read=[&] { return usa_drivetrain(ram.data(),ram.size()); };
    ram[0xdeae]=1;ram[0xdeaf]=0x053c0000;
    auto high=read();assert(high.valid && high.gear==1 && high.rpm>7800 && high.rpm<8000);
    ram[0xdeae]=2;ram[0xdeaf]=0x044f757a; // observed post-upshift rev, ~25.93
    auto low=read();assert(low.valid && low.gear==2 && low.rpm<high.rpm-2000);
    for (unsigned g=0;g<=4;++g) {ram[0xdeae]=g;assert(read().gear==int(g));}
    ram[0xdeae]=5;assert(!read().valid);
    ram[0xdeae]=0;ram[0xdeaf]=0x80000000;assert(read().rpm==900);
    ram[0xdeaf]=0x00800000;assert(!read().valid);
    ram[0xdeaf]=0x7f7fffff;assert(!read().valid);
    ram[0xdeaf]=0x05600000;assert(read().fraction==1); // legal over-rev clamps fill
    ram[0xe8a8]=0xfffffff0;assert(!read().valid);
    ram[0xe8a8]=0x1ffff;assert(!read().valid);
    ram[0xe8a8]=0xde76;ram[0x9e55]^=1;assert(!read().valid);
    assert(!usa_drivetrain(nullptr,0).valid);
    assert(!usa_drivetrain(ram.data(),100).valid);
}
