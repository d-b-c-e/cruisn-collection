#include "offroad_host_scenery.h"
#include <cassert>
#include <map>
int main()
{
    using namespace cruisn;
    using namespace cruisn::offroad_host;
    std::map<uint32_t,uint32_t> m={{0x11141,0x9e0000},{0x11142,0x10390},{0x19e29,0xa00000},
        {0x19e21,2},{0x19e23,256}};
    auto read=[&](uint32_t p){return m[p];};
    MaterialState s;assert(material_state(read,s) && s.ready);
    m[0x11145]=1;assert(!material_state(read,s));
    m[0x11144]=1;assert(material_state(read,s) && !s.ready);
    m[0x11145]=0;m[0x11143]=1;m[0x19e20]=1;assert(material_state(read,s) && !s.ready);
    m[0x19e20]=0;assert(material_state(read,s) && s.ready);
    Quad q{};q[0]=0x100;q[1]=256;
    assert(material_bound(q,s));q[1]=257;assert(!material_bound(q,s));q[1]=256;
    q[14]=255;q[10]=0x100;assert(!material_bound(q,s));
    q[0]=3;q[1]=508;assert(material_bound(q,s));q[1]=509;assert(!material_bound(q,s));
    std::array<Float,3> pos={{Float::integer(3000),Float::integer(4000),Float::integer(12000)}};
    assert(order(pos,Float::integer(1))==169000000);
    pos[2]=-pos[2];assert(order(pos,Float::integer(1))==-169000000);
    offroad_model::Model model;model.vertices.push_back({{Float().store(),Float().store(),Float().store()}});
    std::array<uint32_t,12> matrix;matrix.fill(Float().store());matrix[11]=Float::integer(70000).store();
    std::vector<offroad_model::Vertex> points;
    auto reciprocal=[](int32_t i){return offroad_distance::reciprocal(i);};
    assert(!offroad_model::project(model,matrix,Float::integer(256).store(),0x1e03,reciprocal,points));
    assert(offroad_model::project(model,matrix,Float::integer(256).store(),0x1e03,reciprocal,points,2));
    assert(points[0][0]==256 && points[0][1]==200);
    matrix[11]=Float::integer(502).store();
    assert(!offroad_model::project(model,matrix,Float::integer(256).store(),0x1e03,reciprocal,points,2));
    assert(!offroad_model::project(model,matrix,0,0x1e60,reciprocal,points,2));
    Cache cache;Scene scene;assert(build(read,scene,1,true,cache) && scene.pretrack && scene.objects.empty());
}
