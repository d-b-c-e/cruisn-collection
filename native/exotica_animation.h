// SPDX-License-Identifier: BSD-3-Clause
// Exotica2.4 model-frame sequencer. No guest allocation, RNG, writes or drawing.
// Caller owns node lifetime, table identity and the number/order of updates.
#pragma once
#include <cstdint>
#include <vector>

namespace cruisn { namespace exotica_animation {
struct Sequence
{
    uint32_t period=0,random_extent=0;
    std::vector<uint32_t> models;
};
struct State
{
    uint32_t remaining=0,cursor=0,model=0; // cursor==models.size() names the sentinel
};
inline bool descriptor(uint32_t word)
{return (word&0xffffff)>=0xa00000;}

inline bool decode(uint32_t header,const std::vector<uint32_t> &words,Sequence &out)
{
    out=Sequence();
    if(words.size()<2 || words.size()>257)return false;
    const uint32_t count=uint32_t(words.size()-1),period=header>>24,random=(header>>16)&255;
    // The observed tables encode their length both in the header and terminator.
    if(!period || (header&65535)!=count || random>count || words.back()!=uint32_t(0-count))return false;
    for(uint32_t i=0;i<count;++i)
        if(words[i]>>24 || !descriptor(words[i]))return false;
    out.period=period;out.random_extent=random;out.models.assign(words.begin(),words.end()-1);
    return true;
}

inline bool step(const Sequence &sequence,const State &before,State &after)
{
    after=State();
    if(!sequence.period || sequence.period>255 || sequence.models.empty() || sequence.models.size()>256 ||
        before.cursor>sequence.models.size() || before.remaining>sequence.period || !descriptor(before.model))return false;
    if(before.remaining>1)
    {after=before;--after.remaining;return true;}
    // E8D3 fetches at the cursor; a negative terminator resets to the first entry.
    const uint32_t index=before.cursor==sequence.models.size()?0:before.cursor;
    if(sequence.models[index]>>24 || !descriptor(sequence.models[index]))return false;
    after.remaining=sequence.period;after.cursor=index+1;after.model=sequence.models[index];
    return true;
}
} }
