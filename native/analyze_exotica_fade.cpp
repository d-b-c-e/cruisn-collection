#include "exotica_fade.h"
#include <iostream>
int main()
{
    unsigned n=0;
    for (;;)
    {
        std::cin>>std::ws;
        if(std::cin.peek()==std::char_traits<char>::eof())return n?0:2;
        uint64_t a,b,c;
        if(!(std::cin>>a>>b>>c) || ++n>8192 ||
            a>0xffffffff || b>0xffffffff || c>0xffffffff)return 2;
        cruisn::ExoticaFadeStep out;
        if(!cruisn::exotica_fade_step(uint32_t(a),uint32_t(b),uint32_t(c),out))return 1;
        std::cout<<out.packed<<" "<<out.flags<<" "<<out.completed<<"\n";
    }
}
