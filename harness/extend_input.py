"""Append a labeled synthetic continuation without changing recorded INP rows.

This creates a stimulus, not a verified recording. Record it through MAME's INP
writer and compare the resulting original prefix before using it as a case.
The tail releases digital buttons and uses explicit normalized analog keyframes.
Scenario frames/keyframes are relative to the first appended input row.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from synthesize_input import LAYOUTS, ANALOG_LAYOUTS, generate


def extend(source, scenario):
    if len(source)<64 or source[:8]!=b'MAMEINP\0' or source[16:18]!=b'\x03\x00':
        raise ValueError('requires a supported MAME INP v3.0 recording')
    rom=source[20:32].split(b'\0')[0].decode('ascii')
    if rom not in LAYOUTS:raise ValueError('unsupported recording port layout')
    ports=LAYOUTS[rom];analog=ANALOG_LAYOUTS[rom]
    stride=16+8*len(ports)+13*len(analog)
    payload=zlib.decompress(source[64:])
    if len(payload)%stride or len(payload)<stride*3:
        raise ValueError('recording has incomplete input rows')
    rows=len(payload)//stride
    extra=scenario.get('frames')
    if type(extra) is not int or extra<1 or rows-1+extra>36000:
        raise ValueError('continuation requires positive integer frames, total at most36000')
    keys=scenario.get('analog',{})
    if set(keys)!=set(analog):raise ValueError('continuation must explicitly set every pedal and steering axis')
    if any(not points or points[0][0]!=0 or any(type(n) is not int or not 0<=n<extra for n,_ in points)
           for points in keys.values()):
        raise ValueError('continuation analog points must start at zero and fit the tail')
    for pulse in scenario.get('buttons',[]):
        if type(pulse['start']) is not int or type(pulse['end']) is not int or not 0<=pulse['start']<pulse['end']<=extra:
            raise ValueError('continuation button pulse outside tail')
    template=bytearray(payload[-stride+16:])
    offsets={};at=16
    for port in ports:
        struct.pack_into('<I',template,at-16+4,0)  # release digital value, retain defaults/configuration
        at+=8
        if port in analog:offsets[port]=at;at+=13
    # A neutral, constant template lets the existing codec validate analog
    # ranges/sensitivities and Zeus's distinct first-refresh rounding.
    seed=source[:64]+zlib.compress(b''.join(payload[n*stride:n*stride+16]+template for n in range(3)))
    tail=zlib.decompress(generate(seed,scenario)[64:])
    generated=bytearray(zlib.decompress(generate(seed,dict(frames=rows-1+extra))[64:]))
    if any(payload[n:n+12]!=generated[n:n+12] for n in range(0,len(payload),stride)):
        raise ValueError('recorded input timing differs from supported generated cadence')
    generated[:len(payload)]=payload  # exact original bytes, including recorded speed metadata
    for n in range(extra):
        # Retain the absolute continuation time, with the relative scripted ports.
        generated[(rows+n)*stride+16:(rows+n+1)*stride]=tail[n*stride+16:(n+1)*stride]
    for offset in offsets.values():
        # The first new frame interpolates from the actual last recorded state.
        previous=struct.unpack_from('<i',payload,len(payload)-stride+offset)[0]
        struct.pack_into('<i',generated,len(payload)+offset+4,previous)
    result=source[:64]+zlib.compress(generated,6)
    return result,dict(kind='recorded-prefix-with-synthetic-tail',rom=rom,
        recorded_rows=rows,recorded_frames=rows-1,synthetic_frames=extra,
        total_frames=rows-1+extra,first_synthetic_row=rows,stride=stride,
        source_sha256=hashlib.sha256(source).hexdigest(),
        prefix_payload_sha256=hashlib.sha256(payload).hexdigest(),
        stimulus_sha256=hashlib.sha256(result).hexdigest(),
        scope='Original input bytes preserved; tail is scripted. No gameplay, replay, transition or visual acceptance yet.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('scenario',type=Path)
    parser.add_argument('--output',required=True,type=Path,help='new directory for stimulus and provenance')
    args=parser.parse_args()
    source=args.input.read_bytes();scenario=args.scenario.read_bytes()
    result,report=extend(source,json.loads(scenario.decode('utf-8')))
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'stimulus.inp').write_bytes(result)
    (args.output/'scenario.json').write_bytes(scenario)
    report.update(source=str(args.input.resolve()),scenario_sha256=hashlib.sha256(scenario).hexdigest())
    (args.output/'provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
