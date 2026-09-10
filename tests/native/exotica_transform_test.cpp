#include "exotica_transform.h"
#include <cassert>
int main()
{
    using namespace cruisn::exotica_transform;
    auto f=[](int v){return Float::integer(v).store();};
    std::array<uint32_t,9> identity,rotation;
    for(unsigned i=0;i<9;++i)identity[i]=f(i%4==0);
    rotation=identity;rotation[0]=f(-1);rotation[8]=f(-1);
    std::array<uint32_t,3> p={{f(10),f(20),f(30)}},c={{f(1),f(2),f(3)}};
    Prepared result;
    assert(prepare(p,c,identity,rotation,identity,0,result));
    assert(result.matrix==rotation && result.depth==27);
    assert(result.translation[0]==f(9) && result.translation[1]==f(18));
    assert(packet(result,f(1),true).size()==13 && packet(result,f(1),false).size()==4);
    assert(prepare(p,c,identity,rotation,identity,0x80000,result) && result.matrix==identity);
    assert(prepare(p,c,identity,rotation,identity,0x80,result) && result.matrix==rotation);
    assert(prepare(p,c,identity,rotation,identity,3,result) && result.translation==p && result.depth==30);
    c[2]=f(30000);assert(prepare(p,c,identity,rotation,identity,0,result) && result.depth==-29970);
    assert(select_model(10,20,-1)==10 && select_model(10,20,25000)==10);
    assert(select_model(10,20,25001)==20 && select_model(10,0,25001)==10);
    assert(!prepare(p,c,identity,rotation,identity,2,result) && result.depth==0);
    assert(matrix_update(0,f(255),f(255)) && !matrix_update(0x10,f(255),f(255)));
    assert(matrix_update(0x10,f(255),f(100)) && !matrix_update(0x80000,f(254),f(100)));
}
