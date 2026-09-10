// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_transform.h"
#include <cassert>
#include <iostream>
int main(){
 uint32_t seed=0x753afb21;auto next=[&](){seed=seed*1664525U+1013904223U;return seed;};
 for(unsigned i=0;i<10000;++i){
  std::array<uint32_t,3> position,camera;std::array<uint32_t,9> view,rotation,alternate;
  for(auto &v:position)v=next();
  for(auto &v:camera)v=next();
  for(auto &v:view)v=next();
  for(auto &v:rotation)v=next();
  for(auto &v:alternate)v=next();
  for(uint32_t flags:{0U,3U,0x80000U,0x80003U,0x80U,1U,2U}){
   cruisn::exotica_transform::Prepared full;int32_t depth=0;
   bool a=cruisn::exotica_transform::prepare(position,camera,view,rotation,alternate,flags,full);
   bool b=cruisn::exotica_transform::camera_depth(position,camera,view,flags,depth);
   assert(a==b);if(a)assert(depth==full.depth);
  }
 }
 std::cout<<"PASS70000 full/early depth decisions across flags and arbitrary C31 operands\n";
}
