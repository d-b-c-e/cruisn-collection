// SPDX-License-Identifier: BSD-3-Clause
// Host-only page write notifications. Clear only after the complete owned update commits.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>
namespace cruisn {
template<std::size_t Bytes,std::size_t PageSize> class WrittenPages {
    static_assert(Bytes && PageSize && Bytes%PageSize==0,"page dimensions");
    static_assert(Bytes/PageSize<=UINT32_MAX,"page index width");
    std::array<bool,Bytes/PageSize> marked_{};
public:
    // Invalid spans never alter the pending set. Mark after an actual write.
    bool mark(std::size_t offset,std::size_t size) {
        if(!size || offset>=Bytes || size>Bytes-offset)return false;
        for(auto i=offset/PageSize;i<=(offset+size-1)/PageSize;++i)marked_[i]=true;
        return true;
    }
    void mark_all(){marked_.fill(true);}
    void clear(){marked_.fill(false);}
    std::vector<uint32_t> pages() const {
        std::vector<uint32_t> result;
        for(std::size_t i=0;i<marked_.size();++i)if(marked_[i])result.push_back(uint32_t(i));
        return result;
    }
};
}
