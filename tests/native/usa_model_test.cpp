#include "usa_model.h"
#include <cassert>
#include <map>
#include <stdexcept>
int main()
{
    using namespace cruisn::usa_model;
    auto f=[](int n){return Float::integer(n).store();};
    // Synthetic square: count-minus-one header, interleaved flags/indices/UV/texture.
    std::vector<uint32_t> words={20,3,0xfff6fff6,0,0xfff6000a,0,0x000a000a,0,0x000afff6,0,
        0x200100,0x03020100,0x00100000,0x10001010,0x20};
    bool io=false;
    auto read=[&](uint32_t p){if(p<0xc00000 || p>=0x1000000)io=true;return words.at(p-0xc00000);};
    Model model;
    assert(load(read,0xc00000,model));
    assert(model.vertices.size()==4 && model.polygons.size()==1 && model.radius==20);
    Transform transform;
    for(unsigned i=0;i<9;++i)transform.matrix[i]=f(i%4==0?1:0);
    transform.center={{f(0),f(0),f(1024)}};
    std::array<uint32_t,32> object{};
    for(unsigned i=0;i<9;++i)object[4+i]=transform.matrix[i];
    object[1]=object[2]=f(0);object[3]=f(1024);object[14]=0x1400;
    object[13]=0xc00000;object[24]=0xc10000;object[25]=0xc20000;
    assert(compact_dispatch(object[14],0x3c4,1));
    assert(!compact_dispatch(0x08001400,0x3c4,1));
    assert(!compact_dispatch(object[14],0x3c3,1));
    assert(!compact_dispatch(object[14],0x3c4,0));
    assert(select_model(object,16000)==0xc00000);
    object[14]|=0x204;
    assert(select_model(object,8000)==0xc00000 && select_model(object,8001)==0xc10000);
    assert(select_model(object,15000)==0xc10000 && select_model(object,15001)==0xc20000);
    object[14]=0x1400;
    const std::array<uint32_t,3> camera={{f(0),f(0),f(0)}};
    const std::array<uint32_t,4> billboard={{f(1),f(0),f(0),f(1)}};
    Transform prepared;
    assert(prepare(object,camera,transform.matrix,transform.matrix,billboard,false,f(200),prepared));
    assert(prepared.matrix==transform.matrix && prepared.center==transform.center);
    object[14]=0x1408;
    assert(prepare(object,camera,transform.matrix,transform.matrix,billboard,true,f(200),prepared));
    for(unsigned i=0;i<4;++i)assert(prepared.matrix[i]==billboard[i]);
    object[14]=0x1420;
    assert(!prepare(object,camera,transform.matrix,transform.matrix,billboard,false,f(200),prepared));
    std::vector<Vertex> vertices;
    auto reciprocal=[&](int32_t index){assert(index==64);return f(1);};
    assert(project(model,transform,reciprocal,vertices));
    std::vector<Quad> output;
    assert(quads(model,vertices,true,[](uint32_t flags){assert(flags==0x200100);return 0x200;},output));
    const Quad expected={{0x100,0x200,246,189,266,189,266,210,246,210,0,16,4112,4096,0x20,0}};
    assert(output.size()==1 && output[0]==expected);
    assert(quads(model,vertices,false,[](uint32_t){return 0x00021234;},output) && output[0]==expected);
    // Compact X/Z order and vertical-origin operand, not a World 9-word matrix.
    transform.compact=true;transform.matrix={{f(1),f(0),f(0),f(1),0,0,0,0,0}};
    std::vector<Vertex> compact;
    assert(project(model,transform,reciprocal,compact) && compact==vertices);
    transform.origin_y=f(210);
    assert(project(model,transform,reciprocal,compact));
    assert(Float::load(compact[0][1]).fix()==199);
    transform.origin_y=f(200);
    // The extended tail must never call through guest memory past index4999.
    transform.center[2]=f(160016);
    auto no_guest=[](int32_t)->uint32_t{throw std::runtime_error("unexpected guest table read");};
    assert(!project(model,transform,no_guest,vertices,Projection::host,160000) && vertices.empty());
    assert(project(model,transform,no_guest,vertices,Projection::host,240000));
    assert(Float::load(vertices[0][2]).fix()==160016);
    transform.center[2]=f(0);
    assert(!project(model,transform,no_guest,vertices) && vertices.empty());
    transform.center={{f(100000),f(0),f(1024)}};
    assert(!project(model,transform,reciprocal,vertices) && vertices.empty());
    assert(project(model,transform,reciprocal,vertices,Projection::captured));
    // The original USA branch retains cross==0. Back-facing polygons disappear.
    for(auto &v:vertices)v={{f(256),f(200),f(1024)}};
    assert(quads(model,vertices,true,[](uint32_t){return 0;},output) && output.size()==1);
    auto broken=model;broken.polygons[0][1]=0x04020100;
    assert(!quads(broken,vertices,true,[](uint32_t){return 0;},output) && output.empty());
    assert(!load(read,0x993000,model) && !io && model.vertices.empty());
    assert(!load(read,0xffffffff,model) && !io);
    words[1]=0x04000003;
    assert(!load(read,0xc00000,model) && model.vertices.empty());
    words[1]=3;words[11]=0x04020100;
    assert(!load(read,0xc00000,model) && model.vertices.empty());
}
