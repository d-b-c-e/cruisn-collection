// SPDX-License-Identifier: BSD-3-Clause
#include "zeus_endpoint_pair.h"
#include <cassert>
#include <iostream>
using namespace cruisn::zeus_endpoint_pair;
int main() {
    Pair p;p.frame=5219;p.model=240;p.count=2;
    p.original.state[0]=5219;p.original.state[1]=4;p.original.state[7]=8;p.original.state[8]=240;
    p.original.state[9]=30;p.original.state[10]=2047;p.replacement=p.original;
    p.replacement.state[7]=248;p.replacement.state[8]=0;p.replacement.state[9]=28;p.replacement.state[10]=0;
    std::array<uint8_t,544> bytes;assert(encode(p,bytes));Pair decoded;
    assert(decode(bytes.data(),bytes.size(),decoded) && decoded.model==240);
    Order order;assert(order.complete() && order.expect(decoded) && !order.complete());
    assert(!order.expect(decoded));cruisn::zeus_model::Quad output;output.state[0]=999;
    auto bad=p.original;bad.state[2]=1;
    assert(!order.consume(bad,output) && output.state[0]==999 && order.pending());
    assert(order.consume(p.original,output) && output.state[9]==28 && !order.complete());
    auto later=p;later.model=241;
    assert(!order.expect(later));p.index=1;assert(order.expect(p));
    assert(order.consume(p.original,output) && order.complete());
    assert(!order.expect(p));assert(order.expect(later));
    assert(!decode(bytes.data(),543,decoded));bytes[20]=1;assert(!decode(bytes.data(),544,decoded));
    for(unsigned field:{0u,1u,2u,9u,11u,12u,16u}) {
        auto invalid=p;invalid.replacement.state[field]^=1;
        assert(!valid(invalid));
    }
    auto invalid=p;invalid.replacement.vertices[0][0]=1;assert(!valid(invalid));
    p.original.state[0]=0;p.replacement.state[0]=0;assert(valid(p)); // explicit live record convention
    std::cout<<"PASS original/private pair ABI, immutable geometry/state and ordered single consumption\n";
}
