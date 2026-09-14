// SPDX-License-Identifier: BSD-3-Clause
// Offline owned-render comparison only. Input owners need separate lifetime /
// actual-device-boundary verification; this program does not execute the game.
#include "exotica_composition.h"
#include "exotica_scene_capture.h"
#include <fstream>
#include <iostream>
#include <stdexcept>

static std::vector<uint8_t> read(const char *path,size_t limit) {
    std::ifstream file(path,std::ios::binary|std::ios::ate);
    if(!file)throw std::runtime_error("input open");
    const auto size=file.tellg();if(size<0 || uint64_t(size)>limit)throw std::runtime_error("input bound");
    std::vector<uint8_t> data(static_cast<size_t>(size));file.seekg(0);
    if(size && !file.read(reinterpret_cast<char *>(data.data()),size))throw std::runtime_error("input read");
    return data;
}
static cruisn::exotica_scene::Result scene(const char *instances,const char *quads) {
    auto wire=read(instances,4096*44);auto polygons=read(quads,131072*260);
    if(wire.size()%44 || polygons.size()%260)throw std::runtime_error("scene extent");
    cruisn::exotica_scene::Result out;
    for(size_t offset=0;offset<wire.size();offset+=44) {
        uint32_t w[11];std::memcpy(w,wire.data()+offset,44);
        cruisn::exotica_scene::Instance i;i.entry=w[0];i.source=w[1];i.descriptor=w[2];i.base=w[3];i.count=w[4];i.band=w[5];
        i.palette=w[6];i.palette_control=w[7];std::memcpy(&i.depth,w+8,4);i.first_quad=w[9];i.quad_count=w[10];out.instances.push_back(i);
    }
    static_assert(sizeof(cruisn::zeus_model::Quad)==260,"quad snapshot layout");
    out.quads.resize(polygons.size()/260);if(!polygons.empty())std::memcpy(out.quads.data(),polygons.data(),polygons.size());
    return out;
}
static void write(const std::string &path,const void *data,size_t bytes) {
    std::ofstream f(path,std::ios::binary);if(!f || (bytes && !f.write(static_cast<const char *>(data),bytes)))throw std::runtime_error("output write");
    f.close();if(!f)throw std::runtime_error("output close");
}
int main(int argc,char **argv) {
    try {
        const uint32_t endian=1;if(*reinterpret_cast<const uint8_t *>(&endian)!=1)throw std::runtime_error("little-endian snapshots required");
        if(argc!=9)throw std::runtime_error("usage: active-instances active-quads waiting-instances waiting-quads owners proposal-wave ready-wave output-prefix");
        auto active=scene(argv[1],argv[2]),waiting=scene(argv[3],argv[4]);
        auto owner_data=read(argv[5],4096*48),proposal=read(argv[6],16777216),ready=read(argv[7],16777216);
        if(owner_data.size()%48 || proposal.size()!=16777216 || ready.size()!=16777216)throw std::runtime_error("owner/image extent");
        std::vector<cruisn::scenery_lifetimes::Handle> owners;
        for(size_t offset=0;offset<owner_data.size();offset+=48) {
            uint64_t w[6];std::memcpy(w,owner_data.data()+offset,48);
            if(w[1]>UINT32_MAX || w[2]>UINT32_MAX || w[3]>UINT32_MAX)throw std::runtime_error("owner narrowing");
            cruisn::scenery_lifetimes::Handle h;h.key.realm=w[0];h.key.section=uint32_t(w[1]);h.key.source=uint32_t(w[2]);
            h.slot=uint32_t(w[3]);h.epoch=w[4];h.generation=w[5];owners.push_back(h);
        }
        cruisn::exotica_scene::Result out;cruisn::exotica_composition::Counts counts;
        if(!cruisn::exotica_composition::filter(active,waiting,owners,proposal.data(),ready.data(),ready.size(),out,counts))throw std::runtime_error("composition rejected");
        const auto instances=cruisn::exotica_scene::instance_words(out);
        write(std::string(argv[8])+"-instances.bin",instances.data(),instances.size()*sizeof(instances[0]));
        write(std::string(argv[8])+"-quads.bin",out.quads.data(),out.quads.size()*260);
        std::cout<<"{\"overlaps\":"<<counts.overlaps<<",\"removed_quads\":"<<counts.removed_quads
            <<",\"texture_pages\":"<<counts.texture_pages<<",\"instances\":"<<out.instances.size()<<",\"quads\":"<<out.quads.size()<<"}\n";
        return 0;
    } catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
}
