// SPDX-License-Identifier: BSD-3-Clause
// Offline scene assembly from LOCAL captures. No ROM/resources are distributed.
#include "exotica_scene.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <chrono>
#include <string>
#include <iomanip>
static std::vector<uint32_t> load(const char *path,size_t bytes)
{
    std::ifstream f(path,std::ios::binary|std::ios::ate);
    if(!f || f.tellg()!=std::streamoff(bytes))throw std::runtime_error("snapshot size");
    f.seekg(0);std::vector<uint32_t> v(bytes/4);
    if(!f.read(reinterpret_cast<char *>(v.data()),bytes))throw std::runtime_error("snapshot read");
    return v;
}
template<class T> void write(const std::string &name,const std::vector<T> &data)
{
    std::ofstream f(name,std::ios::binary);
    if(!f.write(reinterpret_cast<const char *>(data.data()),data.size()*sizeof(T)))throw std::runtime_error("output write");
    f.close();if(!f)throw std::runtime_error("output close");
}
int main(int argc,char **argv)
{
    try
    {
        if(argc!=7)return 2;
        std::ifstream input(argv[5],std::ios::binary);
        auto word=[&](){uint32_t w;if(!input.read(reinterpret_cast<char *>(&w),4))throw std::runtime_error("context truncated");return w;};
        const auto magic=word();
        if(magic!=0x31534358 && magic!=0x32534358)throw std::runtime_error("context magic");
        cruisn::exotica_scene::Parameters p;
        p.frame=word();p.multiplier=word();p.margin=cruisn::zeus_model::word_float(word());
        const auto fade=word(),bank=word(),partial=word();
        if(fade>1 || bank>2 || partial>1)throw std::runtime_error("context switches");
        p.complete_fade=fade!=0;p.scale=word();p.setup.palette_setup=word();
        for(auto &v:p.camera)v=word();
        for(auto &v:p.view)v=word();
        for(auto &v:p.alternate)v=word();
        for(auto &v:p.setup.constants)v=word();
        for(auto &v:p.setup.commands)v=word();
        for(auto &v:p.setup.programs)v=word();
        for(auto &b:p.setup.bodies)for(auto &v:b)v=word();
        const auto defaults=word();if(!defaults || defaults>16)throw std::runtime_error("context defaults");
        for(unsigned i=0;i<defaults;++i)p.setup.defaults.push_back(word());
        p.context.quad_size=word();p.context.ucode=word();p.context.palette=word();
        p.context.texture=word();p.context.yscale=word();p.context.zoffset=word();
        for(auto &v:p.context.matrix)v=cruisn::zeus_model::word_float(word());
        for(auto &v:p.context.translation)v=cruisn::zeus_model::word_float(word());
        for(auto &v:p.context.light)v=cruisn::zeus_model::word_float(word());
        for(auto &v:p.context.regs)v=word();
        for(auto &v:p.context.render)v=word();
        if(magic==0x32534358)
        {
            if(word()!=1)throw std::runtime_error("context bounds switch");
            p.frustum_bounds=true;
        }
        if(input.peek()!=std::char_traits<char>::eof())throw std::runtime_error("context trailing bytes");
        const auto ram=load(argv[1],0x100000),main=load(argv[2],0x800000),banks=load(argv[3],0x3000000),wave=load(argv[4],0x1000000);
        auto read=[&](uint32_t a){
            if(a<0x40000)return ram[a];
            if(a>=0xa00000 && a<0xc00000)return main[a-0xa00000];
            if(a>=0xc00000 && a<0x1000000)return banks[bank*0x400000+a-0xc00000];
            throw std::runtime_error("unmapped C32 word");};
        auto model_read=[&](uint32_t base,uint32_t count,std::vector<uint32_t> &words){
            const size_t start=2*(size_t(base%1024)+size_t((base>>16)%2048)*1024),size=2*(size_t(count)+1);
            if(start>wave.size() || size>wave.size()-start)return false;
            words.assign(wave.begin()+start,wave.begin()+start+size);return true;};
        const auto start=std::chrono::steady_clock::now();
        cruisn::exotica_future::Result sources;
        if(!cruisn::exotica_future::build(read,sources,partial!=0))throw std::runtime_error("source boundary");
        const auto ready=std::chrono::steady_clock::now();
        cruisn::exotica_scene::Result scene;
        if(!cruisn::exotica_scene::build(sources.sources,p,read,model_read,[](const cruisn::exotica_future::Source &s){return s.future;},scene))
            throw std::runtime_error("scene assembly rejected");
        const auto end=std::chrono::steady_clock::now();
        const std::string prefix=argv[6];write(prefix+"-quads.bin",scene.quads);
        std::vector<std::array<uint32_t,11>> instances;
        for(const auto &s:scene.instances)instances.push_back({{s.entry,s.source,s.descriptor,s.base,s.count,s.band,s.palette,s.palette_control,
            uint32_t(s.depth),uint32_t(s.first_quad),uint32_t(s.quad_count)}});
        write(prefix+"-instances.bin",instances);
        std::cout<<std::setprecision(9)<<"{\"passed\":true,\"sources\":"<<sources.sources.size()<<",\"instances\":"<<scene.instances.size()
            <<",\"quads\":"<<scene.quads.size()<<",\"viewport_quads\":"<<scene.viewport_polygons
            <<",\"model_words_read\":"<<scene.model_words_read<<",\"selected\":"<<scene.selected
            <<",\"unsupported_transform\":"<<scene.unsupported_transform<<",\"culled_distance\":"<<scene.culled_distance
            <<",\"culled_bounds\":"<<scene.culled_bounds
            <<",\"maximum_depth\":"<<scene.maximum_depth
            <<",\"source_microseconds\":"<<std::chrono::duration_cast<std::chrono::microseconds>(ready-start).count()
            <<",\"assembly_microseconds\":"<<std::chrono::duration_cast<std::chrono::microseconds>(end-ready).count()<<"}\n";
    }
    catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
