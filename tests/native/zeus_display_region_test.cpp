#include "../../native/zeus_display_region.h"

#include <cassert>

using cruisn::zeus_display::Mode;
using cruisn::zeus_display::Rect;
using cruisn::zeus_display::select;

int main()
{
	Rect const physical{2560, 0, 5120, 1440};
	auto full = select(physical, 2560, 1440);
	assert(full.mode == Mode::full_monitor);
	assert(full.rect.left == 2560 && full.rect.right == 5120);

	Rect const merged{0, 0, 7680, 1440};
	auto center = select(merged, 2560, 1440);
	assert(center.mode == Mode::center_of_three);
	assert(center.rect.left == 2560 && center.rect.right == 5120);
	assert(center.rect.top == 0 && center.rect.bottom == 1440);

	Rect const offset{-2560, 100, 5120, 1540};
	center = select(offset, 2560, 1440);
	assert(center.mode == Mode::center_of_three);
	assert(center.rect.left == 0 && center.rect.right == 2560);

	assert(select(merged, 3840, 2160).mode == Mode::invalid);
	assert(select({0, 0, 5120, 1440}, 2560, 1440).mode == Mode::invalid);
	assert(select({0, 0, 0, 1440}, 2560, 1440).mode == Mode::invalid);
	assert(select(physical, 0, 1440).mode == Mode::invalid);
}
