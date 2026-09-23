#pragma once

#include <cstdint>

namespace cruisn::zeus_display {

struct Rect {
	int32_t left, top, right, bottom;
};

enum class Mode { invalid, full_monitor, center_of_three };

struct Selection {
	Rect rect;
	Mode mode;
};

// A merged triple display exposes one monitor to Windows. An explicit
// single-panel target may use its center third; all other mismatches fail.
inline Selection select(Rect monitor, int width, int height) noexcept
{
	int64_t const actual_width = int64_t(monitor.right) - monitor.left;
	int64_t const actual_height = int64_t(monitor.bottom) - monitor.top;
	if (width < 320 || height < 240 || actual_width <= 0 || actual_height <= 0)
		return {{}, Mode::invalid};
	if (actual_width == width && actual_height == height)
		return {monitor, Mode::full_monitor};
	if (actual_width == int64_t(width) * 3 && actual_height == height)
		return {{int32_t(int64_t(monitor.left) + width), monitor.top,
			int32_t(int64_t(monitor.left) + int64_t(width) * 2), monitor.bottom},
			Mode::center_of_three};
	return {{}, Mode::invalid};
}

} // namespace cruisn::zeus_display
