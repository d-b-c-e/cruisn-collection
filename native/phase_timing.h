// SPDX-License-Identifier: BSD-3-Clause
// Opt-in bounded CPU profiling. No file writes or allocations during sampling.
#pragma once
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <vector>
namespace cruisn {
class PhaseTiming {
public:
    enum Phase : uint32_t { source, waiting_build, future_build, future_material,
        active_seal, waiting_ready, active_build, active_material,
        future_stage, future_encode, future_submit, future_commit, phase_count };
    struct Row { uint32_t frame; uint64_t scene; Phase phase; double us; uint64_t units; };
    static constexpr size_t capacity=65536;
private:
    uint32_t m_first=0,m_last=0;
    bool m_configured=false,m_failed=false;
    std::vector<Row> m_rows;
public:
    bool configure(const char *text) {
        if(m_configured)return false;
        m_configured=true;
        if(!text)return true;
        auto number=[](const char *&p,uint32_t &out) {
            uint64_t n=0;
            if(*p<'0' || *p>'9')return false;
            while(*p>='0' && *p<='9') {
                n=n*10+unsigned(*p++-'0');if(n>UINT32_MAX)return false;
            }
            out=uint32_t(n);return true;
        };
        const char *p=text;uint32_t first,last;
        if(!number(p,first) || *p++!=':' || !number(p,last) || *p || !first || last<first || last-first>=2000)return false;
        m_rows.reserve(capacity);m_first=first;m_last=last;return true;
    }
    bool enabled()const{return m_first!=0;}
    bool contains(uint32_t frame)const{return enabled() && frame>=m_first && frame<=m_last;}
    uint32_t first()const{return m_first;}
    uint32_t last()const{return m_last;}
    size_t size()const{return m_rows.size();}
    bool good(uint32_t final_frame)const {
        return enabled() && !m_failed && !m_rows.empty() && final_frame>=m_last;
    }
    void add(uint32_t frame,uint64_t scene,Phase phase,double us,uint64_t units=0) {
        if(!contains(frame))return;
        if(!scene || phase>=phase_count || !std::isfinite(us) || us<0 || m_rows.size()==capacity) {m_failed=true;return;}
        m_rows.push_back({frame,scene,phase,us,units});
    }
    bool write(FILE *file,uint32_t final_frame)const {
        if(!file || !enabled())return false;
        static const char *names[]={"source","waiting_build","future_build","future_material",
            "active_seal","waiting_ready","active_build","active_material",
            "future_stage","future_encode","future_submit","future_commit"};
        if(std::fprintf(file,"frame,scene,phase,microseconds,units\n")<0)return false;
        for(const auto &r:m_rows)
            if(std::fprintf(file,"%u,%llu,%s,%.3f,%llu\n",r.frame,(unsigned long long)r.scene,
                names[r.phase],r.us,(unsigned long long)r.units)<0)return false;
        return good(final_frame) && !std::ferror(file);
    }
};
}
