#include "world_host_layout.h"
#include <cassert>
#include <map>
int main()
{
 for(uint32_t revision:{24u,25u}){
  const auto *p=cruisn::world_host::layout(revision);
  const uint32_t limit=revision==24?0xd58c:0xd586;
  std::map<uint32_t,uint32_t> ram={{0x69,0x08280000|p->scene},
   {revision==24?0x7b55u:0x7b47u,0x08280000|p->pending},
   {revision==24?0x7b5cu:0x7b4eu,0x1ae03000},{p->section,0},{limit,0}};
  auto read=[&](uint32_t address){return ram.at(address);};
  assert(cruisn::world_host::track_reset(read,revision)==(revision==25));
  assert(cruisn::world_host::scene_matches(read,revision)==(revision==25));
  assert(cruisn::world_host::track_reset(read,revision,true));
  assert(cruisn::world_host::scene_matches(read,revision,true));
  ram[0x69]^=1;assert(!cruisn::world_host::scene_matches(read,revision,true));ram[0x69]^=1;
  ram[p->section]=0xc00000;
  assert(!cruisn::world_host::track_reset(read,revision,true));
  assert(!cruisn::world_host::scene_matches(read,revision,true));
  ram[limit]=11;
  assert(cruisn::world_host::scene_matches(read,revision));
  assert(cruisn::world_host::scene_matches(read,revision,true));
  ram[p->section]=0;ram[limit]=1;
  assert(!cruisn::world_host::track_reset(read,revision,true));
  assert(!cruisn::world_host::scene_matches(read,revision,true));
 }
}
