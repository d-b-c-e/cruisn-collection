#include "vunit_far_coverage.h"
#include "scenery_c31.h"
#include <cassert>
#include <limits>
using namespace cruisn::vunit_far;
int main()
{
    const std::array<Point,4> xy={{{{0,0}},{{100,0}},{{100,100}},{{0,100}}}};
    const std::array<double,4> z={{100,300,300,100}};
    Mask m{};
    assert(coverage(xy,z,400,m) && m==Mask{});
    assert(coverage(xy,z,50,m) && m[0]==-1);
    assert(coverage(xy,z,200,m) && m[0]==4);
    const Mask expected={{4,0,0,0,0,0,75,0,75,100,0,100,0,0,0,0}};
    assert(m==expected); // World-linear 0.5 would incorrectly clip at x=50.
    auto alternating=z;alternating={{100,300,100,300}};
    assert(coverage(xy,alternating,200,m) && m[0]==6);
    assert(coverage(xy,{{200,200,200,200}},200,m) && m[0]==-1);
    auto triangle=xy;triangle[3]=triangle[2];
    assert(coverage(triangle,{{100,300,300,300}},200,m) && m[0]>=3);
    const double bad[]={0,-1,1e10,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()};
    for(auto v:bad) {
        m.fill(9);assert(!coverage(xy,z,v,m) && m==Mask{});
        auto depths=z;depths[2]=v;m.fill(9);assert(!coverage(xy,depths,200,m) && m==Mask{});
    }
    auto invalid=xy;invalid[1][0]=65537;
    assert(!coverage(invalid,z,200,m) && m==Mask{});
    Input input;input.far=240000;
    const auto word=[](int n){return cruisn::scenery::Float::integer(n).store();};
    input.words={{word(200000),word(300000),word(300000),word(200000)}};
    std::array<double,4> decoded;
    assert(decode(input,decoded) && decoded[0]==200000 && decoded[1]==300000);
    input.far=160000;assert(!decode(input,decoded));input.far=240000;
    for(int n:{999,480000,-200000}){auto bad_input=input;bad_input.words[0]=word(n);assert(!decode(bad_input,decoded));}
    input.words.fill(word(200000));assert(!decode(input,decoded));
    input.words.fill(word(300000));assert(!decode(input,decoded));
    invalid=xy;invalid[2][1]=std::numeric_limits<float>::quiet_NaN();
    assert(!coverage(invalid,z,200,m) && m==Mask{});
}
