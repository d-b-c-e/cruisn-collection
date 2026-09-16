"""Bind host preparation rows to the completed renderer's auxiliary prefix.

The requested mirror frame is a presentation boundary, not a camera/scene ID.
This selects the last submitted host scene for each physical page. Subsequent
clears, original geometry and CPU writes still require pixel/ownership checks.
"""
import csv
from pathlib import Path
import re


def select(scenes, receipt):
    for key in ('frame', 'visible_page', 'auxiliary_quads'):
        if type(receipt.get(key)) is not int or receipt[key] < 0:
            raise ValueError('invalid completed host receipt')
    if receipt['visible_page'] not in (0, 1):
        raise ValueError('invalid completed host physical page')
    limit = receipt['auxiliary_quads']
    pages = [None, None]
    total = 0
    previous = -1
    for ordinal, scene in enumerate(scenes):
        frame, page, count = (scene[key] for key in ('frame', 'page', 'quads'))
        if (any(type(v) is not int for v in (frame, page, count)) or
                not max(0, previous) <= frame <= 0xffffffff or not 0 <= page <= 65535 or
                not 0 <= count <= 1048576 or
                not re.fullmatch('[0-9a-f]{16}', scene['quads_hash'])):
            raise ValueError('invalid host scene order/extent/fingerprint')
        previous = frame
        start, end = total, total + count
        total = end
        consumed = max(0, min(limit, end) - start)
        if consumed:
            if frame > receipt['frame']:
                raise ValueError('completed host prefix includes a future frame')
            physical = (page >> 2) & 1
            pages[physical] = dict(ordinal=ordinal, frame=frame, page_control=page,
                physical_page=physical, first_quad=start, end_quad_exclusive=start+consumed,
                prepared_quads=count, consumed_quads=consumed, complete=consumed == count,
                prepared_quads_hash=scene['quads_hash'])
    if total < limit:
        raise ValueError('host journal does not cover completed auxiliary count')
    return dict(schema=1, completed_frame=receipt['frame'], visible_page=receipt['visible_page'],
        consumed_auxiliary_quads=limit, prepared_auxiliary_quads=total,
        excluded_unconsumed_quads=total-limit, pages=pages,
        visible=pages[receipt['visible_page']], pixel_reproduction_verified=False,
        scope='Completed auxiliary submission prefix only; later clears, original '
              'geometry, CPU writes and resource changes are not replayed.')


def require_preparation_frame(completion, frame, page=None):
    """Reject a different or partially consumed scene before using its operands."""
    if page is None:
        page = completion['visible_page']
    if type(frame) is not int or type(page) is not int or page not in (0, 1):
        raise ValueError('invalid requested host preparation frame/page')
    scene = completion['pages'][page]
    if scene is None or not scene['complete'] or scene['frame'] != frame:
        raise ValueError('saved preparation frame does not match completed host scene')
    return scene


def load(run, game, receipt):
    if game not in ('world', 'usa', 'offroad'):
        raise ValueError('unsupported host completion game')
    path = Path(run)/f'{game}-host-scenes.csv'
    if not 0 < path.stat().st_size <= 16*1024*1024:
        raise ValueError('host completion journal extent')
    with path.open(encoding='utf-8', newline='') as stream:
        rows = []
        for row in csv.DictReader(stream):
            if len(rows) >= 20000:
                raise ValueError('host completion scene budget')
            rows.append(dict(frame=int(row['frame']), page=int(row['page']),
                             quads=int(row['quads']), quads_hash=row['quads_hash']))
    return select(rows, receipt)
