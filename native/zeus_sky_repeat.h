// license:BSD-3-Clause
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>

namespace cruisn {
struct zeus_sky_tile {
    // Original quad fields2..16: texture/material, page/scale, and clip.
    std::array<uint32_t,15> state{};
    std::array<std::array<float,6>,4> v{};
};
struct zeus_sky_copy { unsigned index; float shift; };
struct zeus_sky_plan {
    bool accepted=false;
    float period=0;
    unsigned comparisons=0;
    std::vector<zeus_sky_copy> copies;
};
inline bool zeus_sky_candidate(const zeus_sky_tile &q)
{
    if ((q.state[7]&~512u)!=52 || q.state[10] ||
        (q.state[9]!=0 && q.state[9]!=400) || q.state[11] || q.state[12] ||
        q.state[13]!=511 || q.state[14]!=399) return false;
    for (auto const &v:q.v) for (float f:v) if (!std::isfinite(f) || std::abs(f)>1e12f) return false;
    for (auto const &v:q.v) if (v[2]!=q.v[0][2] || v[5]!=q.v[0][5]) return false;
    return q.v[0][2]>0 && q.v[0][5]>0 &&
        std::abs(q.v[0][0]-q.v[3][0])<.002f && std::abs(q.v[1][0]-q.v[2][0])<.002f &&
        std::abs(q.v[0][1]-q.v[1][1])<.002f && std::abs(q.v[2][1]-q.v[3][1])<.002f &&
        q.v[1][0]-q.v[0][0]>1 && q.v[1][0]-q.v[0][0]<4096 &&
        q.v[2][1]-q.v[0][1]>1 && q.v[2][1]-q.v[0][1]<2048;
}
inline bool zeus_sky_same(const zeus_sky_tile &a,const zeus_sky_tile &b)
{
    if (a.state!=b.state) return false;
    for (unsigned i=0;i<4;++i) for (unsigned j=1;j<6;++j) if (a.v[i][j]!=b.v[i][j]) return false;
    return std::abs((a.v[1][0]-a.v[0][0])-(b.v[1][0]-b.v[0][0]))<.002f;
}

// Recognize repetition already present in a contiguous, coplanar background.
// Copy a proven tile at unchanged scale/UVs only beyond its existing extent.
// The caller owns palette/upload lifetime and emits before foreground geometry.
// No model IDs, texture addresses, track names or fixed panorama period.
inline zeus_sky_plan zeus_sky_repeat(const std::vector<zeus_sky_tile> &tiles,unsigned margin)
{
    zeus_sky_plan fail;
    if (tiles.size()<8 || tiles.size()>64 || !margin || margin>120) return fail;
    struct band { float top,bottom,left,right; std::vector<unsigned> ids; };
    std::vector<band> bands;
    for (unsigned i=0;i<tiles.size();++i) {
        auto const &q=tiles[i];
        if (!zeus_sky_candidate(q) || q.state[9]!=tiles[0].state[9] ||
            q.v[0][2]!=tiles[0].v[0][2] || q.v[0][5]!=tiles[0].v[0][5]) return fail;
        auto found=std::find_if(bands.begin(),bands.end(),[&](const band &b){return b.top==q.v[0][1] && b.bottom==q.v[2][1];});
        if (found==bands.end()) { bands.push_back({q.v[0][1],q.v[2][1],0,0,{i}}); if (bands.size()>4) return fail; }
        else found->ids.push_back(i);
    }
    for (auto &b:bands) {
        std::sort(b.ids.begin(),b.ids.end(),[&](unsigned a,unsigned c){return tiles[a].v[0][0]<tiles[c].v[0][0];});
        b.left=tiles[b.ids.front()].v[0][0]; b.right=tiles[b.ids.back()].v[1][0];
        if (b.left>0 || b.right<512 || b.right-b.left<1024) return fail;
        for (unsigned i=1;i<b.ids.size();++i)
            if (std::abs(tiles[b.ids[i-1]].v[1][0]-tiles[b.ids[i]].v[0][0])>.02f) return fail;
    }
    std::vector<float> candidates;
    for (unsigned i=0;i<tiles.size();++i) for (unsigned j=0;j<i;++j) {
        const float d=std::abs(tiles[i].v[0][0]-tiles[j].v[0][0]);
        if (d>512 && d<16384 && zeus_sky_same(tiles[i],tiles[j])) candidates.push_back(std::round(d*100)/100);
    }
    std::sort(candidates.begin(),candidates.end());
    candidates.erase(std::unique(candidates.begin(),candidates.end()),candidates.end());
    if (candidates.size()>64) return fail;
    zeus_sky_plan result;
    for (float period:candidates) {
        unsigned checked=0; bool bad=false;
        for (unsigned i=0;i<tiles.size() && !bad;++i) for (float shift : {-period,period}) {
            unsigned matches=0,match=0;
            for (unsigned j=0;j<tiles.size();++j)
                if (std::abs((tiles[j].v[0][0]-tiles[i].v[0][0])-shift)<.02f &&
                    std::abs(tiles[j].v[0][1]-tiles[i].v[0][1])<.002f) { ++matches; match=j; }
            if (matches) { ++checked; if (matches!=1 || !zeus_sky_same(tiles[i],tiles[match])) { bad=true; break; } }
        }
        if (!bad && checked>=tiles.size()) { result.accepted=true; result.period=period; result.comparisons=checked; break; }
    }
    if (!result.accepted) return fail;
    for (auto const &b:bands) {
        if (b.bottom<=0 || b.top>=400) continue;
        for (unsigned side=0;side<2;++side) {
            if (side ? b.right>=512+margin : b.left<=-float(margin)) continue;
            const float target=side ? b.right : b.left;
            bool found=false;
            // Use submission order to make equivalent copies reproducible.
            for (unsigned i=0;i<tiles.size() && !found;++i) {
                auto const &q=tiles[i];
                if (q.v[0][1]!=b.top || q.v[2][1]!=b.bottom) continue;
                const float edge=side ? q.v[0][0] : q.v[1][0];
                const float multiple=std::round((target-edge)/result.period);
                if (!multiple || std::abs(edge+multiple*result.period-target)>=.02f) continue;
                const float shift=target-edge,lo=q.v[0][0]+shift,hi=q.v[1][0]+shift;
                if (side ? (hi<512+margin || lo<512) : (lo>-float(margin) || hi>0)) return fail;
                result.copies.push_back({i,shift}); found=true;
            }
            if (!found) return fail;
        }
    }
    return result;
}
}
