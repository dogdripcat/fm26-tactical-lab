"""Read-only, offset-aligned binary comparison. No FM field interpretation."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

MAGIC = bytes.fromhex('28 b5 2f fd')
LIMIT = 8 * 1024 * 1024


def byte_diff(a, b):
    n=max(len(a),len(b)); same=sum(x==y for x,y in zip(a,b))
    ranges=[]; start=None
    for i in range(n+1):
        changed=i<n and (i>=len(a) or i>=len(b) or a[i]!=b[i])
        if changed and start is None: start=i
        if not changed and start is not None:
            def context(data):
                lo=min(len(data),max(0,start-32)); hi=min(len(data),i+32)
                return {'start':lo,'end_exclusive':hi,'hex':data[lo:hi].hex(' ')}
            ranges.append({'start':start,'end_exclusive':i,'length':i-start,
                           'a_context':context(a),'b_context':context(b)})
            start=None
    return {'comparison':'offset-aligned; insertions can shift subsequent bytes',
            'size_a':len(a),'size_b':len(b),'denominator_bytes':n,
            'identical_bytes':same,'changed_bytes':n-same,
            'identical_percent':100*same/n if n else 100.0,
            'changed_percent':100*(n-same)/n if n else 0.0,'ranges':ranges}


def strings(data):
    return [{'offset':m.start(),'text':m.group().decode('ascii')}
            for m in re.finditer(rb'[\x20-\x7e]{4,}',data)]


def string_diff(a,b):
    aa,bb=strings(a),strings(b)
    return {'definition':'ASCII printable runs >=4 bytes; offsets local to compared data',
            'a':aa,'b':bb,'only_a':sorted({x['text'] for x in aa}-{x['text'] for x in bb}),
            'only_b':sorted({x['text'] for x in bb}-{x['text'] for x in aa})}


def frame_end(data,start):
    """Standard Zstandard frame boundaries, independent of FMF structure."""
    p=start+4
    def take(n):
        nonlocal p
        if p+n>len(data): raise ValueError('truncated Zstandard frame')
        part=data[p:p+n]; p+=n; return part
    flag=take(1)[0]
    if flag & 0x18: raise ValueError('unsupported/reserved frame flags')
    single=bool(flag & 32)
    if not single: take(1)
    take((0,1,2,4)[flag&3])
    take((1 if single else 0,2,4,8)[flag>>6])
    while True:
        header=int.from_bytes(take(3),'little'); kind=(header>>1)&3; size=header>>3
        if kind==3: raise ValueError('reserved block type')
        take(1 if kind==1 else size)
        if header&1: break
    if flag&4: take(4)
    return p


def decompress(data):
    node=os.environ.get('FM26LAB_NODE') or shutil.which('node')
    if not node: raise RuntimeError('Node.js with zstdDecompressSync required; set FM26LAB_NODE to its executable')
    code="const fs=require('node:fs'),z=require('node:zlib');process.stdout.write(z.zstdDecompressSync(fs.readFileSync(0),{maxOutputLength:8388608}));"
    result=subprocess.run([node,'-e',code],input=data,capture_output=True,timeout=30)
    if result.returncode: raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[:2000])
    if len(result.stdout)>LIMIT: raise RuntimeError('decompression output limit exceeded')
    return result.stdout


def frames(data):
    reports=[]; payloads={}; offset=0
    while True:
        start=data.find(MAGIC,offset)
        if start<0: break
        offset=start+4; record={'offset':start,'status':'signature_only'}
        try:
            end=frame_end(data,start)
            record.update(end_exclusive=end,compressed_bytes=end-start)
            decoded=decompress(data[start:end])
            record.update(status='decompressed',decoded_bytes=len(decoded),
                          decoded_sha256=hashlib.sha256(decoded).hexdigest(),printable_strings=strings(decoded))
            payloads[len(reports)]=decoded
        except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as exc:
            record.update(status='error',error=str(exc))
        reports.append(record)
    return reports,payloads


def compare_files(a,b,label=None):
    paths=[Path(a).resolve(strict=True),Path(b).resolve(strict=True)]
    blobs=[p.read_bytes() for p in paths]
    before=[hashlib.sha256(d).hexdigest() for d in blobs]
    fa,pa=frames(blobs[0]); fb,pb=frames(blobs[1]); comparisons=[]
    for i in range(max(len(fa),len(fb))):
        item={'candidate_index':i,'pairing':'discovery order only; semantic correspondence unknown'}
        if i in pa and i in pb:
            item.update(byte_diff=byte_diff(pa[i],pb[i]),printable_strings=string_diff(pa[i],pb[i]))
        else: item['status']='not_comparable_missing_or_failed_frame'
        comparisons.append(item)
    after=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    if before!=after: raise ValueError('Source hash changed during analysis; report aborted')
    return {'label':label,'label_is_user_annotation_only':True,
            'sources':[{'path':str(p),'size_bytes':len(d),'sha256_before':x,'sha256_after':y,'unchanged':x==y}
                       for p,d,x,y in zip(paths,blobs,before,after)],
            'observed':{'raw_byte_diff':byte_diff(*blobs),'raw_printable_strings':string_diff(*blobs),
                        'zstandard':{'a':fa,'b':fb,'decoded_comparisons':comparisons}},
            'unknown_meaning':['No field, role ID, formation or instruction semantics assigned.',
                               'Frame pairing by order does not establish matching logical content.'],
            'limits':{'decoded_bytes_per_frame':LIMIT,'input':'whole files in memory',
                      'strings':'ASCII only','offsets':'zero-based; range ends exclusive'}}


def diff_fmf_cmd(args):
    try:
        sources=[Path(args.a).resolve(strict=True),Path(args.b).resolve(strict=True)]
        dest=Path(args.out).resolve() if args.out else None
        if dest is not None:
            if dest.suffix.lower()=='.fmf' or any(dest==p or (dest.exists() and dest.samefile(p)) for p in sources):
                raise ValueError('Output must not be an FMF or source alias')
            if dest.exists(): raise ValueError('Output already exists; choose a new report path')
        report=compare_files(*sources,args.label)
        text=json.dumps(report,ensure_ascii=True,indent=2)
        if dest is not None:
            with dest.open('x',encoding='utf-8') as f: f.write(text+'\n')
        print(text)
    except (OSError,ValueError) as exc:
        raise SystemExit(f'diff-fmf: {exc}') from exc
