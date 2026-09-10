#include "zeus_host_materials.h"
#include <cassert>
#include <iostream>
struct Instance { uint32_t palette, palette_control; };
int main() {
    using namespace cruisn::zeus_host;
    std::vector<uint8_t> wave(16777216);
    // Includes black, primary colors, all channels, and the unused high bit.
    const uint16_t words[] = {0, 0x7c00, 0x03e0, 0x001f, 0x7fff, 0xffff};
    const uint32_t expected[] = {0, 0xf80000, 0x00f800, 0x0000f8, 0xf8f8f8, 0xf8f8f8};
    for (unsigned i = 0; i < 6; ++i) { wave[i*2] = uint8_t(words[i]); wave[i*2+1] = uint8_t(words[i] >> 8); }
    Palette row;
    assert(palette(wave.data(), wave.size(), 0, 0x0084003f, row));
    for (unsigned i = 0; i < 6; ++i) assert(row.colors[i] == expected[i]);
    const auto saved = row.colors;
    assert(!palette(wave.data(), wave.size(), UINT32_MAX, 0x0084003f, row) && row.colors == saved);
    assert(!palette(wave.data(), wave.size(), 0, 0x0084001f, row) && row.colors == saved);
    assert(!palette(wave.data(), wave.size()-1, 0, 0x0084003f, row));
    assert(palette(wave.data(), wave.size(), (16777216-512)/8, 0x0084003f, row));
    assert(!palette(wave.data(), wave.size(), (16777216-512)/8+1, 0x0084003f, row));
    PaletteSet first, second;
    std::vector<Instance> instances = {{0,0x0084003f}, {64,0x0084003f}, {0,0x0084003f}};
    assert(palettes(instances, wave.data(), wave.size(), first));
    assert(first.rows.size() == 2 && first.instance_rows == std::vector<uint32_t>({0,1,0}));
    wave[0] = 31;
    assert(palettes(instances, wave.data(), wave.size(), second));
    assert(first.rows[0].colors[0] == 0 && second.rows[0].colors[0] == 0xf8);
    instances.back().palette_control = 0;
    assert(!palettes(instances, wave.data(), wave.size(), second));
    assert(second.rows[0].colors[0] == 0xf8); // failure leaves prior owned colors intact
    WaveImage producer, consumer;
    Packet packet; packet.frame=5000; packet.scene=12; packet.snapshot=true;
    assert(producer.stage(wave.data(),wave.size(),packet.wave));
    packet.rows=first.rows; // stale colors must reject before applying even the first page
    assert(!accept(packet,consumer) && consumer.bytes().empty());
    packet.rows=second.rows;
    std::vector<uint8_t> wire;
    assert(encode(packet,wire));
    Packet decoded; assert(decode(wire.data(),wire.size(),decoded));
    assert(decoded.frame==5000 && decoded.scene==12 && decoded.snapshot);
    assert(accept(decoded,consumer) && consumer.bytes()==wave);
    assert(producer.apply(packet.wave));
    assert(!accept(decoded,consumer));
    wave[4000]=42; wave[4096]=93;
    packet.frame=5001;packet.scene=13;packet.snapshot=false;
    assert(producer.stage(wave.data(),wave.size(),packet.wave));
    // A palette straddling two changed pages must bind the proposed generation.
    Palette crossing;assert(palette(wave.data(),wave.size(),500,0x0084003f,crossing));
    packet.rows={crossing};
    const auto stable=consumer.bytes();const auto generation=consumer.generation();
    auto damaged=packet;damaged.rows[0].colors.back()^=1;
    assert(!accept(damaged,consumer) && consumer.bytes()==stable && consumer.generation()==generation);
    assert(encode(packet,wire) && decode(wire.data(),wire.size(),decoded));
    assert(accept(decoded,consumer) && consumer.bytes()==wave);
    for (unsigned kind=0;kind<8;++kind) {
        auto bad=wire;
        if(kind==0)bad[0]^=1;
        if(kind==1)std::fill(bad.begin()+4,bad.begin()+8,0);
        if(kind==2)bad[20]=255;
        if(kind==3)bad[24]=2;
        if(kind==4)bad[28]=1;
        if(kind==5)bad.resize(bad.size()-1);
        if(kind==6)bad.push_back(0);
        if(kind==7)bad[16]^=1;
        assert(!decode(bad.data(),bad.size(),decoded));
    }
    std::cout << "PASS private palette layout, ownership, bounds and budget\n";
}
