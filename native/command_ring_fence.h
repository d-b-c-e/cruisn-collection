// SPDX-License-Identifier: BSD-3-Clause
// Observe an existing single-producer command ring. Never inserts a command,
// waits for the consumer or changes guest memory. Caller guarantees no overrun.
#pragma once
#include <cstdint>
namespace cruisn {
template<uint32_t Base,uint32_t Size> class CommandRingFence
{
    static_assert(Size>1 && uint64_t(Base)+Size<=UINT64_C(0x100000000),"ring address range");
    uint32_t cursor_=0,target_=0,remaining_=0;
    bool pending_=false;
    static bool valid(uint32_t p){return p>=Base && uint64_t(p)<uint64_t(Base)+Size;}
public:
    enum class Status { invalid,pending,ready };
    bool pending() const{return pending_;}
    uint32_t remaining() const{return remaining_;}
    uint32_t target() const{return target_;}
    uint32_t cursor() const{return cursor_;}
    Status begin(uint32_t consumer,uint32_t producer,bool parser_empty)
    {
        if(pending_ || !valid(consumer) || !valid(producer))return Status::invalid;
        const uint32_t distance=uint32_t((uint64_t(producer)+Size-consumer)%Size);
        if(!distance && !parser_empty)return Status::invalid;
        cursor_=consumer;target_=producer;remaining_=distance;pending_=distance!=0;
        return pending_?Status::pending:Status::ready;
    }
    // Call AFTER the existing consumer has processed this word and queued its
    // original rendering work. The target must also finish a complete command.
    Status consumed(uint32_t next,bool parser_empty)
    {
        if(!pending_ || !remaining_ || next!=Base+(cursor_-Base+1)%Size)return Status::invalid;
        const bool ready=remaining_==1;
        if(ready && (next!=target_ || !parser_empty))return Status::invalid;
        cursor_=next;--remaining_;pending_=!ready;
        return ready?Status::ready:Status::pending;
    }
};
}
