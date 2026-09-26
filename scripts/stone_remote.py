"""Read-only, cached HTTP ranges for the official large STONE ZIP/SQLite files.

Only requested byte blocks are downloaded. SQLite decoding is provided by APSW;
ZIP parsing/CRC verification by Python's zipfile, not custom binary parsers.
"""
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request


class RemoteFile(io.RawIOBase):
    def __init__(self, source, cache, block_size=1024*1024):
        self.source=source;self.size=int(source['size']);self.position=0;self.block_size=block_size
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        identity={'id':source['id'],'size':self.size,'block_size':block_size}
        identity_path=self.cache/'identity.json'
        if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
            raise ValueError('Cache belongs to a different remote file')
        identity_path.write_text(json.dumps(identity))
        self.downloaded=0

    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.position
    def seek(self,offset,whence=0):
        pos=offset+(self.position if whence==1 else self.size if whence==2 else 0)
        if whence not in (0,1,2) or pos<0:raise ValueError('Invalid seek')
        self.position=pos;return pos

    def block(self,index):
        start=index*self.block_size;end=min(start+self.block_size,self.size)-1
        path=self.cache/f'{index:09d}.bin';digest=path.with_suffix('.sha256')
        if path.exists() and digest.exists():
            data=path.read_bytes()
            if len(data)==end-start+1 and hashlib.sha256(data).hexdigest()==digest.read_text():return data
            raise ValueError('Corrupt cached range '+str(path))
        for attempt in range(3):
            try:
                req=urllib.request.Request(self.source['url']+'&range_start='+str(start),headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
                with urllib.request.urlopen(req,timeout=45) as response:
                    expected=f'bytes {start}-{end}/{self.size}'
                    if response.status!=206 or response.headers.get('Content-Range')!=expected:
                        raise ValueError('Server did not return the exact requested byte range')
                    data=response.read(end-start+2)
                if len(data)!=end-start+1:raise ValueError('Incomplete remote range')
                temp=path.with_suffix('.part');temp.write_bytes(data);temp.replace(path)
                digest.write_text(hashlib.sha256(data).hexdigest());self.downloaded+=len(data)
                print(f'Downloaded {self.source["id"]}: block {index}, {self.downloaded/1e6:.1f} MB this run',flush=True)
                return data
            except Exception:
                if attempt==2:raise
                time.sleep(1+attempt)

    def read_at(self,offset,amount):
        if offset<0 or amount<0:raise ValueError('Invalid range')
        end=min(offset+amount,self.size);parts=[]
        while offset<end:
            index,within=divmod(offset,self.block_size);block=self.block(index)
            n=min(end-offset,len(block)-within);parts.append(block[within:within+n]);offset+=n
        return b''.join(parts)

    def read(self,size=-1):
        data=self.read_at(self.position,max(0,self.size-self.position) if size<0 else size)
        self.position+=len(data);return data


def connect_sqlite(remote):
    import apsw

    class File:
        def xRead(self,amount,offset):return remote.read_at(offset,amount)
        def xFileSize(self):return remote.size
        def xClose(self):pass
        def xLock(self,level):pass
        def xUnlock(self,level):pass
        def xCheckReservedLock(self):return False
        def xFileControl(self,op,pointer):return False
        def xSectorSize(self):return 4096
        def xDeviceCharacteristics(self):return apsw.SQLITE_IOCAP_IMMUTABLE
        def xWrite(self,data,offset):raise apsw.ReadOnlyError('Remote source is read-only')
        def xTruncate(self,size):raise apsw.ReadOnlyError('Remote source is read-only')
        def xSync(self,flags):pass

    class VFS(apsw.VFS):
        def xOpen(self,name,flags):
            if flags[0]&apsw.SQLITE_OPEN_READWRITE:raise apsw.ReadOnlyError('Read-only connection required')
            flags[1]=apsw.SQLITE_OPEN_READONLY
            return File()
        def xAccess(self,path,flags):return False

    vfs=VFS('stone-readonly-'+remote.source['id'],'')
    connection=apsw.Connection('file:stone.db3?immutable=1',flags=apsw.SQLITE_OPEN_READONLY|apsw.SQLITE_OPEN_URI,vfs=vfs.vfsname if hasattr(vfs,'vfsname') else 'stone-readonly-'+remote.source['id'])
    return connection,vfs
