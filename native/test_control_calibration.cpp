#include "control_calibration.h"
#include <cassert>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>

int main(int argc,char **argv)
{
	try {
		if (argc==9) {
			cruisn::control_calibration c{std::string(argv[1])=="pedal",std::string(argv[2])=="1",
				std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]),std::stod(argv[6])};
			double const raw=std::stod(argv[7]);
			std::cout<<std::setprecision(17)<<(std::string(argv[8])=="pass"?raw:cruisn::normalize_control(raw,c))<<'\n';return 0;
		}
		assert(argc==1);
		std::string const prefix="cruisn-calibration-v1\n";
		std::string const row="00112233-4455-6677-8899-aabbccddeeff|11112233-4455-6677-8899-aabbccddeeff|YAXIS|pedal|-1|0|1|0|0\n";
		std::istringstream stream(prefix+row);
		auto const profile=cruisn::parse_control_calibration(stream);
		assert(profile.configured && profile.entries.size()==1);
		std::string const id="A renamed device product_00112233-4455-6677-8899-AABBCCDDEEFF instance_11112233-4455-6677-8899-AABBCCDDEEFF";
		auto const *cal=profile.find(id,1);assert(cal && cruisn::normalize_control(0.,*cal)==.5);
		assert(profile.find(id,0)==nullptr && profile.find("Unrelated device",1)==nullptr);
		assert(cruisn::normalize_control(cruisn::neutral_control_raw(*cal),*cal)==0.);
		auto inverted=*cal;inverted.invert=true;
		assert(cruisn::normalize_control(cruisn::neutral_control_raw(inverted),inverted)==0.);
		for (auto const &bad:{prefix+row+row,std::string("unknown\n")+row,prefix+"bad\n"}) {
			bool rejected=false;try { std::istringstream input(bad);cruisn::parse_control_calibration(input); }
			catch(std::exception const &) { rejected=true; }assert(rejected);
		}
		for (double raw:{-2.,2.,std::numeric_limits<double>::quiet_NaN()}) {
			bool rejected=false;try { cruisn::normalize_control(raw,*cal); }catch(std::exception const &) { rejected=true; }assert(rejected);
		}
		std::cout<<"PASS profile identity/duplicates/schema and neutral invalid-sample boundaries\n";
	} catch(std::exception const &e) { std::cerr<<e.what()<<'\n';return 1; }
}
