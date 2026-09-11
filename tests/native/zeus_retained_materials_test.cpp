#include "zeus_retained_materials.h"
#include <cassert>
#include <iostream>
using namespace cruisn::zeus_host;
int main() {
    WaveImage producer, consumer;
    std::vector<uint8_t> live(16777216);
    live[0]=31;live[7000]=42;
    Packet early;early.frame=5000;early.scene=17;
    assert(producer.stage(live.data(),live.size(),early.wave));
    assert(accept(early,consumer) && producer.apply(early.wave));
    Palette saved;assert(palette(live.data(),live.size(),0,0x0084003f,saved));
    const auto original=consumer.bytes();const auto hash=consumer.image_hash();
    // Ordinary renderer uploads and guest writes must not change the private
    // scene's palette or textures before its later draw.
    live[0]=0;live[7000]=99;
    Packet late;late.frame=early.frame;late.scene=early.scene;late.rows={saved};
    assert(retain(late,producer) && retained_shape(late,producer));
    assert(late.wave.pages.empty() && !late.wave.full && late.wave.generation==2);
    std::vector<uint8_t> wire;Packet decoded;
    assert(encode(late,wire) && wire.size()==32+64+1032);
    assert(decode(wire.data(),wire.size(),decoded));
    for(unsigned kind=0;kind<8;++kind) {
        auto bad=decoded;
        if(kind==0)++bad.wave.base;
        if(kind==1)++bad.wave.result_hash;
        if(kind==2)bad.wave.pages.push_back(WaveImage::Update{});
        if(kind==3)bad.wave.full=true;
        if(kind==4)bad.rows[0].colors[0]=0;
        if(kind==5)bad.rows[0].control=0;
        if(kind==6)bad.scene=0;
        if(kind==7)bad.frame=16002;
        assert(!accept_retained(bad,consumer));
        assert(consumer.generation()==1 && consumer.image_hash()==hash && consumer.bytes()==original);
    }
    assert(accept_retained(decoded,consumer) && producer.apply(late.wave));
    assert(consumer.bytes()==original && consumer.image_hash()==hash && consumer.generation()==2);
    assert(!accept_retained(decoded,consumer)); // duplicate late packet
    Packet next;next.frame=5001;next.scene=18;
    assert(producer.stage(live.data(),live.size(),next.wave));
    assert(next.wave.base==2 && next.wave.generation==3 && next.wave.pages.size()==2);
    assert(accept(next,consumer) && producer.apply(next.wave));
    assert(consumer.bytes()==live);
    assert(!accept_retained(decoded,consumer)); // stale proposal after next scene
    Packet untouched;untouched.frame=5001;untouched.scene=18;untouched.wave.generation=99;untouched.rows={saved};
    assert(!retain(untouched,producer) && untouched.wave.generation==99); // stale palette
    WaveImage empty;assert(!retain(untouched,empty));
    Packet no_geometry;no_geometry.frame=5001;no_geometry.scene=18;
    assert(retain(no_geometry,producer) && accept_retained(no_geometry,consumer));
    assert(consumer.generation()==4 && consumer.bytes()==live); // valid empty cohort
    std::cout<<"PASS retained material ownership, zero-page sequence, mutation and stale/repeated rejection\n";
}
