import sys, zipfile, shutil, re
from lxml import etree
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
ORDER = ["lnL","lnR","lnT","lnB","lnTlToBr","lnBlToTr","cell3D","noFill","solidFill","gradFill","blipFill","pattFill","grpFill","headers","extLst"]
src = sys.argv[1]; tmp = src + ".tmp"
zin = zipfile.ZipFile(src); zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
n = 0
for it in zin.infolist():
    data = zin.read(it.filename)
    if re.match(r"ppt/slides/slide\d+\.xml$", it.filename) and b"tcPr" in data:
        root = etree.fromstring(data)
        for tc in root.iter("{%s}tcPr" % A):
            kids = list(tc)
            srt = sorted(kids, key=lambda e: ORDER.index(etree.QName(e).localname) if etree.QName(e).localname in ORDER else 99)
            if srt != kids:
                for k in kids: tc.remove(k)
                for k in srt: tc.append(k)
                n += 1
        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    zout.writestr(it, data)
zout.close(); shutil.move(tmp, src); print("reordered", n)
