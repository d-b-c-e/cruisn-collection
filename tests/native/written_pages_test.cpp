#include "written_pages.h"
#include "page_image.h"
#include <algorithm>
#include <cassert>
#include <iostream>
int main(){
 using Marks=cruisn::WrittenPages<16,4>;Marks marks;
 assert(marks.pages().empty());assert(marks.mark(3,2));assert((marks.pages()==std::vector<uint32_t>{0,1}));
 assert(marks.mark(15,1));auto saved=marks.pages();
 assert(!marks.mark(16,1)&&!marks.mark(0,17)&&!marks.mark(0,0)&&!marks.mark(SIZE_MAX,1)&&!marks.mark(1,SIZE_MAX));
 assert(marks.pages()==saved);marks.clear();assert(marks.pages().empty());
 marks.mark_all();assert((marks.pages()==std::vector<uint32_t>{0,1,2,3}));marks.clear();
 using Image=cruisn::PageImage<16,4>;Image full,selected;std::array<uint8_t,16> source{};
 for(unsigned i=0;i<1000;++i){
  const auto offset=(i*7)%16;source[offset]^=uint8_t(i);assert(marks.mark(offset,1));
  if(i%23==0){source.fill(uint8_t(i));marks.mark_all();} // save-state restoration bypasses ordinary writes
  Image::Packet a,b;assert(full.stage(source.data(),16,a)&&selected.stage_selected_pages(source.data(),16,marks.pages(),b));
  std::vector<uint8_t>x,y;assert(Image::encode(a,x)&&Image::encode(b,y)&&x==y);
  if(i%7==0){ // abandoned submission preserves ALL marks; a later write extends them
   const auto changed=(offset+9)%16;source[changed]^=73;assert(marks.mark(changed,1));
   assert(full.stage(source.data(),16,a)&&selected.stage_selected_pages(source.data(),16,marks.pages(),b));
   assert(Image::encode(a,x)&&Image::encode(b,y)&&x==y);
  }
 assert(full.apply(a)&&selected.apply(b)&&full.bytes()==selected.bytes());marks.clear();
 }
 Image::Packet sentinel;assert(selected.stage(source.data(),16,sentinel));
 const auto generation=sentinel.generation;
 assert(!selected.stage_selected_pages(nullptr,16,{},sentinel));
 assert(!selected.stage_selected_pages(source.data(),15,{},sentinel));
 assert(!selected.stage_selected_pages(source.data(),16,{1,1},sentinel));
 assert(!selected.stage_selected_pages(source.data(),16,{2,1},sentinel));
 assert(!selected.stage_selected_pages(source.data(),16,{4},sentinel));
 assert(sentinel.generation==generation && sentinel.pages.empty());
 // A forgotten writer notification is detectable by the independent full scan.
 source[7]^=1;Image::Packet complete,missing;
 assert(full.stage(source.data(),16,complete));
 assert(selected.stage_selected_pages(source.data(),16,{},missing));
 assert(complete.result_hash!=missing.result_hash);
 // CPU scene seals and GPU commits consume different intervals of the same
 // writes. Clearing one reader must never lose the other reader's pending data.
 Marks upload,seal;seal.mark_all();std::array<uint8_t,16> live{},sealed{},uploaded{};
 for(unsigned tick=0;tick<1000;++tick) {
  auto offset=(tick*11)%16;live[offset]^=uint8_t(tick+1);
  assert(upload.mark(offset,1) && seal.mark(offset,1));
  if(tick%5==0) {
   for(auto page:upload.pages())std::copy_n(live.begin()+page*4,4,uploaded.begin()+page*4);
   upload.clear();assert(uploaded==live);
  }
  if(tick%7==0) {
   for(auto page:seal.pages())std::copy_n(live.begin()+page*4,4,sealed.begin()+page*4);
   seal.clear();assert(sealed==live);
  }
  if(tick%23==0){live.fill(uint8_t(tick));upload.mark_all();seal.mark_all();}
 }
 // Device's expanded8-byte writes always fit one4KB page, including wrap edges.
 cruisn::WrittenPages<16777216,4096> device;
 for(uint32_t address: {0U,0x3ffU,0x7ff03ffU,0xffffffffU,0x8000400U}){
  const size_t block=address%1024+((address>>16)%2048)*1024;
  assert(device.mark(block*8,8));assert(device.pages().size()==1);device.clear();
 }
 std::cout<<"PASS write ranges, reset coverage, abandoned packets and1000 full/selected identities\n";
}
