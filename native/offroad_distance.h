// SPDX-License-Identifier: BSD-3-Clause
// Off Road1.63 global far/clipping/projection controls. No guest writes.
#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace cruisn { namespace offroad_distance {
struct word { uint32_t address,value; };
constexpr uint32_t table_base=0xcb0fc8, original_far=47296, original_clip=63680;
constexpr int32_t minimum_index=-4096;
constexpr word projection_sites[]={
    {0x1c44,0x0a414000},
    {0x1c46,0x0a404000},
    {0x1c4e,0x0a424000},
    {0x1d1c,0x24e14005},
    {0x1d1f,0x24e14005},
    {0x1d23,0x24e14005},
    {0x1d26,0x24e14085},
    {0x1d2a,0x24e14005},
    {0x1d2d,0x24e14005},
    {0x1d31,0x24e14085},
    {0x1d34,0x24e14005},
    {0x1d38,0x24e14005},
    {0x1daf,0x24e1400b},
    {0x1db0,0x800f40c3},
    {0x1dc4,0x07474000},
    {0x1e2e,0x24e1400b},
    {0x1e2f,0x800f40c3},
    {0x1e50,0x24e1400b},
    {0x1e51,0x800f40c3},
    {0x1e90,0x24e1400b},
    {0x1e91,0x800f40c3},
    {0x1ed1,0x24e1400b},
    {0x1ed2,0x800f40c3},
    {0x1f11,0x24e1400b},
    {0x1f12,0x800f40c3},
    {0x1f52,0x24e1400b},
    {0x1f53,0x800f40c3},
    {0x22e2,0x24e14002},
    {0x22e5,0x24e14002},
    {0x22e9,0x24e14002},
    {0x22ec,0x24e14002},
    {0x230f,0x24e1400b},
    {0x2310,0x800f40c3},
    {0x2342,0x24e14002},
    {0x2345,0x24e14002},
    {0x2349,0x24e14002},
    {0x234c,0x24e14002},
    {0x236f,0x24e1400b},
    {0x2370,0x800f40c3},
    {0x239c,0x07404000},
    {0x2562,0x24e14002},
    {0x2565,0x24e14002},
    {0x2569,0x24e14002},
    {0x256c,0x24e14002},
    {0x257e,0x0a414000},
    {0x2580,0x0a404000},
    {0x2588,0x0a424000},
    {0x25cf,0x24e1400b},
    {0x25d0,0x800f40c3},
    {0x27ae,0x24e1400b},
    {0x27af,0x800f40c3},
    {0x2822,0x24e14002},
    {0x2825,0x24e14002},
    {0x2829,0x24e14002},
    {0x282c,0x24e14002},
    {0x284f,0x24e1400b},
    {0x2850,0x800f40c3},
    {0xe035,0x07404000},
    {0xe221,0x07424000},
};
constexpr word ceiling_sites[]={{0x1c42,0x04b111a8},{0x1c43,0x54b111a8},
    {0x1e8e,0x04b111a8},{0x1e8f,0x54b111a8},{0x1f0f,0x04b111a8},{0x1f10,0x54b111a8},
    {0x239a,0x04b111a8},{0x239b,0x54b111a8},{0x257c,0x04b111a8},{0x257d,0x54b111a8},
    {0xe033,0x04b111a8},{0xe034,0x54b111a8}};
constexpr word guards[]={{0x1c35,0x0420b724},{0x1c36,0x6a2a066c},
    {0x1df8,0x0420b725},{0x1e9d,0x0420b725},
    {0x111a7,table_base},{0x111a8,63679},{0x11221,0x0f38c000},{0x11223,0x0f78c000},
    {0x1820,0x07201221},{0x1821,0x1420b724},{0x1822,0x07201223},{0x1823,0x1420b725}};
inline bool valid_multiplier(uint32_t multiplier) { return multiplier>=1 && multiplier<=3; }
inline uint32_t maximum_index(uint32_t multiplier) { return valid_multiplier(multiplier) ? original_clip*multiplier-1 : 0; }
inline uint32_t positive_c31(double value)
{
    float f=float(value);uint32_t bits;std::memcpy(&bits,&f,sizeof(bits));
    return (((uint32_t((bits>>23)&255)-127)&255)<<24)|(bits&0x7fffff);
}
inline uint32_t far_word(uint32_t multiplier) { return positive_c31(original_far*multiplier); }
inline uint32_t clip_word(uint32_t multiplier) { return positive_c31(original_clip*multiplier); }
inline uint32_t reciprocal(int32_t index)
{
    if (index<minimum_index || index>int32_t(maximum_index(3))) return 0;
    uint64_t numerator=index<503 ? uint64_t(1007-index)*100000000 : 50400000000ULL;
    uint64_t denominator=index<503 ? 504 : uint32_t(index+1);
    uint64_t q=numerator/denominator,r=numerator%denominator;
    // The original table uses eight decimal places, exact ties to even. Binary
    // round(float,8) disagrees at two measured entries; integer rounding does not.
    if (2*r>denominator || (2*r==denominator && (q&1))) ++q;
    return positive_c31(double(q)/100000000.0);
}
template <size_t N> inline bool words_match(const uint32_t *ram,const word (&sites)[N])
{ for (auto const &w:sites) if (ram[w.address]!=w.value) return false;return true; }
inline bool code_matches(const uint32_t *ram,size_t words)
{ return ram && words>=0x20000 && words_match(ram,guards) && words_match(ram,projection_sites) && words_match(ram,ceiling_sites); }
inline const word *projection_site(uint32_t pc)
{ for (auto const &w:projection_sites) if (pc==w.address+1) return &w;return nullptr; }
inline bool ceiling_pc(uint32_t pc)
{ for (auto const &w:ceiling_sites) if (pc==w.address+1) return true;return false; }
inline bool indexed_read(uint32_t offset,uint32_t ar0,uint32_t ir0)
{ return ar0==table_base && int64_t(offset)==int64_t(table_base)+int32_t(ir0); }
inline bool far_pc(uint32_t pc) { return pc==0x1c36; }
inline bool clip_pc(uint32_t pc) { return pc==0x1df9 || pc==0x1e9e; }
} }
