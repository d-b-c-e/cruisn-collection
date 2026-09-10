// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <chrono>
#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <deque>
#include <functional>
#include <mutex>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace cruisn {
// Only already encoded host screenshots enter this queue. No GL context,
// device state, guest memory or borrowed pixel storage reaches the writer.
// The caller owns index until finish() returns. All writes occur in FIFO order.
class CaptureWriter
{
public:
    struct Request {
        std::string path, row;
        std::vector<uint8_t> bitmap;
        FILE *index = nullptr;
    };
    struct Stats {
        uint64_t submitted=0, written=0, failed=0, rejected=0;
        uint64_t peak_bytes=0, write_total_us=0, write_max_us=0, drain_us=0, waits=0, wait_us=0;
    };
    using Sink = std::function<bool(const Request &)>;
    explicit CaptureWriter(uint64_t limit=512u*1024u*1024u, Sink sink=write)
        : m_limit(limit), m_sink(std::move(sink)) {}
    ~CaptureWriter() { finish(); }
    CaptureWriter(const CaptureWriter &) = delete;
    CaptureWriter &operator=(const CaptureWriter &) = delete;

    // Ordinary admission is nonblocking. Explicit offline pacing may wait for
    // capacity with a caller-owned signal and deadline. In-flight storage
    // is included in the byte/job budgets, not just the waiting deque.
    bool submit(Request &&request, unsigned wait_ms=0, std::atomic<bool> *pacing=nullptr)
    {
        std::unique_lock<std::mutex> lock(m_mutex);
        const auto fits=[&]{return request.bitmap.size()<=m_limit-m_bytes && m_jobs<32;};
        if (!m_stop && !request.bitmap.empty() && request.bitmap.size()<=m_limit && !fits() && wait_ms && pacing) {
            struct Signal { std::atomic<bool> *flag; ~Signal(){flag->store(false);} } signal{pacing};
            const auto began=Clock::now(); pacing->store(true); ++m_stats.waits;
            m_space.wait_for(lock,std::chrono::milliseconds(wait_ms),[&]{return m_stop || fits();});
            m_stats.wait_us+=elapsed(began);
        }
        if (m_stop || request.bitmap.empty() || !fits()) {
            ++m_stats.rejected; return false;
        }
        if (!m_thread.joinable()) m_thread=std::thread(&CaptureWriter::run,this);
        m_bytes+=request.bitmap.size(); ++m_jobs; ++m_stats.submitted;
        if (m_bytes>m_stats.peak_bytes) m_stats.peak_bytes=m_bytes;
        m_queue.push_back(std::move(request)); m_ready.notify_one(); return true;
    }
    Stats finish()
    {
        const auto began=Clock::now();
        { std::lock_guard<std::mutex> lock(m_mutex); m_stop=true; m_ready.notify_one(); m_space.notify_all(); }
        if (m_thread.joinable()) {
            m_thread.join();
            m_stats.drain_us=elapsed(began);
        }
        return m_stats;
    }
private:
    using Clock=std::chrono::steady_clock;
    static uint64_t elapsed(Clock::time_point began)
    { return uint64_t(std::chrono::duration_cast<std::chrono::microseconds>(Clock::now()-began).count()); }
    static bool write(const Request &request)
    {
        FILE *file=std::fopen(request.path.c_str(),"wb");
        if (!file) return false;
        const bool written=std::fwrite(request.bitmap.data(),1,request.bitmap.size(),file)==request.bitmap.size();
        const bool closed=std::fclose(file)==0;
        if (!written || !closed) return false;
        // A row is published only after the complete BMP has closed successfully.
        if (!request.row.empty()) {
            if (!request.index) return false;
            const bool indexed=std::fwrite(request.row.data(),1,request.row.size(),request.index)==request.row.size();
            const bool flushed=std::fflush(request.index)==0;
            if (!indexed || !flushed) return false;
        }
        return true;
    }
    void run()
    {
        for (;;) {
            Request request;
            {
                std::unique_lock<std::mutex> lock(m_mutex);
                m_ready.wait(lock,[&]{ return m_stop || !m_queue.empty(); });
                if (m_queue.empty()) return;
                request=std::move(m_queue.front()); m_queue.pop_front();
            }
            const auto began=Clock::now(); bool success=false;
            try { success=m_sink(request); } catch (...) { success=false; }
            const auto duration=elapsed(began);
            const size_t bytes=request.bitmap.size();
            std::vector<uint8_t>().swap(request.bitmap);
            {
                std::lock_guard<std::mutex> lock(m_mutex);
                if (success) ++m_stats.written; else ++m_stats.failed;
                m_stats.write_total_us+=duration;
                if (duration>m_stats.write_max_us) m_stats.write_max_us=duration;
                m_bytes-=bytes; --m_jobs; m_space.notify_all();
            }
        }
    }
    uint64_t m_limit, m_bytes=0; unsigned m_jobs=0; bool m_stop=false;
    Sink m_sink; Stats m_stats; std::deque<Request> m_queue;
    std::mutex m_mutex; std::condition_variable m_ready, m_space; std::thread m_thread;
};
} // namespace cruisn
