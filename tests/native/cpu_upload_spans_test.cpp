#include "cpu_upload_spans.h"
#include <cassert>
#include <tuple>
#include <vector>
int main() {
    cruisn::cpu_upload_spans spans(8,3);
    using Span=std::tuple<unsigned,unsigned,unsigned>;
    std::vector<Span> uploaded;
    auto flush=[&]() { spans.flush([&](unsigned p,unsigned at,unsigned n){uploaded.emplace_back(p,at,n);}); };
    spans.mark(0,2,2);spans.mark(0,3,3);spans.mark(0,7,3);spans.mark(1,21,8);
    assert(spans.pending(0) && spans.mask(0)[2] && !spans.mask(0)[6]);
    flush();
    assert((uploaded==std::vector<Span>{{0,2,4},{0,7,1},{0,8,2},{1,21,3}}));
    uploaded.clear();flush();assert(uploaded.empty());
    assert(!spans.pending(0) && !spans.pending(1));
    spans.mark(1,4,1);spans.mark(0,24,1);spans.mark(0,23,0);spans.mark(2,0,1);
    flush();assert((uploaded==std::vector<Span>{{1,4,1}}));
    // All repeated startup writes become one upload per row, preserving holes.
    uploaded.clear();for(int pass=0;pass<8;++pass)for(unsigned at=0;at<24;++at)spans.mark(0,at,1);
    flush();assert((uploaded==std::vector<Span>{{0,0,8},{0,8,8},{0,16,8}}));
    spans.mark(1,1,4);spans.clear(1);
    assert(!spans.pending(1) && !spans.mask(1)[1] && !spans.mask(1)[4]);
}
