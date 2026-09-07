"""Capture actual emulator UDP packets on private localhost ports during replay."""
import csv
import json
from pathlib import Path
import socket
import struct
import threading

from verification import write_json, sha256_file


class TelemetryLoopback:
    def __init__(self, directory):
        self.directory=Path(directory)
        self.stopping=threading.Event()
        self.sockets=[];self.threads=[];self.counts={};self.errors=[]

    def start(self, environment):
        for kind,key in [('forza','MIDV_TELEM_FORZA'),('json','MIDV_TELEM_UDP')]:
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,4*1024*1024)
            sock.bind(('127.0.0.1',0));sock.settimeout(.1)
            self.sockets.append(sock);self.counts[kind]=0
            environment[key]='127.0.0.1:'+str(sock.getsockname()[1])
            thread=threading.Thread(target=self.receive,args=(kind,sock),daemon=True)
            self.threads.append(thread);thread.start()

    def receive(self, kind, sock):
        try:
            path=self.directory/('forza.csv' if kind=='forza' else 'telemetry.jsonl')
            with path.open('w',encoding='utf-8',newline='') as stream:
                if kind=='forza':
                    writer=csv.writer(stream)
                    writer.writerow(['timestamp_ms','race_on','max_rpm','idle_rpm','rpm','speed_ms','gear'])
                while True:
                    try: data,_=sock.recvfrom(65535)
                    except socket.timeout:
                        if self.stopping.is_set():break
                        continue
                    self.counts[kind]+=1
                    if self.counts[kind]>500000:
                        raise ValueError('telemetry capture exceeds bounded packet budget')
                    if kind=='forza':
                        if len(data)!=324:raise ValueError(f'Forza packet length {len(data)}')
                        race,stamp=struct.unpack_from('<iI',data)
                        maximum,idle,rpm=struct.unpack_from('<fff',data,8)
                        speed,=struct.unpack_from('<f',data,256)
                        writer.writerow([stamp,race,maximum,idle,rpm,speed,data[319]])
                    else:
                        stream.write(json.dumps(json.loads(data))+'\n')
        except Exception as error:
            self.errors.append(f'{kind}: {error}')

    def close(self):
        self.stopping.set()
        for thread in self.threads:thread.join(2)
        for sock in self.sockets:sock.close()
        if any(thread.is_alive() for thread in self.threads):self.errors.append('receiver did not stop')
        report={'passed':not self.errors and all(self.counts.get(k,0)>0 for k in ('forza','json')),
                'local_only':True,'packets':self.counts,'errors':self.errors,
                'files':{p.name:sha256_file(p) for p in [self.directory/'forza.csv',self.directory/'telemetry.jsonl'] if p.is_file()}}
        write_json(self.directory/'telemetry-loopback.json',report)
        return report
