// SPDX-License-Identifier: BSD-3-Clause
// LOCAL snapshots only. Queue every owned packet before reconstructing images.
#include "page_image.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

using Image = cruisn::PageImage<16777216, 4096>;

static std::vector<uint8_t> read(const std::string &path, std::size_t limit) {
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    if (!stream || stream.tellg() < 0 || uint64_t(stream.tellg()) > limit)
        throw std::runtime_error("input size");
    std::vector<uint8_t> bytes(std::size_t(stream.tellg()), uint8_t(0));
    stream.seekg(0);
    if (!bytes.empty() && !stream.read(reinterpret_cast<char *>(bytes.data()), bytes.size()))
        throw std::runtime_error("input read");
    return bytes;
}
static void write(const std::string &path, const std::vector<uint8_t> &bytes) {
    std::ofstream stream(path, std::ios::binary);
    if (!stream.write(reinterpret_cast<const char *>(bytes.data()), bytes.size()))
        throw std::runtime_error("output write");
    stream.close();
    if (!stream) throw std::runtime_error("output close");
}

int main(int argc, char **argv) {
    try {
        // --stage OUTPUT_PREFIX IMAGE... or --replay OUTPUT_PREFIX PACKET...
        if (argc < 4 || argc > 11) throw std::runtime_error("one to eight inputs required");
        const bool stage = std::string(argv[1]) == "--stage";
        if (!stage && std::string(argv[1]) != "--replay") throw std::runtime_error("mode");
        Image producer, consumer;
        std::vector<std::vector<uint8_t>> queue;
        for (int i = 3; i < argc; ++i) {
            auto bytes = read(argv[i], stage ? 16777216 : Image::maximum_packet_bytes);
            if (stage) {
                Image::Packet packet;
                if (!producer.stage(bytes.data(), bytes.size(), packet) || !producer.apply(packet) ||
                    producer.bytes() != bytes || !Image::encode(packet, bytes))
                    throw std::runtime_error("producer ownership");
            }
            queue.push_back(std::move(bytes));
        }
        std::vector<std::size_t> counts;
        for (std::size_t i = 0; i < queue.size(); ++i) {
            Image::Packet packet;
            if (!Image::decode(queue[i].data(), queue[i].size(), packet) || !consumer.apply(packet))
                throw std::runtime_error("consumer packet");
            const auto prefix = std::string(argv[2]) + "-" + std::to_string(i);
            write(prefix + ".pim", queue[i]);
            write(prefix + ".bin", consumer.bytes());
            counts.push_back(packet.pages.size());
        }
        std::cout << "{\"passed\":true,\"page_counts\":[";
        for (std::size_t i = 0; i < counts.size(); ++i) std::cout << (i ? "," : "") << counts[i];
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
