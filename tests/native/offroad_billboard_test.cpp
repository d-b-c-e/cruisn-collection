#include "offroad_billboard.h"
#include <cassert>
int main()
{
    using namespace cruisn::offroad_billboard;
    auto f=[](int n){return Float::integer(n).store();};
    std::array<uint32_t,22> object{};object[5]=4;
    object[11]=f(10);object[12]=f(20);object[13]=f(1000);
    std::array<uint32_t,12> view{},basis{},matrix{},vertices{},output{};
    view.fill(f(0));basis.fill(f(0));vertices.fill(f(0));
    for(unsigned i:{0U,5U,10U})view[i]=basis[i]=f(1);
    basis[0]=f(-1);basis[3]=basis[7]=basis[11]=f(9999);
    assert(prepare(object,view,basis,matrix));
    assert(matrix[0]==f(-1) && matrix[3]==f(10) && matrix[7]==f(20) && matrix[11]==f(1000));
    vertices[0]=f(3);vertices[1]=f(4);vertices[2]=f(5);
    assert(project(vertices,matrix,f(256),[&](uint32_t z){assert(z==1000 || z==1005);return f(1);},output));
    assert(output[0]==263 && output[1]==176 && output[2]==1005);
    std::array<uint32_t,6> polygon={{0x10100,0x02030405,0x06070809,10,0x00030000,0x00090006}};
    std::array<uint16_t,16> draw;
    object[18]=100;object[19]=200;
    assert(quad(object,polygon,output,3,0x2000,draw));
    assert(draw[0]==0x2100 && draw[1]==103 && draw[10]==0x0405 && draw[14]==210);
    polygon[4]=1;assert(!quad(object,polygon,output,3,0,draw));
    assert((draw==std::array<uint16_t,16>{}));
    polygon[4]=0x00030000;assert(!quad(object,polygon,output,3,1,draw));
    for(unsigned flags:{0U,2U,6U}) {
        object[5]=flags;matrix.fill(123);
        assert(!prepare(object,view,basis,matrix));
        assert((matrix==std::array<uint32_t,12>{}));
    }
    object[5]=4;assert(prepare(object,view,basis,matrix));
    // A late bad vertex must not leave a partially produced result.
    vertices[11]=f(63680);output.fill(123);
    assert(!project(vertices,matrix,f(256),[&](uint32_t){return f(1);},output));
    assert((output==std::array<uint32_t,12>{}));
}
