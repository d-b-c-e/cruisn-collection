"""Atomic saved telemetry connection; address limits match the native IPv4 sender."""
import ipaddress
from settings_view import update_section

PRESET = '127.0.0.1:5300'
ALIASES = {'1','on','true','yes'}
OFF = {'','0','off','false','no'}


def enabled(section):
    if 'enabled' in section:
        return str(section['enabled']).strip().lower() in ALIASES
    return any(str(section.get(key,'')).strip().lower() not in OFF for key in ('forza','udp'))


def destination(value, *, forza):
    value=str(value or '').strip()
    if value.lower() in OFF:return ''
    if forza and value.lower() in ALIASES:return PRESET
    parts=value.split(',')
    if not 1 <= len(parts) <= (4 if forza else 1):
        raise ValueError('Forza supports up to four destinations; diagnostic UDP supports one.')
    targets=[]
    for part in parts:
        part=part.strip()
        if ':' in part:
            host,port=part.rsplit(':',1)
        elif part.isdecimal():host,port='127.0.0.1',part
        else:raise ValueError('Enter an IPv4 address and port, for example 127.0.0.1:5300.')
        if not port.isascii() or not port.isdecimal() or not 1<=int(port)<=65535:
            raise ValueError('Port must be between 1 and 65535.')
        if host.lower()=='localhost':host='127.0.0.1'
        try:host=str(ipaddress.IPv4Address(host))
        except ipaddress.AddressValueError as exc:
            raise ValueError('Use a numeric IPv4 address; the game sender does not resolve hostnames or IPv6.') from exc
        targets.append(f'{host}:{int(port)}')
    result=','.join(targets)
    if len(result)>255:raise ValueError('Telemetry destination is too long.')
    return result


def launch_overrides(section, environment):
    """Explicit diagnostic environment still wins; saved Off suppresses saved streams."""
    result={}
    if enabled(section):
        for key,envkey in (('forza','MIDV_TELEM_FORZA'),('udp','MIDV_TELEM_UDP')):
            if envkey not in environment:
                target=destination(section.get(key,''),forza=key=='forza')
                if target:result[envkey]=target
    return result


def set_enabled(path, section, value):
    changes={'enabled':'1' if value else '0'}
    if value:
        proposed=dict(section,**changes)
        if not any(str(proposed.get(k,'')).strip().lower() not in OFF for k in ('forza','udp')):
            proposed['forza']=changes['forza']=PRESET
        launch_overrides(proposed,{})  # Refuse invalid saved destinations before writing.
    update_section(path,'telemetry',changes,'.before-telemetry.bak')


def apply_connection(path, forza, udp):
    values={'forza':destination(forza,forza=True),'udp':destination(udp,forza=False)}
    update_section(path,'telemetry',values,'.before-telemetry.bak')


def connection_dialog(section):
    """One modal draft; Cancel never writes or affects the current stream."""
    import tkinter as tk
    from tkinter import ttk
    root=tk.Tk();root.title('Telemetry connection');root.resizable(False,False)
    result=[]
    ttk.Label(root,text='Forza Horizon 5 / SimHub destinations (IPv4:port)',padding=10).grid(row=0,column=0,columnspan=2,sticky='w')
    forza=tk.StringVar(value=section.get('forza',''))
    udp=tk.StringVar(value=section.get('udp',''))
    entry=ttk.Entry(root,textvariable=forza,width=56);entry.grid(row=1,column=0,columnspan=2,padx=10,sticky='ew')
    ttk.Label(root,text='Diagnostic JSON UDP destination (optional)',padding=10).grid(row=2,column=0,columnspan=2,sticky='w')
    ttk.Entry(root,textvariable=udp,width=56).grid(row=3,column=0,columnspan=2,padx=10,sticky='ew')
    error=tk.StringVar()
    ttk.Label(root,textvariable=error,wraplength=440,padding=10).grid(row=4,column=0,columnspan=2,sticky='w')
    def apply():
        try:values=(destination(forza.get(),forza=True),destination(udp.get(),forza=False))
        except ValueError as exc:error.set(str(exc));return
        result.append(values);root.destroy()
    ttk.Button(root,text='Apply connection',command=apply).grid(row=5,column=0,padx=10,pady=10)
    ttk.Button(root,text='Cancel',command=root.destroy).grid(row=5,column=1,padx=10,pady=10)
    root.bind('<Escape>',lambda _:root.destroy());root.protocol('WM_DELETE_WINDOW',root.destroy)
    entry.focus_set();root.mainloop()
    return result[0] if result else None
