// SPDX-License-Identifier: BSD-3-Clause
// Global World 2.4/2.5 distance experiment. No model or level allowlist.
#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace cruisn { namespace world_distance {
constexpr uint32_t original_far=80000, reciprocal_base=0xb66f, first_extra=5000;
constexpr uint32_t maximum_lead=12;
struct word { uint32_t address, value; };
struct layout { uint32_t table, selected_model, pending_limit, pending_pc; };
constexpr layout v24={0xb66f,0xd4bf,0xd58c,0x7b51};
constexpr layout v25={0xb665,0xd4b9,0xd586,0x7b43};
inline const layout *layout_for_revision(uint32_t revision)
{ return revision==24 ? &v24 : revision==25 ? &v25 : nullptr; }
// Low immediate becomes the chosen maximum reciprocal index.
constexpr word clamps[] = {{0xae,0x04e30000},{0xaf,0x54e30000},
    {0x13a,0x04f20000},{0x13b,0x55720000},{0x14d,0x04f20000},{0x14e,0x55720000},
    {0x199,0x04f20000},{0x19a,0x55720000},{0x677,0x04f20000},{0x678,0x55720000}};
constexpr word projection_sites[] = {{0xb3,0x0741c300},
    {0x142,0x8308820b},{0x146,0x835882c3},{0x151,0xde100382},{0x153,0xde180b82},
    {0x19f,0x24c00182},{0x1a1,0xde180b82},{0x1de,0x8308820b},{0x1e2,0x835882c3},
    {0x1e9,0xde100382},{0x1eb,0xde180b82},{0x21b,0x24c00182},{0x21d,0xde180b82},
    {0x50d,0x24c00182},{0x50f,0xde180b82},{0x67d,0x24c00182},{0x67f,0xde180b82}};

inline bool valid_far(uint32_t far)
{ return far==80000 || far==100000 || far==160000 || far==240000; }
inline uint32_t maximum_index(uint32_t far)
{ return far==original_far ? 4999 : far/16; }
inline bool projection_pc(uint32_t pc)
{
    for (auto const &site:projection_sites) if (site.address+1==pc) return true;
    return false;
}
inline bool code_matches(const uint32_t *ram, size_t words, uint32_t far, uint32_t revision=24)
{
    const auto *profile=layout_for_revision(revision);
    if (!profile || !ram || words<0x20000 || !valid_far(far) || ram[0x40]!=far || ram[0x4d]!=profile->table
        || ram[0x9c]!=(0x15290000|profile->selected_model) || ram[0xa0]!=0x04a30040 || ram[0xa8]!=0x04a30040)
        return false;
    for (auto const &w:clamps) if (ram[w.address]!=(w.value|maximum_index(far))) return false;
    for (auto const &w:projection_sites) if (ram[w.address]!=w.value) return false;
    return true;
}
inline bool pending_matches(const uint32_t *ram, size_t words, uint32_t revision=24)
{
    const auto *profile=layout_for_revision(revision);
    if (!profile || !ram || words<0x20000 || ram[profile->pending_limit]!=11) return false;
    // Independently observed instruction sequences, not an assumed global relocation.
    constexpr word pending24[]={{0x7b50,0x0224d58c},{0x7b51,0x04a4d584},{0x7b58,0x04800004},
        {0x7b59,0x6a290008},{0x7b5c,0x1ae03000},{0x7b5d,0x1540000e},{0x7b61,0x1541c000},
        {0x7b62,0x1528d50b},{0x7b68,0x0840001b},{0x7b69,0x02e0ffff}};
    constexpr word pending25[]={{0x7b42,0x0224d586},{0x7b43,0x04a4d57e},{0x7b4a,0x04800004},
        {0x7b4b,0x6a290008},{0x7b4e,0x1ae03000},{0x7b4f,0x1540000e},{0x7b53,0x1541c000},
        {0x7b54,0x1528d505},{0x7b5a,0x0840001b},{0x7b5b,0x02e0ffff}};
    const word *expected=revision==24 ? pending24 : pending25;
    for (size_t i=0;i<sizeof(pending24)/sizeof(word);++i)
        if (ram[expected[i].address]!=expected[i].value) return false;
    return true;
}
inline uint32_t reciprocal(uint32_t index, uint32_t far)
{
    if (!valid_far(far) || index<first_extra || index>maximum_index(far)) return 0;
    // Existing table entries remain untouched; expand the measured six-decimal
    // far-tail generator in host memory, never into adjacent guest object RAM.
    float value=float(std::floor(512.0/(16*index+1)*1000000+0.5)/1000000);
    uint32_t ieee; std::memcpy(&ieee,&value,sizeof(ieee));
    return ((((ieee>>23)-127)&255)<<24)|(ieee&0x7fffff);
}
} }
