#include "capture_writer.h"
#include <cassert>
#include <stdexcept>

int main()
{
    using Writer=cruisn::CaptureWriter;
    std::mutex mutex; std::condition_variable changed;
    bool entered=false, released=false; std::vector<unsigned> order;
    Writer writer(8,[&](const Writer::Request &request) {
        std::unique_lock<std::mutex> lock(mutex); entered=true; changed.notify_all();
        changed.wait(lock,[&]{return released;});
        order.push_back(request.bitmap[0]); return true;
    });
    auto request=[](unsigned value) { Writer::Request r; r.bitmap.assign(4,uint8_t(value)); return r; };
    assert(writer.submit(request(1)));
    { std::unique_lock<std::mutex> lock(mutex); changed.wait(lock,[&]{return entered;}); }
    assert(writer.submit(request(2)));
    // In-flight job still owns half the budget. Admission never waits for I/O.
    assert(!writer.submit(request(3)));
    { std::lock_guard<std::mutex> lock(mutex); released=true; changed.notify_all(); }
    auto stats=writer.finish();
    assert(order==std::vector<unsigned>({1,2}));
    assert(stats.submitted==2 && stats.written==2 && stats.failed==0 && stats.rejected==1 && stats.peak_bytes==8);
    assert(!writer.submit(request(4)));
    assert(writer.finish().rejected==2);
    Writer failed(8,[](const Writer::Request &) -> bool {throw std::runtime_error("write failed");});
    assert(failed.submit(request(1))); auto failure=failed.finish();
    assert(failure.submitted==1 && failure.written==0 && failure.failed==1);
    Writer bad_path; // Actual fopen failure, with no fabricated success receipt.
    assert(bad_path.submit(request(1))); assert(bad_path.finish().failed==1);
    Writer unused; assert(unused.finish().submitted==0);
    entered=false; released=false; std::atomic<bool> pacing{false};
    Writer paced(4,[&](const Writer::Request &) {
        std::unique_lock<std::mutex> lock(mutex); entered=true; changed.notify_all();
        changed.wait(lock,[&]{return released;}); return true;
    });
    assert(paced.submit(request(1)));
    { std::unique_lock<std::mutex> lock(mutex); changed.wait(lock,[&]{return entered;}); }
    // A timed-out admission clears its signal and records a rejection.
    assert(!paced.submit(request(2),1,&pacing)); assert(!pacing.load());
    bool admitted=false;
    std::thread producer([&]{admitted=paced.submit(request(3),1000,&pacing);});
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(1);
    while (!pacing.load() && std::chrono::steady_clock::now()<deadline) std::this_thread::yield();
    assert(pacing.load());
    { std::lock_guard<std::mutex> lock(mutex); released=true; changed.notify_all(); }
    producer.join(); auto p= paced.finish();
    assert(admitted && !pacing.load() && p.written==2 && p.rejected==1 && p.waits==2 && p.wait_us>0);
}
