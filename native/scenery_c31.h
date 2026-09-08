// license:BSD-3-Clause
// copyright-holders:Aaron Giles
// Host-only C31 arithmetic, adapted from MAME 320c3x_ops.ipp. No CPU flags/state.
// Full BSD notice: harness/scenery_c31.py. Projection-domain validation uses the
// actual MAME helper bodies and fixtures/scenery/c31-vectors.json.xz.
#pragma once
#include <cstdint>
#include <array>

namespace cruisn { namespace scenery {
struct Float
{
    int32_t m; int e;
    Float(int32_t mantissa=0, int exponent=-128):m(mantissa),e(exponent) {}
    static Float load(uint32_t v) { return Float(int32_t(v<<8),int8_t(v>>24)); }
    uint32_t store() const { return (uint32_t(e&255)<<24)|(uint32_t(m>>8)&0xffffff); }
    Float reload() const { return load(store()); }
    static int leading(uint32_t v) { int n=0; if(!v)return 32; while(!(v&0x80000000)){++n;v<<=1;} return n; }
    static Float integer(int32_t v)
    {
        if(!v)return Float();
        if(v==-1)return Float(INT32_MIN,-1);
        int n=leading(v>0?uint32_t(v):~uint32_t(v));
        return Float(int32_t((uint32_t(v)<<n)^0x80000000),31-n);
    }
    int32_t fix() const
    {
        int shift=31-e;
        if(shift<=0)return m>=0?INT32_MAX:INT32_MIN;
        if(shift>31)return m>>31;
        return (m>>shift)^int32_t(1U<<(31-shift));
    }
    static Float finish(int64_t man,int exp)
    {
        if(!man || exp<=-128)return Float();
        if(exp>127)return Float(man<0?INT32_MIN:INT32_MAX,127);
        return Float(int32_t(uint32_t(man)^0x80000000),exp);
    }
    static Float normalize(int64_t man,int exp)
    {
        if(!man || exp<=-128)return Float();
        while(man>=INT64_C(0x100000000) || man<-INT64_C(0x100000000)){man>>=1;++exp;}
        if(man>=-INT64_C(0x80000000) && man<INT64_C(0x80000000))
        {
            int n=leading(man>0?uint32_t(man):~uint32_t(man));
            man*=INT64_C(1)<<n;exp-=n;
        }
        return finish(man,exp);
    }
    Float operator-() const { return e==-128?Float():normalize(-(int64_t(m)^INT64_C(0x80000000)),e); }
    Float sum(const Float &b,bool sub) const
    {
        int exp=e>b.e?e:b.e;
        if(e-b.e>=32)return *this;
        if(b.e-e>=32)return sub?-b:b;
        int64_t a1=(int64_t(m)^INT64_C(0x80000000))>>(exp-e);
        int64_t b1=(int64_t(b.m)^INT64_C(0x80000000))>>(exp-b.e);
        return normalize(sub?a1-b1:a1+b1,exp);
    }
    Float operator+(const Float &b) const {return e==-128?b:b.e==-128?*this:sum(b,false);}
    Float operator-(const Float &b) const {return b.e==-128?*this:sum(b,true);}
    Float operator*(const Float &b) const
    {
        if(e==-128 || b.e==-128)return Float();
        int32_t a1=(m>>8)^0x800000,b1=(b.m>>8)^0x800000;
        int64_t man=(int64_t(a1)*b1)>>15;int exp=e+b.e;
        while(man>=INT64_C(0x100000000) || man<-INT64_C(0x100000000)){man>>=1;++exp;}
        return finish(man,exp);
    }
};
inline Float dot(const std::array<Float,3> &a,const Float *b)
{return (a[0]*b[0]+a[1]*b[1])+a[2]*b[2];}
} }
