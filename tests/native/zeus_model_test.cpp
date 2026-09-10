#include "zeus_model.h"
#include <cassert>
using namespace cruisn::zeus_model;
uint32_t bits(float value){uint32_t w;std::memcpy(&w,&value,4);return w;}
int main()
{
    Context c;c.frame=1;c.matrix[0]=c.matrix[4]=c.matrix[8]=1;c.translation[2]=100;
    c.regs[0x66]=0x8e;c.regs[0x68]=0x9d;c.regs[0x6c]=9;
    c.regs[0x6a]=bits(256);c.regs[0x6b]=bits(200);
    c.render[1]=511;c.render[2]=399;c.render[0xc]=256;
    std::vector<uint32_t> words={0x229d0000,1,0x38000000,0,0x0001ffff,0xffffffff,0,0,0,0,0xffff0001,0x00010001};
    Result r;assert(decode(words,c,r) && r.quads.size()==1 && r.polygons==1);
    const auto baseline=r.quads[0];assert(baseline.state[1]==4 && baseline.state[9]==28);
    assert(baseline.vertices[0][0]<256 && baseline.vertices[2][0]>256);
    assert(baseline.state[15]==511 && baseline.state[16]==399);
    auto material=words;material.insert(material.begin(),{0x36200000,0x05000005});
    assert(decode(material,c,r) && r.quads[0].state[3]==5 && c.texture==0 && c.render[5]==0);
    material=words;material[1]=0x82;
    assert(decode(material,c,r) && (r.quads[0].state[9]&64) && !(r.quads[0].state[9]&24));
    material=words;material.insert(material.begin(),{0x36200000,0x15000000|0xffffff});
    assert(decode(material,c,r) && r.quads[0].state[10]==0xffffffff);
    c.translation[2]=-100;assert(decode(words,c,r) && r.quads.empty() && r.near_rejected==1);
    c.translation[2]=0;auto crossing=words;crossing[8]=0x0001ffff;crossing[9]=0x00010001;
    assert(decode(crossing,c,r) && r.near_clipped==1 && r.quads[0].state[1]==5);
    c.translation[2]=100;c.quad_size=14;auto normal=words;normal.insert(normal.end(),4,0x12345678);
    assert(decode(normal,c,r) && std::memcmp(&r.quads[0],&baseline,sizeof(Quad))==0);
    c.quad_size=10;auto bad=words;bad.pop_back();assert(!decode(bad,c,r));
    bad=words;bad[0]=0xff000000;assert(!decode(bad,c,r));
    bad=words;bad.insert(bad.begin(),{0x36200000,0x08000000});assert(!decode(bad,c,r));
    c.regs[0x6c]=31;assert(!decode(words,c,r));
}
