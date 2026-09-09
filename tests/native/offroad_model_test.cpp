#include "offroad_model.h"
#include <cassert>
#include <map>
int main()
{
    using namespace cruisn::offroad_model;
    auto f=[](int n){return Float::integer(n).store();};
    std::map<uint32_t,uint32_t> ram;
    const uint32_t descriptor=0xc00007,v=0xc10000,p=0xc20000;
    const std::array<uint32_t,5> lod={{3,v,0,0,p}};
    for(unsigned i=0;i<5;++i)ram[descriptor+i]=lod[i];
    const int xyz[]={-10,10,0,10,10,0,10,-10,0,-10,-10,0};
    for(unsigned i=0;i<12;++i)ram[v+i]=f(xyz[i]);
    const std::array<uint32_t,6> poly={{0x210003,0x01000200,0x03000400,0x30,0x00030000,0x00090006}};
    for(unsigned i=0;i<6;++i)ram[p+i]=poly[i];
    unsigned reads=0;
    auto read=[&](uint32_t address){++reads;return ram.at(address);};
    Model model;
    assert(load(read,descriptor,model) && model.vertices.size()==4 && model.polygons.size()==1);
    std::array<uint32_t,12> matrix;
    for(unsigned i=0;i<12;++i)matrix[i]=f(i==0 || i==5 || i==10);
    matrix[11]=f(1000);
    std::vector<Vertex> points;
    auto reciprocal=[&](int32_t index){assert(index==1000);return f(1);};
    assert(project(model,matrix,f(256),0x1e03,reciprocal,points));
    const std::vector<Vertex> expected={{{246,190}},{{266,190}},{{266,210}},{{246,210}}};
    assert(points==expected);
    std::vector<Quad> output;
    auto palette=[](uint32_t index){assert(index==0x21);return 0x17;};
    assert(quads(model,points,0x400,0x200,0x1000,palette,output));
    const Quad quad={{0x403,0x217,246,190,266,190,266,210,246,210,0x200,0x100,0x400,0x300,0x1030,0}};
    assert(output.size()==1 && output[0]==quad);
    // Reject incomplete output atomically, including a malformed later polygon.
    auto broken=model;broken.polygons.push_back(poly);broken.polygons[1][4]=1;
    assert(!quads(broken,points,0,0,0,palette,output) && output.empty());
    broken=model;broken.polygons[0][5]=12;
    assert(!quads(broken,points,0,0,0,palette,output) && output.empty());
    std::swap(points[1],points[3]);
    assert(quads(model,points,0,0,0,palette,output) && output.empty());
    for(auto &point:points)point={{256,200}};
    assert(quads(model,points,0,0,0,palette,output) && output.size()==1);
    // Original branch-specific bounds, with no out-of-range reciprocal reads.
    unsigned lookups=0;
    auto near_reciprocal=[&](int32_t index){++lookups;assert(index==-4096);return f(1);};
    matrix[11]=f(-5000);
    assert(!project(model,matrix,f(256),0x1e03,near_reciprocal,points) && lookups==0 && points.empty());
    assert(project(model,matrix,f(256),0x1e3b,near_reciprocal,points) && points==expected && lookups==4);
    matrix[11]=f(70000);lookups=0;
    auto far_reciprocal=[&](int32_t index){++lookups;assert(index==63679);return f(1);};
    assert(!project(model,matrix,f(256),0x1e03,far_reciprocal,points) && lookups==0);
    assert(project(model,matrix,f(256),0x1e60,far_reciprocal,points) && points==expected && lookups==4);
    assert(!project(model,matrix,f(256),0,far_reciprocal,points) && points.empty());
    const unsigned before=reads;
    assert(!load(read,0x980000,model) && reads==before && model.vertices.empty());
    assert(!load(read,0xffffffff,model) && reads==before);
    ram[descriptor]=0xffffffff;
    assert(!load(read,descriptor,model) && model.vertices.empty());
    ram[descriptor]=3;ram[descriptor+1]=0x980000;
    assert(!load(read,descriptor,model) && model.vertices.empty());
    ram[descriptor+1]=v;ram[p+4]=1;
    assert(!load(read,descriptor,model) && model.vertices.empty());
}
