#include "zeus_margin_clear.h"
#include <cassert>
#include <climits>
#include <utility>
int main()
{
    for (uint32_t page : {0u,400u}) {
        auto legacy=cruisn::zeus_margin_clear((page+216)*512,184*512,false);
        assert(legacy.row==page+216 && legacy.count==184 && !legacy.expanded);
        auto full=cruisn::zeus_margin_clear((page+216)*512,184*512,true);
        assert(full.row==page && full.count==400 && full.expanded);
        // Every row-aligned subrange stays on its own page, including edges.
        for (uint32_t start=0;start<400;++start) for (uint32_t count=1;count<=400-start;++count) {
            auto s=cruisn::zeus_margin_clear((page+start)*512,count*512,true);
            assert(s.row==page && s.count==400);
            assert(s.expanded==(start!=0 || count!=400));
        }
    }
    for (auto pair : {std::pair<uint32_t,uint32_t>{399*512,2*512},
            {799*512,2*512},{800*512,100*512},{216*512+1,184*512},
            {216*512,184*512+1},{0,0},{0,1024*512},{0,UINT_MAX}}) {
        auto a=cruisn::zeus_margin_clear(pair.first,pair.second,false);
        auto b=cruisn::zeus_margin_clear(pair.first,pair.second,true);
        assert(a.row==b.row && a.count==b.count && !b.expanded);
    }
    auto wrapped=cruisn::zeus_margin_clear((1024+616)*512,184*512,true);
    assert(wrapped.row==400 && wrapped.count==400 && wrapped.expanded);
}
