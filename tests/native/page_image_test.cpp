#include "page_image.h"
#include <cassert>
#include <iostream>
int main() {
 using Image=cruisn::PageImage<16,4>;
 Image producer,consumer;Image::Packet first,second,third;
 std::array<uint8_t,16> a{};
 assert(!producer.stage(nullptr,16,first) && !producer.stage(a.data(),15,first));
 assert(producer.stage(a.data(),16,first));assert(first.full && first.pages.size()==4);
 assert(producer.bytes().empty() && producer.generation()==0);
 assert(producer.apply(first));a[5]=73;
 assert(producer.stage(a.data(),16,second) && second.pages.size()==1 && second.pages[0].index==1);
 assert(producer.apply(second));a[5]=91;a[15]=250;
 assert(producer.stage(a.data(),16,third) && third.pages.size()==2);assert(producer.apply(third));
 assert(!consumer.apply(second) && consumer.bytes().empty() && consumer.generation()==0);
 assert(consumer.apply(first));assert(consumer.bytes()[5]==0);
 const auto original=consumer.bytes();
 for(unsigned kind=0;kind<9;++kind) {
  auto invalid=second;
  if(kind==0)invalid.pages.push_back(invalid.pages.front());
  if(kind==1)invalid.pages[0].index=4;
  if(kind==2)invalid.generation=3;
  if(kind==3)invalid.full=true;
  if(kind==4)invalid.base=0;
  if(kind==5)invalid.pages.clear();
  if(kind==6)invalid.pages[0].bytes[0]^=1;
  if(kind==7)invalid.result_hash^=1;
  if(kind==8)invalid.base_hash^=1;
  assert(!consumer.apply(invalid));assert(consumer.bytes()==original && consumer.generation()==1);
 }
 assert(consumer.apply(second));assert(consumer.bytes()[5]==73);
 assert(!consumer.apply(second));assert(consumer.apply(third));assert(consumer.bytes()==producer.bytes());
 Image::Packet unchanged;assert(producer.stage(a.data(),16,unchanged) && unchanged.pages.empty());
 assert(producer.apply(unchanged) && consumer.apply(unchanged));assert(producer.bytes()==consumer.bytes());
 auto incomplete=first;incomplete.pages.pop_back();Image fresh;
 assert(!fresh.apply(incomplete) && fresh.bytes().empty());

 // A dropped staging result must not silently advance the producer baseline.
 Image dropped; Image::Packet abandoned, retry;
 assert(dropped.stage(a.data(),16,abandoned));
 a[0]=113; assert(dropped.stage(a.data(),16,retry));
 assert(retry.full && retry.base==0 && retry.generation==1);
 assert(dropped.apply(retry) && dropped.bytes()[0]==113);
 // Wire records own every page independently of both source and typed packet.
 std::vector<uint8_t> wire;
 assert(Image::encode(first,wire));
 assert(wire.size()==96 && wire[0]=='P' && wire[1]=='I' && wire[2]=='M' && wire[3]=='1');
 Image::Packet decoded;
 assert(Image::decode(wire.data(),wire.size(),decoded));
 first.pages[0].bytes[0]=199;
 Image replay; assert(replay.apply(decoded) && replay.bytes()[0]==0);
 for(size_t size=0;size<wire.size();++size) {
  auto sentinel=second;
  assert(!Image::decode(wire.data(),size,sentinel));
  assert(sentinel.generation==second.generation && sentinel.pages[0].bytes==second.pages[0].bytes);
 }
 for(unsigned kind=0;kind<12;++kind) {
  auto bad=wire;
  if(kind==0)bad[0]^=1;
  if(kind==1)bad[4]^=1;
  if(kind==2)bad[8]^=1;
  if(kind==3)bad[12]=255;
  if(kind==4)bad[48]=2;
  if(kind==5)bad[52]=1;
  if(kind==6)bad[56]=1;
  if(kind==7)bad[60]=1;
  if(kind==8)bad[72]=0; // duplicate second page index
  if(kind==9)bad[64]=4; // out of range
  if(kind==10)bad[24]=0; // wrapped generation
  if(kind==11)bad.push_back(0);
  assert(!Image::decode(bad.data(),bad.size(),decoded));
 }
 assert(Image::encode(third,wire));
 // Corrupt the LAST page: no valid earlier page may be committed first.
 wire.back()^=1;
 Image before_third; assert(Image::encode(second,wire));
 assert(before_third.apply(retry)); // different baseline must reject a same-number delta
 assert(!before_third.apply(second));
 assert(Image::encode(third,wire)); wire.back()^=1;
 assert(Image::decode(wire.data(),wire.size(),decoded));
 Image clean; first.pages[0].bytes[0]=0;
 assert(clean.apply(first) && clean.apply(second));
 const auto stable=clean.bytes(); const auto hash=clean.image_hash();
 assert(!clean.apply(decoded) && clean.bytes()==stable && clean.image_hash()==hash && clean.generation()==2);
 auto wrap=second; wrap.base=UINT64_MAX; wrap.generation=0;
 assert(!Image::encode(wrap,wire) && !clean.apply(wrap));
 std::cout<<"PASS staged ownership, delayed generations and atomic rejection\n";
}
