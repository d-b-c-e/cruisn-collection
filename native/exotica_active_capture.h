// SPDX-License-Identifier: BSD-3-Clause
// own current list operands and recheck ownership before submission.
#pragma once
#include "exotica_active.h"
namespace cruisn { namespace exotica_active {
struct OwnedList {
    uint32_t entry=0,head=0;
    Parameters parameters;
    std::vector<Source> sources;
    std::vector<Decision> decisions;
};
struct Selection {
    Parameters parameters;
    std::vector<Source> sources;
};
struct Selections {
    std::array<Selection,4> lists;
    size_t objects=0,candidates=0,already_submitted=0;
};
inline bool same_decision(const Decision &a,const Decision &b) {
    return a.stock==b.stock && a.wide==b.wide && a.flags==b.flags &&
        a.index==b.index && a.factor==b.factor && a.depth==b.depth &&
        a.translation==b.translation && a.margin_candidate==b.margin_candidate;
}
class Capture {
    std::vector<OwnedList> m_lists;
    std::set<uint32_t> m_slots;
public:
    void clear(){m_lists.clear();m_slots.clear();}
    size_t lists()const{return m_lists.size();}
    template<class Read> bool capture(uint32_t entry,uint32_t head,const Parameters &p,Read read) {
        if(entry!=0xbbb5+m_lists.size() || m_lists.size()==4)return false;
        OwnedList list;list.entry=entry;list.head=head;list.parameters=p;
        if(!read_list(entry,head,read,list.sources) || list.sources.size()>max_objects-m_slots.size())return false;
        auto slots=m_slots;
        for(const auto &s:list.sources) {
            Decision d;
            if(!slots.insert(s.source).second || !classify(s,p,read,d))return false;
            list.decisions.push_back(d);
        }
        m_slots=std::move(slots);m_lists.push_back(std::move(list));return true;
    }
    // Caller must also check the captured camera/view/setup dependencies at its
    // actual device fence. This helper owns lists and rechecks their render words
    // and projection factors; it does not observe device or GL completion.
    template<class Read> bool finish(Read read,const std::set<uint32_t> &submitted,Selections &out)const {
        if(m_lists.size()!=4)return false;
        Selections selected;
        for(size_t i=0;i<4;++i) {
            const auto &list=m_lists[i];std::vector<Source> current;
            if(read(list.entry)!=list.head || !read_list(list.entry,list.head,read,current) ||
                current.size()!=list.sources.size())return false;
            auto &result=selected.lists[i];result.parameters=list.parameters;
            for(size_t j=0;j<current.size();++j) {
                const auto &owned=list.sources[j];const auto &now=current[j];
                if(owned.source!=now.source)return false;
                for(size_t k=0;k<31;++k)
                    if(k!=20 && owned.words[k]!=now.words[k])return false;
                // Offset20 is the original cull scratch result. No state/model
                // assembly reads it; every actual render field remains checked.
                Decision d;
                if(!classify(now,list.parameters,read,d) || !same_decision(d,list.decisions[j]))return false;
                ++selected.objects;
                if(!d.margin_candidate)continue;
                ++selected.candidates;
                if(submitted.count(owned.source)){++selected.already_submitted;continue;}
                Source source=owned;source.words[15]=d.flags;
                result.sources.push_back(source);
            }
        }
        out=std::move(selected);return true;
    }
};
} }
