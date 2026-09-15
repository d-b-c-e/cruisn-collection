#include "offroad_model.h"
#include <cassert>
int main()
{
    using namespace cruisn::offroad_model;
    auto f=[](int n){return Float::integer(n).store();};
    Model model;
    model.vertices={{{f(-10),f(10),f(0)}},{{f(10),f(10),f(1)}},
                    {{f(10),f(-10),f(2)}},{{f(-10),f(-10),f(3)}}};
    model.polygons={{{0,0,0,0,0x00030000,0x00090006}},
                    {{0,0,0,0,0x00090000,0x00030006}}}; // second is back-facing
    std::array<uint32_t,12> matrix{};
    for(unsigned i=0;i<12;++i)matrix[i]=f(i==0 || i==5 || i==10);
    matrix[11]=f(70000);
    std::vector<Vertex> old_points,points;
    std::vector<uint32_t> depths;
    auto reciprocal=[&](int i){assert(i==63679);return f(1);};
    assert(project(model,matrix,f(256),0x1e60,reciprocal,old_points));
    assert(project(model,matrix,f(256),0x1e60,reciprocal,points,0,&depths));
    assert(points==old_points && depths==std::vector<uint32_t>({f(70000),f(70001),f(70002),f(70003)}));
    std::vector<Quad> old_quads,quads_out;
    std::vector<std::array<uint32_t,4>> quad_depths;
    auto palette=[](uint32_t){return 0U;};
    assert(quads(model,points,0,0,0,palette,old_quads));
    assert(quads(model,points,0,0,0,palette,quads_out,&depths,&quad_depths));
    assert(old_quads==quads_out && quad_depths.size()==1 && old_quads.size()==1);
    assert((quad_depths[0]==std::array<uint32_t,4>{{f(70000),f(70001),f(70002),f(70003)}}));
    // Invalid or unpaired depth streams cannot leave partial geometry/metadata.
    auto short_depths=depths;short_depths.pop_back();
    assert(!quads(model,points,0,0,0,palette,quads_out,&short_depths,&quad_depths));
    assert(quads_out.empty() && quad_depths.empty());
    assert(!quads(model,points,0,0,0,palette,quads_out,nullptr,&quad_depths));
    assert(!quads(model,points,0,0,0,palette,quads_out,&depths,nullptr));
    model.polygons.back()[4]=1;
    assert(!quads(model,points,0,0,0,palette,quads_out,&depths,&quad_depths));
    assert(quads_out.empty() && quad_depths.empty());
    assert(!project(model,matrix,f(256),0x1e03,reciprocal,points,0,&depths));
    assert(points.empty() && depths.empty());
    // Host depth uses the same transform, without extending original bounds.
    auto host_reciprocal=[&](int i){assert(i>=70000 && i<=70003);return f(1);};
    assert(project(model,matrix,f(256),0x1e03,host_reciprocal,points,3,&depths));
    assert(points==old_points && depths.front()==f(70000));
}
