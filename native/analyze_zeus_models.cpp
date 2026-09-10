// SPDX-License-Identifier: BSD-3-Clause
// Compare independent read-only model decoding with original ordered Zeus quads.
#include "zeus_model.h"
#include <fstream>
#include <iostream>
#include <string>
struct Header
{
    uint32_t version,frame,id,base,count,quad_size,system,first_quad;
    uint32_t last_quad,ucode,palette,texture,yscale,zoffset,raw_words,reserved;
    double time;
    float matrix[9],translation[4],light[3];
    uint32_t regs[128],render[80];
};
static_assert(sizeof(Header)==968,"Zeus source header layout");
int main(int argc,char **argv)
{
    using namespace cruisn::zeus_model;
    if(argc!=3 && argc!=4)return 2;
    std::ofstream report;if(argc==4)report.open(argv[3]);
    if(argc==4 && !report)return 2;
    auto fail=[&](const char *reason,uint32_t id){
        const std::string message="{\"passed\":false,\"error\":\""+std::string(reason)+"\",\"model\":"+std::to_string(id)+"}\n";
        std::cout<<message;if(report)report<<message;return 1;};
    std::ifstream source(argv[1],std::ios::binary),records(argv[2],std::ios::binary);
    if(!source || !records)return fail("missing capture",0);
    std::vector<Quad> quads;uint64_t bytes=0;
    while(true)
    {
        uint32_t p[2];records.read(reinterpret_cast<char *>(p),8);
        if(!records){if(records.eof() && records.gcount()==0)break;return fail("truncated projected prefix",0);}
        bytes+=8+p[1];if(bytes>64*1024*1024 || p[0]<1 || p[0]>4 ||
            p[1]!=(p[0]==1?260U:p[0]==2?1024U:p[0]==3?16U:24U))return fail("invalid projected record",0);
        if(p[0]==1)
        {
            Quad q;if(!records.read(reinterpret_cast<char *>(&q),sizeof(q)))return fail("truncated projected quad",0);
            if(q.state[1]<3 || q.state[1]>8)return fail("invalid projected vertex count",0);
            quads.push_back(q);
        }
        else{records.ignore(p[1]);if(!records)return fail("truncated projected state",0);}
    }
    if(quads.empty())return fail("empty projected stream",0);
    bytes=0;unsigned models=0,covered=0,polygons=0,near=0,backfaces=0,clipped=0,writes=0;
    uint32_t last=0,frame=0;double time=-1;
    while(true)
    {
        uint32_t p[2];source.read(reinterpret_cast<char *>(p),8);
        if(!source){if(source.eof() && source.gcount()==0)break;return fail("truncated source prefix",models+1);}
        bytes+=8+p[1];if(bytes>64*1024*1024 || p[0]!=0x31534d5a || p[1]<sizeof(Header) ||
            p[1]>sizeof(Header)+8*(0xc800+1) || ++models>4096)return fail("invalid source record",models);
        Header h;if(!source.read(reinterpret_cast<char *>(&h),sizeof(h)))return fail("truncated source header",models);
        const uint32_t block=h.base%1024+((h.base>>16)%2048)*1024;
        if(h.id!=models || h.version!=1 || h.system!=1 || h.reserved || h.zoffset || h.count>0xc800 ||
            h.raw_words!=(h.base?2*(h.count+1):0) || p[1]!=sizeof(h)+4*h.raw_words ||
            uint64_t(block)*2+h.raw_words>1024*2048*2 || h.first_quad<last || h.last_quad<h.first_quad ||
            h.last_quad>quads.size() || !std::isfinite(h.time) || h.time<time || h.frame<frame)
            return fail("invalid source identity/state/ownership",models);
        std::vector<uint32_t> words(h.raw_words);
        if(!source.read(reinterpret_cast<char *>(words.data()),4*words.size()))return fail("truncated model words",models);
        Context c;c.frame=h.frame;c.quad_size=h.quad_size;c.texture=h.texture;c.yscale=h.yscale;
        std::copy(h.matrix,h.matrix+9,c.matrix.begin());std::copy(h.translation,h.translation+3,c.translation.begin());
        std::copy(h.regs,h.regs+128,c.regs.begin());std::copy(h.render,h.render+80,c.render.begin());
        Result r;if(!decode(words,c,r))return fail("unsupported or invalid model",models);
        if(r.quads.size()!=h.last_quad-h.first_quad)return fail("projected count mismatch",models);
        for(size_t i=0;i<r.quads.size();++i)
            if(std::memcmp(&r.quads[i],&quads[h.first_quad+i],sizeof(Quad)))return fail("ordered quad/state mismatch",models);
        covered+=r.quads.size();polygons+=r.polygons;near+=r.near_rejected;
        backfaces+=r.backfaces;clipped+=r.near_clipped;writes+=r.register_writes;
        last=h.last_quad;time=h.time;frame=h.frame;
    }
    if(!models || !covered)return fail("empty model coverage",0);
    const std::string result="{\"passed\":true,\"models\":"+std::to_string(models)+
        ",\"covered_quads\":"+std::to_string(covered)+",\"total_quads\":"+std::to_string(quads.size())+
        ",\"polygons\":"+std::to_string(polygons)+",\"near_rejected\":"+std::to_string(near)+
        ",\"backfaces\":"+std::to_string(backfaces)+",\"near_clipped\":"+std::to_string(clipped)+
        ",\"register_writes\":"+std::to_string(writes)+"}\n";
    std::cout<<result;if(report)report<<result;return 0;
}
