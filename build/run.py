import sys, nbformat as nbf, copy
from nbconvert.preprocessors import ExecutePreprocessor
from nbb import RAW
LOCAL="/home/user/workspace/lecture7/data/"
for p in sys.argv[1:]:
    nb=nbf.read(p,as_version=4); nb2=copy.deepcopy(nb)
    for c in nb2.cells:
        if c.cell_type=="code": c.source=c.source.replace(RAW,LOCAL)
    ExecutePreprocessor(timeout=600,kernel_name="python3").preprocess(nb2,{"metadata":{"path":"/tmp"}})
    out=p.replace("/notebooks/","/build/exec/")
    nbf.write(nb2,out)
    for i,c in enumerate(nb2.cells):
        if c.cell_type!="code": continue
        for o in c.get("outputs",[]):
            t=o.get("text") or (o.get("data",{}).get("text/plain") if o.get("output_type")!="display_data" or "image/png" not in o.get("data",{}) else "[IMG]")
            if o.get("output_type")=="stream" and o.get("name")=="stderr": t="STDERR: "+o["text"][:300]
            if t: print(f"[{i}]",str(t)[:700])
    print("DONE",p)
