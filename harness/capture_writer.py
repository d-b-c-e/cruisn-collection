"""Validate completed background screenshot writes; absent receipts support old builds."""
import re


def verify(text, require_pacing=False):
    if re.search(r'MID[VZ] screenshot (?:writer|write) (?:failed|rejected)', text):
        raise ValueError('screenshot writer failed or rejected a requested capture')
    lines = [line for line in text.splitlines() if re.match(r'MID[VZ]_CAPTURE_WRITER', line)]
    if not lines:
        if require_pacing:
            raise ValueError('requested screenshot pacing was not acknowledged')
        return None
    if len(lines) != 2 or lines[0] not in ('MIDV_CAPTURE_WRITER_BEGIN', 'MIDZ_CAPTURE_WRITER_BEGIN'):
        raise ValueError('missing or duplicate screenshot writer completion')
    prefix = lines[0].removesuffix('_BEGIN')
    keys = ('submitted', 'written', 'failed', 'rejected', 'peak_bytes',
            'write_total_us', 'write_max_us', 'drain_us')
    match = re.fullmatch(prefix + ''.join(' ' + key + r'=(\d+)' for key in keys) +
                        r'(?: paced=([01]) waits=(\d+) wait_us=(\d+))?', lines[1])
    if not match:
        raise ValueError('malformed screenshot writer completion')
    result = dict(zip(keys, map(int, match.groups()[:len(keys)])))
    if match.group(9) is not None:
        result.update(zip(('paced', 'waits', 'wait_us'), map(int, match.groups()[len(keys):])))
        if not result['paced'] and (result['waits'] or result['wait_us']):
            raise ValueError('unexpected screenshot pacing')
    if require_pacing and result.get('paced') != 1:
        raise ValueError('requested screenshot pacing was not acknowledged')
    count = result['submitted']
    if (count != result['written'] or result['failed'] or result['rejected'] or
            not 0 <= result['peak_bytes'] <= 512 * 1024 * 1024 or
            bool(count) != bool(result['peak_bytes']) or
            not result['write_max_us'] <= result['write_total_us'] <= count * result['write_max_us']):
        raise ValueError('incomplete or inconsistent screenshot writer results')
    result['renderer'] = prefix.split('_')[0]
    return result
