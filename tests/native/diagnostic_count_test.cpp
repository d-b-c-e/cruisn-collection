// SPDX-License-Identifier: BSD-3-Clause
#include "diagnostic_count.h"
#include "exotica_command_owners.h"
#include "zeus_endpoint_pair.h"
#include <cassert>

int main() {
    using Policy=cruisn::DiagnosticJournal::Policy;
    using cruisn::diagnostic_count::add;
    const auto max64=std::numeric_limits<uint64_t>::max();
    const uint64_t max32=std::numeric_limits<uint32_t>::max();
    uint64_t capture=65535,quiet=capture;
    assert(add(capture,1,Policy::capture,65536,max32) && capture==65536);
    assert(!add(capture,1,Policy::capture,65536,max32) && capture==65536);
    assert(add(quiet,2,Policy::quiet,65536,max32) && quiet==65537);
    quiet=max32-1;assert(add(quiet,1,Policy::quiet,65536,max32) && quiet==max32);
    assert(!add(quiet,1,Policy::quiet,65536,max32) && quiet==max32);
    uint64_t bytes=64*1024*1024-8;
    assert(!add(bytes,9,Policy::capture,64*1024*1024) && bytes==64*1024*1024-8);
    assert(add(bytes,9,Policy::quiet,64*1024*1024) && bytes==64*1024*1024+1);
    bytes=max64-8;assert(!add(bytes,9,Policy::quiet,64*1024*1024) && bytes==max64-8);
    assert(add(bytes,8,Policy::quiet,64*1024*1024) && bytes==max64);
    assert(!add(bytes,1,Policy::quiet,64*1024*1024) && bytes==max64);
    assert(!add(bytes,0,static_cast<Policy>(7),max64));

    // Exercise the actual producer-ticket and GPU-pair helpers past65536,
    // across drained guest epochs. IDs stay monotonic; no aliasing/reset to1.
    cruisn::exotica_commands::Owners owners;assert(owners.reset(1));
    cruisn::zeus_endpoint_pair::Order order;
    uint64_t id=0;
    for(uint32_t n=1;n<=70000;++n) {
        if(n==35001)assert(owners.reset(2));
        assert(add(id,1,Policy::quiet,65536,max32) && id==n);
        assert(owners.submit(id,0x30002,0x24860000,1));
        cruisn::exotica_commands::Ticket ticket;
        assert(owners.consume(0x30002,0x24860000,1,ticket)==cruisn::exotica_commands::Status::matched);
        assert(ticket.id==id && ticket.epoch==(n<=35000?1:2) && !owners.pending());
        cruisn::zeus_endpoint_pair::Pair pair;pair.frame=n;pair.model=uint32_t(ticket.id);pair.count=1;
        pair.original.state[1]=pair.replacement.state[1]=3;
        std::array<uint8_t,544> wire;
        assert(cruisn::zeus_endpoint_pair::encode(pair,wire));
        cruisn::zeus_endpoint_pair::Pair decoded;assert(cruisn::zeus_endpoint_pair::decode(wire.data(),wire.size(),decoded));
        assert(decoded.model==ticket.id && order.expect(decoded));
        cruisn::zeus_model::Quad result;assert(order.consume(decoded.original,result) && order.complete());
    }
    // The last representable ID is legal; wrapping or reusing a low ID is not.
    cruisn::zeus_endpoint_pair::Pair last;last.frame=70001;last.model=uint32_t(max32);last.count=1;
    last.original.state[1]=last.replacement.state[1]=3;
    assert(order.expect(last));cruisn::zeus_model::Quad result;assert(order.consume(last.original,result));
    last.frame++;last.model=1;assert(!order.expect(last));
}
