"""Verify the built PE contains image bytes from the requested ICO, not a default icon."""
from pathlib import Path
import struct
import sys
import pefile

ico=Path(sys.argv[1]).read_bytes()
reserved,kind,count=struct.unpack_from('<HHH',ico)
assert reserved==0 and kind==1 and count>0
frames=set()
for i in range(count):
    size,offset=struct.unpack_from('<II',ico,6+16*i+8)
    frames.add(ico[offset:offset+size])
pe=pefile.PE(sys.argv[2])
images=set()
for resource in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    if resource.id==3:  # RT_ICON
        for icon in resource.directory.entries:
            for language in icon.directory.entries:
                d=language.data.struct
                images.add(pe.get_data(d.OffsetToData,d.Size))
assert frames & images,'The executable does not contain the requested custom icon'
print('Custom icon image verified in PE resources')
