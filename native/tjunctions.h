// Experimental host geometry correction; never use for native hardware exactness.
#pragma once
#include <array>
#include <cstdint>
#include <cmath>
#include <map>
#include <vector>

namespace cruisn {
using JoinVertex = std::array<int, 4>; // x, y, u, v
using JoinMaterial = std::array<int, 4>;
using JoinKey = std::pair<JoinMaterial, JoinVertex>;
struct JoinEdge { JoinVertex end; size_t quad; };
struct JoinOccurrence { size_t quad; int vertex; };
struct JoinCandidate { double x,y; JoinVertex a,b; };
struct JoinResult { std::vector<std::array<float,8>> positions; size_t aligned = 0; };

template<class GetQuad> JoinResult align_tjunctions(size_t count, GetQuad get)
{
    JoinResult result;
    result.positions.resize(count);
    std::map<JoinKey, std::vector<JoinEdge>> edges;
    std::map<JoinKey, std::vector<JoinOccurrence>> occurrences;
    for (size_t q=0; q<count; ++q) {
        const auto *d = get(q);
        for (int i=0; i<8; ++i) result.positions[q][i] = float(int16_t(d[2+i]));
        if ((d[0] & 0x2f00) != 0x100) continue;
        JoinMaterial material{{d[0],d[1],d[14],d[15]}};
        JoinVertex v[4];
        for (int i=0;i<4;++i) v[i] = {{int16_t(d[2+i*2]),int16_t(d[3+i*2]),d[10+i]&255,d[10+i]>>8}};
        for (int i=0;i<4;++i) {
            occurrences[{material,v[i]}].push_back({q,i});
            const auto &b=v[(i+1)%4];
            if (v[i][0]!=b[0] || v[i][1]!=b[1]) edges[{material,v[i]}].push_back({b,q});
        }
    }
    std::map<JoinKey,std::vector<JoinCandidate>> candidates;
    for (const auto &entry: edges) {
        const auto &material=entry.first.first;
        const auto &a=entry.first.second;
        for (const auto &ab:entry.second) {
            const auto &b=ab.end;
            const double dx=b[0]-a[0],dy=b[1]-a[1],length2=dx*dx+dy*dy;
            if (length2<64) continue;
            auto outgoing=edges.find({material,b});
            if (outgoing==edges.end()) continue;
            for (const auto &bp:outgoing->second) {
                const auto &p=bp.end;
                if (bp.quad==ab.quad || p==a) continue;
                auto closing=edges.find({material,p});
                if (closing==edges.end()) continue;
                bool closed=false;
                for (const auto &pa:closing->second)
                    if (pa.end==a && pa.quad!=ab.quad && pa.quad!=bp.quad) closed=true;
                if (!closed) continue;
                const double t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length2;
                if (!(t>.01 && t<.99)) continue;
                const double x=a[0]+t*dx,y=a[1]+t*dy;
                const double distance=std::hypot(x-p[0],y-p[1]);
                if (!(distance>.001 && distance<=.75)) continue;
                if (std::abs(a[2]+t*(b[2]-a[2])-p[2])>.75 || std::abs(a[3]+t*(b[3]-a[3])-p[3])>.75) continue;
                candidates[{material,p}].push_back({x,y,a,b});
            }
        }
    }
    for (const auto &entry:candidates) {
        const auto &first=entry.second.front();
        bool ambiguous=false;
        for (const auto &c:entry.second) {
            if (candidates.count({entry.first.first,c.a}) || candidates.count({entry.first.first,c.b}) ||
                std::hypot(c.x-first.x,c.y-first.y)>.001) ambiguous=true;
        }
        if (ambiguous) continue;
        for (const auto &where:occurrences[entry.first]) {
            result.positions[where.quad][where.vertex*2]=float(first.x);
            result.positions[where.quad][where.vertex*2+1]=float(first.y);
        }
        ++result.aligned;
    }
    return result;
}
}
