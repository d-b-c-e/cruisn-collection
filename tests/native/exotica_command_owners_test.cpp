// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_command_owners.h"
#include <cassert>
#include <iostream>
using namespace cruisn::exotica_commands;
int main()
{
    Owners owners;Ticket out;out.id=999;
    assert(!owners.submit(1,0x30002,0x24860006,0x100));
    assert(owners.consume(0x30002,0x24860006,0x100,out)==Status::invalid);
    assert(owners.reset(1) && !owners.reset(1));
    assert(owners.submit(1,0x30002,0x24860006,0x100));
    assert(owners.submit(3,0x30010,0x24860006,0x100)); // identical geometry is two owners
    assert(!owners.submit(4,0x30002,0x24860006,0x100) && !owners.reset(2));
    assert(owners.consume(0x30008,0x24860006,0x100,out)==Status::untracked && out.id==999);
    assert(owners.consume(0x30010,0x24860006,0x100,out)==Status::invalid && owners.pending()==2);
    assert(owners.consume(0x30002,0x24860007,0x100,out)==Status::invalid && out.id==999);
    assert(owners.consume(0x30002,0x24860006,0x101,out)==Status::invalid && out.id==999);
    assert(owners.consume(0x30002,0x24860006,0x100,out)==Status::matched && out.id==1 && out.epoch==1);
    assert(owners.consume(0x30010,0x24860006,0x100,out)==Status::matched && out.id==3);
    assert(!owners.submit(2,0x30002,0x24860006,0x100));
    assert(owners.reset(2) && owners.submit(1,0x31ffe,0x24860006,0x100));
    assert(owners.submit(2,0x30000,0x24860006,0x100)); // wrapped ring, ordered tickets
    assert(owners.consume(0x31ffe,0x24860006,0x100,out)==Status::matched && out.epoch==2);
    assert(owners.consume(0x30000,0x24860006,0x100,out)==Status::matched && out.id==2);
    for(auto end:{0u,0x2ffffu,0x32000u,0xffffffffu})assert(!owners.submit(3,end,0x24860006,0x100));
    assert(!owners.submit(3,0x30002,0x24860006,0) && !owners.submit(3,0x30002,0x2486c801,0x100));
    assert(!owners.submit(3,0x30002,0x25860006,0x100));
    assert(owners.reset(3));
    for(uint32_t i=0;i<4096;++i)assert(owners.submit(i+1,0x30000+i,0x24860006,0x100));
    assert(!owners.submit(4097,0x31000,0x24860006,0x100));
    assert(owners.consume(0x30000,0x24860006,0x100,out)==Status::matched);
    assert(owners.submit(4097,0x31000,0x24860006,0x100));
    std::cout<<"PASS exact ring model ownership, order, reuse, reset and bounds\n";
}
