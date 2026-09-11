// Replay actual worker observations, including its separately sampled clocks.
// This verifies conditioning, not the asynchronous mailbox or physical torque.
#include "force_profile.h"
#include "impact_mixer.h"
#include <cmath>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool ok, const char *why) { if (!ok) throw std::runtime_error(why); }
static double number(std::string const &s) {
    size_t used=0; double v=std::stod(s,&used);
    require(used==s.size() && std::isfinite(v),"invalid finite number"); return v;
}
static long long integer(std::string const &s, long long lo, long long hi) {
    size_t used=0; long long v=std::stoll(s,&used);
    require(used==s.size() && v>=lo && v<=hi,"invalid integer"); return v;
}
static void equal(float actual, std::string const &recorded, const char *why) {
    require(actual==float(number(recorded)),why);
}
int main(int argc, char **argv) {
    unsigned long long count=0;
    try {
        require(argc==9,"ticks profiles profile strength smoothing_ms hold_ms impact_axis rumble");
        int strength=int(integer(argv[4],0,100)), hold=int(integer(argv[6],0,60000));
        bool enhanced=integer(argv[7],0,1)!=0; int rumble=int(integer(argv[8],0,100));
        double smoothing=number(argv[5]); require(smoothing>=0 && smoothing<=10000,"smoothing range");
        dbce::force::Profile p; std::string why;
        require(dbce::force::load_profile_dir(argv[2],argv[3],p,&why),"profile missing");
        p.shaper.strength=enhanced?50:strength/2; p.shaper.invert=false;
        p.shaper.smoothing_ms=float(smoothing);
        dbce::force::Shaper shaper(p.shaper); dbce::force::RiseDetector detector;
        dbce::force::ImpactMixer mixer;
        std::ifstream f(argv[1],std::ios::binary); require(bool(f),"missing ticks");
        f.seekg(0,std::ios::end); require(f.tellg()>0 && f.tellg()<=64*1024*1024,"tick byte bound"); f.seekg(0);
        std::string line; std::getline(f,line);
        require(line=="sequence,host_seconds,active,before,candidate,cancel,hold_now_ms,last_write_ms,timeout,detector_ms,trigger_ms,mix_ms,dt,event,arrival,rise,shaped,mixed,out,sink_host_seconds,rumble_request","tick schema");
        double last_host=-1, last_sink=-1; long long last_detector=-1; int applied=0;
        unsigned events=0,cancels=0,timeouts=0,sinks=0;
        while (std::getline(f,line)) {
            require(++count<=131072 && !line.empty() && line.size()<2048,"tick record bound");
            std::istringstream row(line); std::vector<std::string> v; std::string part;
            while(std::getline(row,part,',')) v.push_back(part);
            require(v.size()==21 && line.back()!=',',"tick field count");
            require(integer(v[0],1,131072)==static_cast<long long>(count),"tick sequence");
            double host=number(v[1]); require(host>=0 && host>=last_host && host>=last_sink,"host clock"); last_host=host;
            bool active=integer(v[2],0,1)!=0;
            int want=int(integer(v[3],-32767,32767)), candidate=int(integer(v[4],-32767,32767));
            require(active || want==0,"inactive structural input");
            if(integer(v[5],0,1)) { ++cancels; shaper.reset(); detector.reset(); mixer.reset(); }
            long long hold_now=integer(v[6],-1,86400000), last_write=integer(v[7],-1,86400000);
            bool timed=false;
            if(hold>0 && want) { require(hold_now>=0 && last_write>=0,"watchdog clocks absent"); timed=hold_now-last_write>hold; }
            else require(hold_now==-1 && last_write==-1,"unexpected watchdog clocks");
            require(integer(v[8],0,1)==int(timed),"watchdog decision");
            if(timed) { ++timeouts; want=0; detector.reset(); mixer.reset(); }
            // Enhanced raw input is a later atomic read. It need not match want.
            if(!enhanced) require(candidate==want,"legacy detector input");
            long long when=integer(v[9],0,86400000);
            require(when>=last_detector && when>=static_cast<long long>(host*1000),"detector clock"); last_detector=when;
            bool event=detector.observe(float(candidate)/32767.f,double(when)/1000.);
            require(integer(v[13],0,1)==int(event),"impact decision");
            equal(detector.last_arrival,v[14],"arrival mismatch"); equal(detector.last_rise,v[15],"rise mismatch");
            long long trigger=integer(v[10],-1,86400000), mix=integer(v[11],-1,86400000);
            if(event) ++events;
            if(event && enhanced) { require(trigger>=when,"trigger clock"); mixer.trigger(detector.last_arrival,float(candidate),double(trigger)/1000.); }
            else require(trigger==-1,"unexpected trigger clock");
            float dt=float(number(v[12])); require(dt>=0 && dt<=86400,"shaper dt");
            float shaped=shaper.shape(float(want)/32767.f,0.f,dt,false), mixed=shaped;
            if(enhanced) { require(mix>=when && mix>=trigger,"mix clock"); mixed=mixer.mix(shaped,double(mix)/1000.,float(strength)/100.f); }
            else require(mix==-1,"unexpected mix clock");
            equal(shaped,v[16],"shaped mismatch"); equal(mixed,v[17],"mixed mismatch");
            int out=int(std::lround(double(mixed)*32767.));
            require(integer(v[18],-32767,32767)==out,"quantization mismatch");
            double sink=number(v[19]);
            if(out!=applied) { require(sink>=host && sink>=last_sink,"sink clock missing"); last_sink=sink; applied=out; ++sinks; }
            else require(sink==-1,"unchanged output sent");
            float desired=event && !enhanced ? detector.last_arrival*float(rumble)/100.f*float(strength)/100.f : 0.f;
            equal(desired,v[20],"desired rumble mismatch");
        }
        require(f.eof() && count>0,"incomplete/empty ticks");
        std::printf("{\"passed\":true,\"ticks\":%llu,\"events\":%u,\"cancels\":%u,\"timeouts\":%u,\"sink_changes\":%u,\"last_output\":%d,\"last_host_seconds\":%.17g,\"physical_acceptance\":false}\n",count,events,cancels,timeouts,sinks,applied,last_host);
        return 0;
    } catch(std::exception const &e) { std::fprintf(stderr,"tick %llu: %s\n",count,e.what()); return 1; }
}
