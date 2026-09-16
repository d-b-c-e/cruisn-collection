#include "vunit_journal_policy.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
int main(int argc,char **argv)
{
 using namespace cruisn;
 std::map<std::string,std::string> values={{"MIDV_HOST_RUNTIME","continuous"},{"MIDV_HOST_BOOTSTRAP","1"},{"MIDV_GL","1"},{"MIDV_FFB","0"}};
 auto lookup=[&](const char *key)->const char*{auto it=values.find(key);return it==values.end()?nullptr:it->second.c_str();};
 DiagnosticJournal::Policy policy;
 assert(vunit_journals::select(nullptr,lookup,policy)&&policy==DiagnosticJournal::Policy::capture);
 assert(vunit_journals::select("quiet",lookup,policy)&&policy==DiagnosticJournal::Policy::quiet);
 for(const auto *key:{"MIDV_WORLD_HOST_QUADS","MIDV_USA_HOST_QUADS","MIDV_OFFROAD_HOST_QUADS","MIDV_WORLD_HOST_FADE_METADATA","MIDV_GL_ORIGINAL_MIRROR"}) {
  values[key]="1";assert(!vunit_journals::select("quiet",lookup,policy));values.erase(key);
 }
 values["MIDV_WORLD_HOST_SCENERY"]="2";assert(!vunit_journals::select("quiet",lookup,policy));
 values["MIDV_WORLD_HOST_QUADS"]="0";assert(vunit_journals::select("quiet",lookup,policy));
 values.erase("MIDV_HOST_RUNTIME");assert(!vunit_journals::select("quiet",lookup,policy));
 assert(!vunit_journals::select("invalid",lookup,policy));
 const uint64_t seed=vunit_journals::seed;
 assert(vunit_journals::fold(seed,1,0,2,3)!=vunit_journals::fold(seed,1,1,2,3));
 assert(vunit_journals::fold(seed,1,0,2,3)!=vunit_journals::fold(seed,1,0,3,2));
 if(argc==2) {
  std::ifstream input(argv[1]);assert(input);
  uint64_t hash=seed,frame,page,count,geometry,rows=0;
  while(input>>frame>>page>>count>>geometry) {hash=vunit_journals::fold(hash,frame,page,count,geometry);++rows;}
  assert(input.eof() && rows);std::cout<<rows<<' '<<std::hex<<hash<<'\n';
 } else assert(argc==1);
}
