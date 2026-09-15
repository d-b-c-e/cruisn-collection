// SPDX-License-Identifier: BSD-3-Clause
#include "diagnostic_journal.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <string>

int main(int argc,char **argv) {
    assert(argc==1 || argc==2);
    const std::string path=argc==2?argv[1]:std::string(argv[0])+".journal.tmp";
    {std::ifstream existing(path,std::ios::binary);assert(!existing.good());}
    using Journal=cruisn::DiagnosticJournal;
    Journal capture;
    assert(!capture && !capture.capturing());
    assert(capture.open(path.c_str(),"wb",Journal::Policy::capture));
    assert(capture && capture.capturing());
    assert(capture.buffer(nullptr,_IOFBF,4096)==0);
    assert(capture.print("frame,%s\n%u,%d", "value",42U,-7)==17);
    assert(capture.put('\n')=='\n');
    const unsigned char payload[]={0,1,0xff};
    assert(capture.write(payload,1,sizeof(payload))==sizeof(payload));
    assert(!capture.open(path.c_str(),"wb",Journal::Policy::quiet)); // cannot truncate/reconfigure active capture
    assert(capture.tell()==21 && capture.flush()==0 && !capture.error());
    assert(capture.close()==0 && !capture && !capture.capturing());
    std::ifstream source(path,std::ios::binary);
    std::string bytes((std::istreambuf_iterator<char>(source)),std::istreambuf_iterator<char>());
    const std::string expected=std::string("frame,value\n42,-7\n")+std::string(reinterpret_cast<const char *>(payload),3);
    assert(bytes==expected);source.close();
    Journal quiet;
    assert(quiet.open((path+"/nonexistent/output").c_str(),"wb",Journal::Policy::quiet));
    assert(quiet && !quiet.capturing());
    int formatted=123;assert(quiet.print("%n",&formatted)==0 && formatted==123); // formatting is skipped
    assert(quiet.write(payload,1,3)==3 && quiet.put('\n')=='\n');
    assert(quiet.tell()==0 && quiet.flush()==0 && quiet.close()==0 && !quiet);
    Journal missing;
    assert(!missing.open((path+"/nonexistent/output").c_str(),"wb",Journal::Policy::capture));
    assert(!missing && missing.error()); // capture failure never silently enables runtime
    Journal invalid;
    assert(invalid.open(path.c_str(),"wb",Journal::Policy::quiet));
    assert(invalid.write(payload,2,std::numeric_limits<size_t>::max())==0 && invalid.error());
    assert(invalid.close()==EOF);
    std::remove(path.c_str());
}
