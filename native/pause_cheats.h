// Shared, interpreter-free pause-menu model. Only Lua on the emulation thread
// executes requests, at the next recorded frame boundary after Resume.
#pragma once
#include <algorithm>
#include <mutex>
#include <string>
#include <vector>

namespace cruisn {
struct cheat_row {
    int index = 0, steps = 0;
    std::string description, comment, kind;
    std::vector<std::string> choices;
};
struct cheat_request {
    int index, steps;
    bool activate;
    cheat_request(int i, int s, bool a) : index(i), steps(s), activate(a) {}
};
class cheat_mailbox {
    std::mutex mutex;
    std::vector<cheat_row> rows;
    std::vector<cheat_request> requests;
    bool readonly = false;
public:
    void publish(std::vector<cheat_row> next, bool locked) {
        std::lock_guard<std::mutex> lock(mutex);
        rows = std::move(next); readonly = locked;
    }
    std::vector<cheat_row> snapshot(bool &locked) {
        std::lock_guard<std::mutex> lock(mutex);
        locked = readonly; return rows;
    }
    void submit(std::vector<cheat_request> const &next) {
        std::lock_guard<std::mutex> lock(mutex);
        if (!readonly) requests.insert(requests.end(), next.begin(), next.end());
    }
    std::vector<cheat_request> take() {
        std::lock_guard<std::mutex> lock(mutex);
        std::vector<cheat_request> result; result.swap(requests); return result;
    }
};
// Function-local static is shared across translation units (C++11 ODR).
inline cheat_mailbox &cheat_bus() { static cheat_mailbox bus; return bus; }

class pause_cheats {
public:
    std::vector<cheat_row> rows;
    std::vector<cheat_request> pending;
    bool open = false, readonly = false;
    int selected = 0;
    void begin_pause() {
        rows = cheat_bus().snapshot(readonly);
        pending.clear(); selected = 0; open = false;
    }
    void resume() { cheat_bus().submit(pending); pending.clear(); open = false; }
    void cancel() { pending.clear(); open = false; }
    void move(int direction) {
        // Last row is Back; even an empty catalog has a working way out.
        selected = (selected + int(rows.size()) + 1 + direction) % (int(rows.size()) + 1);
    }
    void change(int direction, bool enter) {
        if (selected == int(rows.size())) { if (enter) open = false; return; }
        if (readonly || pending.size() >= 256) return;
        auto &row = rows[selected];
        if (row.kind == "text" || row.choices.empty()) return;
        bool const shot = row.kind == "oneshot" || row.kind == "oneshot_parameter";
        if (shot && enter) {
            if (row.kind == "oneshot_parameter" && row.steps == 0) row.steps = 1;
            pending.emplace_back(row.index, row.steps, true);
        } else if (row.kind != "oneshot") {
            int const next = std::max(0, std::min(int(row.choices.size()) - 1,
                row.steps + (direction ? direction : (row.steps + 1 == int(row.choices.size()) ? -row.steps : 1))));
            if (next != row.steps) {
                row.steps = next;
                pending.emplace_back(row.index, next, false);
            }
        }
    }
    std::string label(int i) const {
        if (i == int(rows.size())) return "BACK";
        auto const &row = rows[i];
        std::string state = row.choices.empty() ? "INFO" : row.choices.at(row.steps);
        if (row.kind == "oneshot") state = "ENTER TO ACTIVATE";
        else if (row.kind == "oneshot_parameter") state += " / ENTER TO ACTIVATE";
        return row.description + "   [" + state + "]";
    }
};
}
