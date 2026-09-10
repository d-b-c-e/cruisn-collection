#include "zeus_margin_packet.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <limits>
using namespace cruisn;
int main(int argc,char **argv) {
    std::vector<uint8_t> wave(16777216,0);zeus_host::WaveImage image;
    zeus_margin::Packet p;p.materials.frame=5000;p.materials.scene=1;
    assert(image.stage(wave.data(),wave.size(),p.materials.wave));
    zeus_host::Palette row;row.control=0x84003f;p.materials.rows.push_back(row);
    p.margin=86;p.page=400;p.draw=true;
    zeus_margin::Quad q;
    q.polygon.state={{5000,8,0,0,128,0,0,256,0,28,0,400,0,0,0,511,399}};
    const float octagon[8][2]={{-80,50},{-60,40},{-40,50},{-30,70},{-40,90},{-60,100},{-80,90},{-90,70}};
    for(unsigned i=0;i<8;++i)q.polygon.vertices[i]={{octagon[i][0],octagon[i][1],16777214.f,0,0,1}};
    p.quads.push_back(q);std::vector<uint8_t> wire,again;
    assert(zeus_margin::encode(p,wire));zeus_margin::Packet decoded;
    assert(zeus_margin::decode(wire.data(),wire.size(),decoded));
    assert(zeus_margin::encode(decoded,again) && again==wire);
    assert(decoded.quads[0].polygon.state[1]==8 && 3*(8-2)==18);
    zeus_host::WaveImage accepted;assert(zeus_host::accept(decoded.materials,accepted));
    assert(accepted.bytes()==wave);
    for(size_t n: {size_t(0),size_t(31),wire.size()-1}) {
        zeus_margin::Packet unchanged;unchanged.page=123;
        assert(!zeus_margin::decode(wire.data(),n,unchanged) && unchanged.page==123);
    }
    for(size_t offset:{size_t(0),size_t(4),size_t(8),size_t(12),size_t(16),size_t(20),size_t(24),size_t(28)}) {
        auto bad=wire;std::fill_n(bad.begin()+offset,4,255);
        assert(!zeus_margin::decode(bad.data(),bad.size(),decoded));
    }
    auto bad=q.polygon;
    for(unsigned vertices:{0u,2u,9u}) {bad.state[1]=vertices;assert(!zeus_margin::depth24(bad,5000,400));}
    bad=q.polygon;bad.vertices[0][2]=16777216.f;assert(!zeus_margin::depth24(bad,5000,400));
    bad=q.polygon;bad.state[10]=2;assert(!zeus_margin::depth24(bad,5000,400));
    bad=q.polygon;bad.state[10]=1;assert(zeus_margin::depth24(bad,5000,400));
    bad=q.polygon;bad.state[9]|=512;bad.state[10]=16777215;assert(zeus_margin::depth24(bad,5000,400));
    bad.state[10]=16777216;assert(!zeus_margin::depth24(bad,5000,400));
    for(float value:{-1.f,std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}) {
        bad=q.polygon;bad.vertices[0][2]=value;assert(!zeus_margin::depth24(bad,5000,400));
    }
    bad=q.polygon;bad.vertices[0][5]=0;assert(!zeus_margin::depth24(bad,5000,400));
    for(unsigned flags:{20u,28u|32u,28u|256u,28u|1024u}) {
        bad=q.polygon;bad.state[9]=flags;assert(!zeus_margin::depth24(bad,5000,400));
    }
    for(unsigned flags:{12u,28u,30u,28u|64u,28u|128u}) {
        bad=q.polygon;bad.state[9]=flags;assert(zeus_margin::depth24(bad,5000,400));
    }
    bad=q.polygon;bad.state[12]=1;assert(!zeus_margin::depth24(bad,5000,400));
    assert(!zeus_margin::depth24(q.polygon,5001,400) && !zeus_margin::depth24(q.polygon,5000,0));
    p.quads[0].palette=1;assert(!zeus_margin::encode(p,again));p.quads.clear();
    assert(zeus_margin::encode(p,again) && zeus_margin::decode(again.data(),again.size(),decoded));
    size_t actual=0;
    for(int i=1;i<argc;++i) {
        std::ifstream file(argv[i],std::ios::binary);assert(file.good());
        zeus_model::Quad r;
        while(file.read(reinterpret_cast<char *>(&r),sizeof(r))) {
            assert(zeus_margin::depth24(r,r.state[0],r.state[11]));++actual;
        }
        assert(file.eof() && !file.gcount());
    }
    std::cout<<"PASS owned roundtrip/atomic rejection/D24 limits/eight-vertex packet/empty scene; captured quads="<<actual<<"\n";
}
