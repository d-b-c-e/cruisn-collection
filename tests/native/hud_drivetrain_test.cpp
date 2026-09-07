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

    for (bool v25 : {false,true}) {
        std::fill(ram.begin(),ram.end(),0);
        unsigned c=v25?0x9acf:0x9ada,p=v25?0xee08:0xee0e;
        unsigned g=v25?0x99e5:0x99f0,s=v25?0xebdc:0xebe2;
        ram[c]=0x08280000|p;ram[c+1]=0x07400052;ram[c+2]=0x0a60e6aa;
        ram[c+25]=0x08400051;ram[g]=0x08200000|s;ram[g+1]=0x04e00005;
        ram[g+3]=0x04e00004;ram[g+8]=0x084a0051;
        ram[p]=0xe3d0;ram[0xe421]=3;ram[0xe422]=0x0504e249;
        ram[s]=4;ram[s+1]=0x26;
        auto d=world_drivetrain(ram.data(),ram.size(),v25);
        assert(d.valid && d.gear==3 && d.rpm>5800 && d.rpm<5900);
        assert(world_driving(ram.data(),ram.size(),v25));
        ram[s]=5;ram[s+1]=2; // observed finish: HUD remains, driving ends
        assert(world_drivetrain(ram.data(),ram.size(),v25).valid);
        assert(!world_driving(ram.data(),ram.size(),v25));
        ram[s]=6;assert(!world_drivetrain(ram.data(),ram.size(),v25).valid);
        ram[s]=4;ram[p]=0xfffffffc;assert(!world_drivetrain(ram.data(),ram.size(),v25).valid);
        ram[c+2]^=1;assert(!world_drivetrain_code(ram.data(),ram.size(),v25));
    }
    ram.assign(0x40000,0);
    ram[0xc2ac]=0x082810be;ram[0xc2ad]=0x084a0062;
    ram[0xc2c0]=0x082810be;ram[0xc2c1]=0x07400063;ram[0xc2c2]=0x0a60f2ac;
    ram[0xc285]=0x08200076;ram[0xc286]=0x78850000;
    ram[0x3c1b]=0x0a60e7ae;ram[0x3c1d]=0x15201074;
    ram[0x76]=1;ram[0x10be]=0x113ff;ram[0x11461]=1;ram[0x11462]=0x053e56c7;ram[0x1074]=38;
    assert(exotica_drivetrain(ram.data(),ram.size()).rpm>7900);
    assert(exotica_hud_mph(ram.data(),ram.size())==38);
    ram[0x76]=0;assert(!exotica_drivetrain(ram.data(),ram.size()).valid);
    assert(exotica_hud_mph(ram.data(),ram.size())==-1);

    ram.assign(0x20000,0);
    ram[0xabed]=0x082cc86c;ram[0xabee]=0x0aec00bc;ram[0xabef]=0x022c9d25;
    ram[0xaca7]=0x07420436;ram[0xaca8]=0x0a229d6b;ram[0xad9b]=0x0852040b;
    ram[0xad7f]=0x07209d11;ram[0xad84]=0x0a229d77;ram[0xad91]=0x050a0002;ram[0xad97]=0x6200a5cc;
    ram[0x19d6b]=0xf303126f;ram[0x19d25]=0x1c0e1;ram[0x1c0ec]=1;ram[0x1c117]=0x0c3783a3;
    ram[0x19d11]=0x0602eb64;ram[0x19d77]=0xfe6a0dbb;ram[0x19d0c]=1;
    auto off=offroad_drivetrain(ram.data(),ram.size());
    assert(off.valid && off.gear==1 && off.rev>5800 && off.rev<5900);
    assert(offroad_hud_mph(ram.data(),ram.size())==29);
    ram[0x1c86c]=0xffffffff;assert(!offroad_drivetrain(ram.data(),ram.size()).valid);
}
