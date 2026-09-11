// SPDX-License-Identifier: BSD-3-Clause
// LOCAL captured geometry: replace a second full material image with a checked
// retained-image continuation. Does not issue emulator/GPU commands.
#include "zeus_retained_materials.h"
#include "zeus_wide_packet.h"
#include <fstream>
#include <iostream>
#include <stdexcept>

static std::vector<uint8_t> read(const char *path) {
    std::ifstream f(path,std::ios::binary|std::ios::ate);
    if(!f || f.tellg()<0 || uint64_t(f.tellg())>cruisn::zeus_wide::maximum_bytes)
        throw std::runtime_error("bounded packet input");
    std::vector<uint8_t> bytes(size_t(f.tellg()),uint8_t(0));f.seekg(0);
    if(!bytes.empty() && !f.read(reinterpret_cast<char *>(bytes.data()),bytes.size()))
        throw std::runtime_error("packet read");
    return bytes;
}
int main(int argc,char **argv) {
    try {
        if(argc!=4)throw std::runtime_error("EARLY_FULL.xwd WAITING_FULL.xwd OUTPUT.xwd required");
        const auto early_wire=read(argv[1]),waiting_wire=read(argv[2]);
        cruisn::zeus_wide::Packet early,waiting;
        if(!cruisn::zeus_wide::decode(early_wire.data(),early_wire.size(),early) ||
            !cruisn::zeus_wide::decode(waiting_wire.data(),waiting_wire.size(),waiting))
            throw std::runtime_error("packet shape");
        if(early.materials.frame!=waiting.materials.frame || early.materials.scene!=waiting.materials.scene ||
            early.margin!=waiting.margin || early.page!=waiting.page || early.multiplier!=waiting.multiplier ||
            early.draw!=waiting.draw || early.materials.snapshot!=waiting.materials.snapshot)
            throw std::runtime_error("early/waiting scene boundary");
        cruisn::zeus_host::WaveImage image,other;
        if(!cruisn::zeus_host::accept(early.materials,image) ||
            !cruisn::zeus_host::accept(waiting.materials,other) || image.bytes()!=other.bytes())
            throw std::runtime_error("proposal image identity");
        const auto hash=image.image_hash();
        if(!cruisn::zeus_host::retain(waiting.materials,image))throw std::runtime_error("retained staging");
        std::vector<uint8_t> encoded;
        if(!cruisn::zeus_wide::encode(waiting,encoded))throw std::runtime_error("retained encoding");
        cruisn::zeus_wide::Packet decoded;
        if(!cruisn::zeus_wide::decode(encoded.data(),encoded.size(),decoded) ||
            !cruisn::zeus_host::accept_retained(decoded.materials,image) ||
            image.generation()!=2 || image.image_hash()!=hash || image.bytes()!=other.bytes())
            throw std::runtime_error("retained consumer");
        std::ofstream output(argv[3],std::ios::binary);
        if(!output.write(reinterpret_cast<const char *>(encoded.data()),encoded.size()))
            throw std::runtime_error("output write");
        output.close();if(!output)throw std::runtime_error("output close");
        std::cout<<"{\"passed\":true,\"generation\":2,\"pages\":0,\"palettes\":"<<decoded.materials.rows.size()
            <<",\"quads\":"<<decoded.quads.size()<<",\"old_bytes\":"<<waiting_wire.size()
            <<",\"retained_bytes\":"<<encoded.size()<<"}\n";
        return 0;
    } catch(const std::exception &error) {std::cerr<<error.what()<<'\n';return 1;}
}
