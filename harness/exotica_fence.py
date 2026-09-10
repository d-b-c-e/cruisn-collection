"""Validate exact command-ring completion receipts, not visual insertion."""
import csv
from pathlib import Path
import re


def verify(directory, scenes, text, enabled):
    initial = re.findall(r'^MIDZ_HOST_FENCE=(\d+)$', text, re.M)
    final = re.findall(r'^MIDZ_HOST_FENCE_RESULT complete=(\d+) requested=(\d+) completed=(\d+) immediate=(\d+)$', text, re.M)
    if not enabled:
        if initial or final:
            raise ValueError('disabled Exotica command fence ran')
        return None
    if initial != ['1'] or len(final) != 1:
        raise ValueError('missing Exotica command fence acknowledgment')
    complete, requested, completed, immediate = map(int, final[0])
    if complete != 1 or not requested or requested != completed or requested != len(scenes):
        raise ValueError('incomplete Exotica command fences')
    path = Path(directory)/'exotica-host-fences.csv'
    if path.stat().st_size > 2*1024*1024:
        raise ValueError('Exotica command fence log budget')
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != requested or len(rows) > 10002:
        raise ValueError('Exotica command fence row count')
    now_count = total_words = 0
    for row, scene in zip(rows, scenes):
        begin, end, ready = (int(row[k]) for k in ('scene_frame', 'end_frame', 'ready_frame'))
        end_time, ready_time = (float(row[k]) for k in ('end_time', 'ready_time'))
        consumer, target, words, now = (int(row[k]) for k in ('consumer', 'target', 'words', 'immediate'))
        if (int(row['scene']) != int(scene['scene']) or begin != int(scene['scene_frame']) or
                end-begin not in (0, 1) or ready-end not in (0, 1) or
                not 0 <= end_time-float(scene['scene_time']) < .0176 or
                not 0 <= ready_time-end_time < .0176 or ready_time < float(scene['device_time']) or
                not 0x30000 <= consumer < 0x32000 or not 0x30000 <= target < 0x32000 or
                words != (target-consumer) % 0x2000 or now not in (0, 1) or
                bool(now) != (words == 0) or (now and ready_time != end_time) or
                int(row['guest_cycles']) != 0):
            raise ValueError('Exotica command fence order/clock/boundary mismatch')
        now_count += now;total_words += words
    if now_count != immediate:
        raise ValueError('Exotica immediate fence count')
    return dict(passed=True, scenes=requested, immediate=immediate, waited_words=total_words,
                scope='Existing FIFO completion only; original resource and visual checks are separate.')
