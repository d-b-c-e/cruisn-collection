// SPDX-License-Identifier: BSD-3-Clause
// Optional evidence output. Enabled runtime work is separate from an open file.
// This component does not relax rendering, resource or outstanding-owner bounds.
#pragma once
#include <cstdarg>
#include <cstddef>
#include <cstdio>
#include <limits>

namespace cruisn {
class DiagnosticJournal {
public:
    enum class Policy { capture, quiet };
private:
    FILE *m_file=nullptr;
    bool m_enabled=false,m_failed=false;
public:
    DiagnosticJournal()=default;
    DiagnosticJournal(const DiagnosticJournal &)=delete;
    DiagnosticJournal &operator=(const DiagnosticJournal &)=delete;
    ~DiagnosticJournal(){if(m_file)std::fclose(m_file);}

    // Quiet does not open even a null-device file. Callers must explicitly
    // select it; failed capture opens never silently become quiet operation.
    bool open(const char *path,const char *mode,Policy policy) {
        if(m_enabled || m_file || !path || !mode ||
                (policy!=Policy::capture && policy!=Policy::quiet))return false;
        m_failed=false;
        if(policy==Policy::capture) {
            m_file=std::fopen(path,mode);
            if(!m_file){m_failed=true;return false;}
        }
        m_enabled=true;return true;
    }
    explicit operator bool()const{return m_enabled;}
    bool capturing()const{return m_enabled && m_file;}
    bool error()const{return m_failed || (m_file && std::ferror(m_file));}
    int buffer(char *storage,int mode,size_t size) {
        if(!m_enabled)return -1;
        if(!m_file)return 0;
        const int result=std::setvbuf(m_file,storage,mode,size);
        m_failed=m_failed || result!=0;return result;
    }
    // Preserve the compiler's format/type checks when replacing fprintf.
#if defined(__GNUC__) || defined(__clang__)
#if defined(__MINGW_PRINTF_FORMAT)
    __attribute__((format(__MINGW_PRINTF_FORMAT,2,3)))
#else
    __attribute__((format(printf,2,3)))
#endif
#endif
    int print(const char *format,...) {
        if(!m_enabled || !format)return -1;
        if(!m_file)return 0;
        va_list args;va_start(args,format);
        const int result=std::vfprintf(m_file,format,args);va_end(args);
        m_failed=m_failed || result<0;return result;
    }
    size_t write(const void *data,size_t size,size_t count) {
        if(!m_enabled || (size && count && !data) ||
                (size && count>std::numeric_limits<size_t>::max()/size)) {
            m_failed=true;return 0;
        }
        if(!size || !count)return 0;
        if(!m_file)return count;
        const size_t result=std::fwrite(data,size,count,m_file);
        m_failed=m_failed || result!=count;return result;
    }
    int put(int ch) {
        if(!m_enabled)return EOF;
        if(!m_file)return static_cast<unsigned char>(ch);
        const int result=std::fputc(ch,m_file);
        m_failed=m_failed || result==EOF;return result;
    }
    long tell() {
        if(!m_enabled)return -1;
        if(!m_file)return 0;
        const long result=std::ftell(m_file);
        m_failed=m_failed || result<0;return result;
    }
    int flush() {
        if(!m_enabled)return EOF;
        if(!m_file)return m_failed?EOF:0;
        const int result=std::fflush(m_file);
        m_failed=m_failed || result!=0;return result;
    }
    int close() {
        if(!m_enabled)return m_failed?EOF:0;
        const int result=m_file?std::fclose(m_file):0;
        m_file=nullptr;m_enabled=false;m_failed=m_failed || result!=0;
        return m_failed?EOF:0;
    }
};
}
