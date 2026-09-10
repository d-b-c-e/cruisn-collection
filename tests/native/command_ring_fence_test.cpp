// SPDX-License-Identifier: BSD-3-Clause
#include "command_ring_fence.h"
#include <cassert>
#include <iostream>
int main()
{
    using Ring=cruisn::CommandRingFence<0x30000,0x2000>;using S=Ring::Status;
    Ring ring;
    assert(ring.begin(0x30000,0x30000,true)==S::ready && !ring.pending());
    assert(ring.begin(0x30000,0x30000,false)==S::invalid && !ring.pending());
    assert(ring.begin(0x2ffff,0x30000,true)==S::invalid);
    assert(ring.begin(0x30000,0x32000,true)==S::invalid);
    assert(ring.begin(0x31ffe,0x30001,false)==S::pending && ring.remaining()==3);
    assert(ring.begin(0x31ffe,0x30001,true)==S::invalid && ring.remaining()==3);
    assert(ring.consumed(0x30000,true)==S::invalid && ring.remaining()==3);
    assert(ring.consumed(0x31fff,false)==S::pending);
    assert(ring.consumed(0x30000,false)==S::pending);
    assert(ring.consumed(0x30001,false)==S::invalid && ring.remaining()==1);
    assert(ring.consumed(0x30001,true)==S::ready && !ring.pending());
    assert(ring.consumed(0x30002,true)==S::invalid);
    // Every start/target combination for a small ring, including wrap and
    // already drained boundaries; no speculative extra consumer word needed.
    using Small=cruisn::CommandRingFence<17,13>;using T=Small::Status;
    for(unsigned from=17;from<30;++from)for(unsigned to=17;to<30;++to)
    {
        Small r;const unsigned n=(to+13-from)%13;
        assert(r.begin(from,to,true)==(n?T::pending:T::ready));
        for(unsigned i=1;i<=n;++i)assert(r.consumed(17+(from-17+i)%13,i==n)==(i==n?T::ready:T::pending));
        assert(!r.pending() && r.cursor()==to && r.target()==to);
    }
    std::cout<<"PASS exact ring completion, wrap, atomic rejection and parser boundaries\n";
}
