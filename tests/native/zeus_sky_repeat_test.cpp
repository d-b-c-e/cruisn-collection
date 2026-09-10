#include "zeus_sky_repeat.h"
#include <cassert>
#include <limits>
std::vector<cruisn::zeus_sky_tile> strip(float start)
{
    std::vector<cruisn::zeus_sky_tile> rows;
    for (unsigned i=0;i<14;++i) {
        cruisn::zeus_sky_tile q;
        q.state[0]=(i%6)+1; q.state[7]=52; q.state[13]=511; q.state[14]=399;
        const float left=start+i*256,right=left+256;
        q.v={{{{left,-15,123,0,0,1}},{{right,-15,123,256,0,1}},
              {{right,220,123,256,256,1}},{{left,220,123,0,256,1}}}};
        rows.push_back(q);
    }
    return rows;
}
int main()
{
    auto a=strip(-3020); auto p=cruisn::zeus_sky_repeat(a,88);
    assert(p.accepted && p.period==1536 && p.comparisons==16 && p.copies.size()==1);
    auto c=p.copies[0]; assert(a[c.index].v[0][0]+c.shift==564 && a[c.index].v[1][0]+c.shift==820);
    auto left=strip(-40);p=cruisn::zeus_sky_repeat(left,88);
    assert(p.accepted && p.copies.size()==1);c=p.copies[0];assert(left[c.index].v[1][0]+c.shift==-40);
    assert(cruisn::zeus_sky_repeat(strip(-500),88).copies.empty());
    assert(!cruisn::zeus_sky_repeat(a,0).accepted && !cruisn::zeus_sky_repeat(a,121).accepted);
    for (unsigned mutation=0;mutation<6;++mutation) {
        auto b=a;
        if (mutation==0) b[7].v[0][3]+=.25f; // one repeated tile has different UVs
        if (mutation==1) b[7].v[0][0]+=1; // a seam/gap cannot be inferred away
        if (mutation==2) b[7].v[2][2]+=1; // perspective foreground
        if (mutation==3) b[7].state[9]=400; // mixed pages
        if (mutation==4) b[7].v[0][0]=std::numeric_limits<float>::quiet_NaN();
        if (mutation==5) b[7].state[7]=28; // ordinary depth-tested geometry
        assert(!cruisn::zeus_sky_repeat(b,88).accepted);
    }
    // State after upstream depth-floor selection is still a background clear.
    for (auto &q:a) q.state[7]|=512;
    assert(cruisn::zeus_sky_repeat(a,88).accepted);
}
