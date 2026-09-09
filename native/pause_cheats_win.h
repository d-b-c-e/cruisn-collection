// Windows text rasterization used by both GPU pause menus. No font files or
// cheat descriptions are embedded in a release; strings come from imported XML.
#pragma once
#include "pause_cheats.h"
#include <windows.h>

namespace cruisn {
struct menu_bitmap { int width, height; std::vector<unsigned char> pixels; };
inline menu_bitmap menu_text_bitmap(std::string const &text) {
    int const length = MultiByteToWideChar(CP_UTF8, 0, text.data(), int(text.size()), nullptr, 0);
    std::wstring wide(length, L' ');
    MultiByteToWideChar(CP_UTF8, 0, text.data(), int(text.size()), &wide[0], length);
    HDC dc = CreateCompatibleDC(nullptr);
    HFONT font = CreateFontW(-36, 0, 0, 0, FW_MEDIUM, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, ANTIALIASED_QUALITY,
        DEFAULT_PITCH, L"Segoe UI");
    HGDIOBJ old_font = SelectObject(dc, font);
    SIZE size{}; GetTextExtentPoint32W(dc, wide.data(), length, &size);
    int const w = std::min(1800, int(size.cx) + 16), h = 52;
    BITMAPINFO info{}; info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = w; info.bmiHeader.biHeight = -h;
    info.bmiHeader.biPlanes = 1; info.bmiHeader.biBitCount = 32;
    void *bits = nullptr;
    HBITMAP bitmap = CreateDIBSection(dc, &info, DIB_RGB_COLORS, &bits, nullptr, 0);
    if (!dc || !font || !bitmap || !bits) {
        if (bitmap) DeleteObject(bitmap);
        if (dc && old_font) SelectObject(dc, old_font);
        if (font) DeleteObject(font);
        if (dc) DeleteDC(dc);
        return {1, 1, std::vector<unsigned char>(1, 0)};
    }
    HGDIOBJ old_bitmap = SelectObject(dc, bitmap);
    memset(bits, 0, size_t(w) * h * 4);
    SetBkMode(dc, TRANSPARENT); SetTextColor(dc, RGB(255, 255, 255));
    RECT rect{8, 0, w - 8, h};
    DrawTextW(dc, wide.data(), length, &rect, DT_SINGLELINE | DT_VCENTER | DT_END_ELLIPSIS | DT_NOPREFIX);
    GdiFlush();
    menu_bitmap result{w, h, std::vector<unsigned char>(size_t(w) * h)};
    auto bytes = static_cast<unsigned char const *>(bits);
    for (size_t i = 0; i < result.pixels.size(); ++i) result.pixels[i] = bytes[i * 4];
    SelectObject(dc, old_bitmap); SelectObject(dc, old_font);
    DeleteObject(bitmap); DeleteObject(font); DeleteDC(dc);
    return result;
}

template<class Text>
void draw_pause_cheats(pause_cheats const &menu, Text text) {
    text("CHEATS", .10f, 56.f, true);
    text(menu.readonly ? "REPLAY - recorded cheat actions only" :
        "Changes apply when you resume the game", .19f, 26.f, false);
    int const first = (menu.selected / 8) * 8;
    for (int i = first; i <= int(menu.rows.size()) && i < first + 8; ++i)
        text(menu.label(i), .28f + .060f * (i - first), 32.f, i == menu.selected);
    if (menu.rows.empty()) text("Import a cheat file from the launcher game card first", .39f, 28.f, false);
    if (menu.selected < int(menu.rows.size())) {
        std::string comment = menu.rows[menu.selected].comment;
        std::replace(comment.begin(), comment.end(), '\n', ' ');
        std::replace(comment.begin(), comment.end(), '\r', ' ');
        if (!comment.empty()) text(comment, .79f, 22.f, false);
    }
    text(std::to_string(menu.pending.size()) + " pending actions   |   " +
        std::to_string(menu.selected + 1) + " / " + std::to_string(menu.rows.size() + 1), .85f, 24.f, false);
    text("UP / DOWN Select    LEFT / RIGHT Change    ENTER Select / Activate    ESC Back", .91f, 23.f, false);
}
}
