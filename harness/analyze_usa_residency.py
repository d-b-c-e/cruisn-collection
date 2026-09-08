"""Measure pending USA scenery, without asserting it is visible or safe to draw."""
import argparse
import csv
from pathlib import Path
from verification import sha256_file, write_json


def summarize(path):
    counts = dict(pending=0, activate=0, deactivate=0)
    candidates = {factor: 0 for factor in (1.25, 2, 3)}
    objects, pending_objects, future_objects = set(), set(), set()
    minimum, maximum, previous = None, None, 0
    with Path(path).open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            frame, kind, obj = int(row['frame']), row['kind'], int(row['object'], 16)
            depth, radius, limit = (int(row[key]) for key in ('depth', 'radius', 'limit'))
            if frame < previous or frame < 1 or kind not in counts or not 0x1000 <= obj < 0x20000-29:
                raise ValueError('invalid residency event/order/object')
            if radius < 0 or limit != (80000 if kind == 'deactivate' else 75000):
                raise ValueError('unexpected residency radius/limit')
            previous = frame
            counts[kind] += 1
            objects.add(obj)
            if kind == 'pending':
                pending_objects.add(obj)
                distance = depth-radius
                minimum = distance if minimum is None else min(minimum, distance)
                maximum = distance if maximum is None else max(maximum, distance)
                # The depth store is a branch delay-slot instruction: pending
                # visits also include objects rejected by the near test. Far
                # candidates are ahead, so cannot belong to that near rejection.
                if distance > limit:
                    future_objects.add(obj)
                    for factor in candidates:
                        candidates[factor] += distance <= limit*factor
    if not counts['pending']:
        raise ValueError('no pending scenery was measured')
    return dict(schema=1, sha256=sha256_file(path), events=counts,
                observed_objects=len(objects), pending_objects=len(pending_objects),
                future_objects=len(future_objects), pending_depth_minus_radius=[minimum,maximum],
                newly_eligible_visits={str(k):v for k,v in candidates.items()},
                scope='eligibility at the admission distance gate only; not visible pixels or safe residency')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();write_json(args.output,summarize(args.csv))
