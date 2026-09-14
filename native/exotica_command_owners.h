// SPDX-License-Identifier: BSD-3-Clause
// Exact committed two-word model packets, carried to their ring-consumer boundary.
// No guest writes, model/pose heuristics or inferred source identity. Callers bind
// a ticket to an owned source snapshot at commit and verify the actual FIFO site.
#pragma once
#include <cstdint>
#include <cstddef>
#include <deque>
#include <map>
namespace cruisn { namespace exotica_commands {
struct Ticket { uint64_t epoch=0,id=0;uint32_t end=0,opcode=0,base=0; };
enum class Status { invalid,untracked,matched };
class Owners {
    std::deque<Ticket> m_pending;
    std::map<uint32_t,uint64_t> m_ends;
    uint64_t m_epoch=0,m_last=0;
public:
    static bool cursor(uint32_t p){return p>=0x30000 && p<0x32000;}
    static bool model(uint32_t opcode,uint32_t base) {
        const uint32_t count=opcode&65535;
        const uint64_t block=(base%1024)+((base>>16)%2048)*1024;
        return (opcode&0xffff0000)==0x24860000 && base && count<=0xc800 &&
            block*2+2*(uint64_t(count)+1)<=4*1024*1024;
    }
    size_t pending() const{return m_pending.size();}
    uint64_t epoch() const{return m_epoch;}
    // A frame/page change is not a reset. A new epoch needs a drained queue;
    // silently clearing live tickets could assign an old command to a new owner.
    bool reset(uint64_t epoch) {
        if(!epoch || epoch<=m_epoch || !m_pending.empty())return false;
        m_epoch=epoch;m_last=0;return true;
    }
    bool submit(uint64_t id,uint32_t end,uint32_t opcode,uint32_t base) {
        if(!m_epoch || !id || id<=m_last || !cursor(end) || !model(opcode,base) ||
            m_pending.size()>=4096 || m_ends.count(end))return false;
        Ticket t;t.epoch=m_epoch;t.id=id;t.end=end;t.opcode=opcode;t.base=base;
        m_pending.push_back(t);m_ends.emplace(end,id);m_last=id;return true;
    }
    // At the actual device model boundary the caller supplies the consumed ring
    // end and complete opcode/base, not just a visually matching model address.
    // Untracked commands are expected. A later owned ticket cannot pass an earlier
    // one, and a mismatch never removes the pending owner or changes output.
    Status consume(uint32_t end,uint32_t opcode,uint32_t base,Ticket &output) {
        if(!m_epoch || !cursor(end))return Status::invalid;
        const auto found=m_ends.find(end);
        if(found==m_ends.end())return Status::untracked;
        const auto &t=m_pending.front();
        if(t.end!=end || t.id!=found->second || t.opcode!=opcode || t.base!=base)return Status::invalid;
        output=t;m_ends.erase(found);m_pending.pop_front();return Status::matched;
    }
};
} }
