// SPDX-License-Identifier: BSD-3-Clause
// Conservative model bounds from actual vertices, with outward-rounded IEEE float
// intervals. No model resources, game sphere assumptions or GPU calls.
#pragma once
#include "zeus_model.h"
#include <limits>
namespace cruisn { namespace zeus_bounds {
struct Bounds { std::array<int32_t,3> low{},high{}; bool empty=true; };
struct Range { float low,high; };
inline float down(float x){return std::nextafter(x,-std::numeric_limits<float>::infinity());}
inline float up(float x){return std::nextafter(x,std::numeric_limits<float>::infinity());}
inline Range point(float x){return {x,x};}
inline Range add(Range a,Range b){return {down(a.low+b.low),up(a.high+b.high)};}
inline Range mul(Range a,Range b) {
 const float v[]={a.low*b.low,a.low*b.high,a.high*b.low,a.high*b.high};
 return {down(*std::min_element(v,v+4)),up(*std::max_element(v,v+4))};
}
inline Range divide(Range a,Range b) {
 const float v[]={a.low/b.low,a.low/b.high,a.high/b.low,a.high/b.high};
 return {down(*std::min_element(v,v+4)),up(*std::max_element(v,v+4))};
}
inline bool finite(Range r){return std::isfinite(r.low)&&std::isfinite(r.high)&&r.low<=r.high;}
inline bool prepare(const std::vector<uint32_t> &words,uint32_t size,Bounds &result) {
 result=Bounds{};if(words.size()%2 || words.size()>2*(0xc800+1) || (size!=10&&size!=12&&size!=14))return false;
 Bounds out;
 for(size_t i=0;i<words.size();) {
  const auto *d=&words[i];const uint32_t op=d[0]>>24,n=op==0x38?size:2;
  if(n>words.size()-i)return false;
  i+=n;
  if(op==0||op==0x22)continue;
  if(op==0x36) {if(((d[0]>>16)&127)!=0x20 || d[1]>>24>=80 || d[1]>>24==8)return false;continue;}
  if(op!=0x38)return false;
  const int32_t v[4][3]={{int16_t(d[2]),int16_t(d[3]),int16_t(d[6])},
   {int16_t(d[2]>>16),int16_t(d[3]>>16),int16_t(d[6]>>16)},
   {int16_t(d[8]),int16_t(d[9]),int16_t(d[7])},
   {int16_t(d[8]>>16),int16_t(d[9]>>16),int16_t(d[7]>>16)}};
  for(const auto &p:v) {for(unsigned j=0;j<3;++j) {
   if(out.empty)out.low[j]=out.high[j]=p[j];
   else {out.low[j]=std::min(out.low[j],p[j]);out.high[j]=std::max(out.high[j],p[j]);}
  }out.empty=false;}
 }
 result=out;return true;
}
// Uncertain/nonfinite/near-plane-crossing bounds fail open. Original decoding
// remains responsible for validation, clipping and exact polygon output.
inline bool outside(const Bounds &b,const zeus_model::Context &c,float margin,
 float maximum_depth=std::numeric_limits<float>::infinity()) {
 if(!std::isfinite(margin)||margin<0||margin>256)return false;
 const int exponent=int(c.regs[0x66])-0x8e;
 const int uv_exponent=int(c.regs[0x68])-0x9d;
 if(exponent<-31||exponent>31||uv_exponent<-31||uv_exponent>31||
    c.regs[0x6c]>30||c.yscale>1||c.render_policy>7)return false;
 const float clip=zeus_model::word_float(c.regs[0x78]);
 const float ox=zeus_model::word_float(c.regs[0x6a]),oy=zeus_model::word_float(c.regs[0x6b]);
 if(!std::isfinite(clip)||!std::isfinite(ox)||!std::isfinite(oy))return false;
 for(float f:c.matrix)if(!std::isfinite(f))return false;
 for(float f:c.translation)if(!std::isfinite(f))return false;
 if(b.empty)return true;
 const float scale=std::ldexp(1.f,exponent);Range local[3],v[3];
 for(unsigned j=0;j<3;++j){local[j]={float(b.low[j])*scale,float(b.high[j])*scale};if(!finite(local[j]))return false;}
 for(unsigned row=0;row<3;++row) {
  v[row]=add(add(add(mul(local[0],point(c.matrix[row*3])),mul(local[1],point(c.matrix[row*3+1]))),
   mul(local[2],point(c.matrix[row*3+2]))),point(c.translation[row]));
  if(!finite(v[row]))return false;
 }
 if(v[2].high<clip)return true;
 if(v[2].low<std::max(clip,0.f))return false;
 const auto depth=add(mul(v[2],point(4096.f)),point(8388607.f));
 if(!finite(depth)||std::isnan(maximum_depth)||depth.high>=maximum_depth)return false;
 const auto denominator=add(v[2],point(2.f));if(!finite(denominator)||denominator.low<=0)return false;
 const auto factor=divide(point(float(1U<<c.regs[0x6c])),denominator);
 const auto x=add(mul(v[0],factor),point(ox)),y=add(mul(v[1],factor),point(oy));
 if(!finite(factor)||!finite(x)||!finite(y))return false;
 return x.high<-margin || x.low>512+margin || y.high<0 || y.low>400;
}
} }
