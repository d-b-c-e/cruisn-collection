#include "offroad_transform.h"
#include <cassert>
int main()
{
    using namespace cruisn::offroad_transform;
    auto f=[](int n){return Float::integer(n).store();};
    std::vector<uint32_t> words(16386,f(0));words[16384]=words[16385]=f(1);
    auto table=[&](int32_t i){assert(i>=-1 && i<=16384);return words.at(i+1);};
    for(unsigned q=0;q<4;++q)
    {
        const auto value=trig(q*0x40000000U,table);
        assert(value.first.fix()==(q==1?1:q==3?-1:0));
        assert(value.second.fix()==(q==0?1:q==2?-1:0));
    }
    std::array<uint32_t,22> object{};
    std::array<uint32_t,12> view,output;
    for(unsigned i=0;i<12;++i)view[i]=f(i==0 || i==5 || i==10);
    object[11]=f(10);object[12]=f(20);object[13]=f(30);
    object[5]=1;
    assert(prepare(object,view,table,output));
    assert(output[3]==f(10) && output[7]==f(20) && output[11]==f(30));
    auto identity=output;
    object[5]=0;assert(prepare(object,view,table,output) && output==identity);
    object[5]=2;assert(!prepare(object,view,table,output));
    // Synthetic fractional products detect the store/reload in the yaw path.
    words[8192]=words[8193]=0xff3504f3;
    object[5]=0x10;object[15]=0x20000000;
    view[0]=0xff1b925a;view[2]=0xff689868;
    assert(prepare(object,view,table,output) && output[2]==0x00093cdd);
    // LOD thresholds are inclusive; flag0x40 enables the second transition.
    std::array<uint32_t,13> context={{100,1,1,1000,uint32_t(-1000),500,uint32_t(-500),10,20,30,40,50,60}};
    object[5]=0x60;object[8]=109;
    assert(select_lod(object,context).first==0);
    object[8]=110;assert(select_lod(object,context).first==1);
    object[8]=120;assert(select_lod(object,context).first==2);
    object[5]=0x20;assert(select_lod(object,context).first==1);
    object[5]=0xe0;object[8]=140;assert(select_lod(object,context).first==2);
    object[5]=0x2020;object[8]=160;assert(select_lod(object,context).first==2);
    object[5]=0x60;object[8]=620;
    assert(select_lod(object,context).second==-480 && select_lod(object,context).first==0);
    object[8]=uint32_t(-400);
    assert(select_lod(object,context).second==500 && select_lod(object,context).first==2);
    context[1]=2;assert(select_lod(object,context).first==0);
}
