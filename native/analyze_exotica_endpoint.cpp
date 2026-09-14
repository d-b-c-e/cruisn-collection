// SPDX-License-Identifier: BSD-3-Clause
// Bounded LOCAL operand stream. No MAME linkage, guest writes or resource uploads.
#include "exotica_model_endpoint.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <cctype>
static uint32_t word()
{
    std::cin>>std::ws;uint64_t value=0;unsigned digits=0;
    while(std::cin.peek()>='0' && std::cin.peek()<='9') {
        value=value*10+unsigned(std::cin.get()-'0');
        if(++digits>10 || value>UINT32_MAX)throw std::runtime_error("32-bit operand");
    }
    if(!digits || (std::cin.peek()!=std::char_traits<char>::eof() && !std::isspace(static_cast<unsigned char>(std::cin.peek()))))
        throw std::runtime_error("operand token");
    return uint32_t(value);
}
template<class T> void words(T &values){for(auto &v:values)v=word();}
template<class T> void floats(T &values){for(auto &v:values){uint32_t w=word();std::memcpy(&v,&w,4);}}
static void write(const std::string &path,const std::vector<cruisn::zeus_model::Quad> &quads)
{
    std::ofstream stream(path,std::ios::binary);
    if(!stream.write(reinterpret_cast<const char *>(quads.data()),quads.size()*sizeof(quads[0])))throw std::runtime_error("quad write");
    stream.close();if(!stream)throw std::runtime_error("quad close");
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    try {
        uint32_t prior=0;unsigned rows=0;size_t total_words=0;
        for(;;) {
            std::cin>>std::ws;if(std::cin.peek()==std::char_traits<char>::eof())return rows?0:2;
            const uint32_t id=word(),frame=word(),base=word(),count=word(),policy=word();
            if(++rows>4096 || id<=prior || count>0xc800)throw std::runtime_error("model budget/order");
            prior=id;
            cruisn::zeus_state::Context c;
            c.quad_size=word();c.ucode=word();c.palette=word();c.texture=word();c.yscale=word();c.zoffset=word();
            floats(c.matrix);floats(c.translation);floats(c.light);words(c.regs);words(c.render);
            cruisn::exotica_state::Operands a;a.flags=word();a.palette_setup=word();
            words(a.object);words(a.cache);words(a.constants);words(a.commands);words(a.programs);
            for(auto &body:a.bodies)words(body);
            const auto defaults=word();if(!defaults || defaults>16)throw std::runtime_error("defaults budget");
            a.defaults.resize(defaults);words(a.defaults);
            const size_t n=2*(size_t(count)+1);total_words+=n;
            if(total_words>4*1024*1024)throw std::runtime_error("total model words");
            std::vector<uint32_t> model(n);words(model);cruisn::exotica_endpoint::Result result;
            if(!cruisn::exotica_endpoint::prepare(c,frame,base,count,policy,model,a,result))return 1;
            const auto prefix=std::string(argv[1])+"-"+std::to_string(id);
            write(prefix+"-original.bin",result.original);write(prefix+"-endpoint.bin",result.replacement);
            std::cout<<id<<' '<<result.original.size()<<' '<<result.changed<<'\n';
        }
    } catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 2;}
}
