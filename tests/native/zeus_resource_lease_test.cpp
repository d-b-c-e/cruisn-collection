#include "zeus_resource_lease.h"
#include <cassert>
#include <fstream>
#include <iostream>
using namespace cruisn;
// Independent brute-force addresses, including all bilinear neighbors.
static uint32_t address(unsigned type,unsigned flags,int x,int y,int w,uint32_t base) {
    uint64_t n;
    if(flags&(64|128))n=2*((uint64_t(y>>1)*w*2)+((x>>1)<<2)+((y&1)<<1)+(x&1));
    else if(type==0)n=uint64_t(y>>2)*w*4+((x>>2)<<3)+((y&3)<<1)+((x>>1)&1);
    else if(type==1)n=uint64_t(y>>1)*w*2+((x>>2)<<3)+((y&1)<<2)+(x&3);
    else n=uint64_t(y>>2)*w*4+((x>>1)<<3)+((y&3)<<1)+(x&1);
    return uint32_t((uint64_t(base)*8+n)&0xffffff);
}
int main(int argc,char **argv) {
    if(argc==3) {
        std::ifstream f(argv[1],std::ios::binary|std::ios::ate);assert(f);
        const auto size=f.tellg();assert(size>=0 && size%260==0 && size<=std::streamoff(131072*260));
        f.seekg(0);zeus_lease::Coverage coverage;zeus_model::Quad q;size_t n=0;
        while(f.read(reinterpret_cast<char *>(&q),sizeof(q))){assert(coverage.add(q));++n;}
        std::ofstream out(argv[2],std::ios::binary);for(bool p:coverage.pages())out.put(p?1:0);out.close();assert(out);
        std::cout<<"{\"quads\":"<<n<<",\"pages\":"<<coverage.count()<<"}\n";return 0;
    }
    assert(argc==1);size_t checked=0;
    for(unsigned type=0;type<4;++type)for(unsigned flags:{0u,64u,128u})
    for(int w:{16,32,64,128,256})for(uint32_t base:{0u,0x1ffffeu,0x12345u}) {
        zeus_model::Quad q;q.state[1]=4;q.state[2]=type;q.state[3]=base;q.state[4]=w;q.state[9]=flags;
        const float uv[4][2]={{-12,-4},{131,-4},{131,67},{-12,67}};
        for(unsigned i=0;i<4;++i){q.vertices[i][5]=(i+1)*.25f;q.vertices[i][3]=uv[i][0]*256*q.vertices[i][5];q.vertices[i][4]=uv[i][1]*256*q.vertices[i][5];}
        zeus_lease::Coverage c;assert(c.add(q));
        for(int y=0;y<=69;++y)for(int x=0;x<=133;++x) {
            auto a=address(type,flags,x,y,w,base);assert(c.pages()[a/4096]);++checked;
            if(flags&(64|128))assert(c.pages()[((a+1)&0xffffff)/4096]);
        }
        q.vertices[1][3]=std::numeric_limits<float>::infinity();assert(!zeus_lease::Coverage().add(q));
        q.vertices[1][3]=1.e10f;zeus_lease::Coverage full;assert(full.add(q) && full.count()==4096);
    }
    std::vector<uint8_t> a(zeus_lease::wave_bytes),b=a;
    assert(zeus_lease::model_equal(a.data(),b.data(),a.size(),0,0));
    assert(zeus_lease::palette_equal(a.data(),b.data(),a.size(),0));
    b[7]=1;assert(!zeus_lease::model_equal(a.data(),b.data(),a.size(),0,0));
    assert(!zeus_lease::palette_equal(a.data(),b.data(),a.size(),0));
    assert(zeus_lease::model_equal(a.data(),b.data(),a.size(),1,0));
    assert(!zeus_lease::model_equal(a.data(),b.data(),a.size(),0,0xffffffff));
    assert(!zeus_lease::palette_equal(a.data(),b.data(),a.size(),0xffffffff));
    zeus_model::Quad q;q.state[1]=3;q.state[4]=16;
    for(unsigned i=0;i<3;++i)q.vertices[i][5]=1;
    zeus_lease::Coverage used;assert(used.add(q) && used.count()==1);
    b=a;b[10000]=1;assert(used.equal(a.data(),b.data(),a.size()));
    b[0]=1;assert(!used.equal(a.data(),b.data(),a.size()));
    std::cout<<"PASS "<<checked<<" bounded texture addresses, wrap, palette/model mutation\n";
}
