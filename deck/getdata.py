import json, os, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.show=lambda *a,**k: plt.close('all')
def run(nb):
    ns={}; d=json.load(open(f'../build/exec/{nb}.ipynb')); os.chdir('/tmp')
    for c in d['cells']:
        if c['cell_type']=='code':
            src=''.join(c['source']); lines=src.split('\n')
            exec(src, ns)
    os.chdir('/home/user/workspace/lecture7/deck'); return ns
out={}
raw=pd.read_csv('../data/students.csv')
out['stud_raw']=dict(neg_math=int((raw['math score']<0).sum()), standart=int((raw['lunch']=='standart').sum()))
s=run('00_students_etalon')
w=s['df']['writing score']; bins=list(range(0,101,10)); bins[-1]=101
out['stud_hist']=pd.cut(w,bins,right=False,include_lowest=True).value_counts(sort=False).tolist()
out['stud_hist'][-1]+=int((w==100).sum()) if False else 0
out['stud_corr']=s['corr'].round(2).values.tolist()
b=run('01_oilgas_brent_oilspill')
m=b['s'].resample('ME').mean()
out['brent_m']={'d':[x.strftime('%Y-%m') for x in m.index],'v':[round(float(v),2) for v in m.values]}
out['brent_vol']={str(k):round(float(v),1) for k,v in b['yearly']['волатильность, % годовых'].items()}
g=run('02_energy_smart_grid')
q=g['share'].groupby('tau_group',observed=True)['stabf'].apply(lambda x:(x=='unstable').mean())
out['grid_q']={str(k):round(float(v),3) for k,v in q.items()}
c=run('03_construction_concrete')
out['conc_scatter']={'fact':[round(float(v),1) for v in c['y_te'][:0]]}
# regression scatter: recompute with fe cols
from sklearn.model_selection import train_test_split; from sklearn.linear_model import LinearRegression
be=c['beton']; Xtr,Xte,ytr,yte=train_test_split(be[c['fe_cols']],be['strength_mpa'],test_size=0.25,random_state=42)
p=LinearRegression().fit(Xtr,ytr).predict(Xte)
out['conc_scatter']={'fact':[round(float(v),1) for v in yte],'pred':[round(float(v),1) for v in p]}
a=run('04_production_predictive_maintenance')
out['ai4i']={k:np.asarray(v).tolist() for k,v in a['res'].items()}
f=run('05_reverse_task_synthetic_dataset')
out['flare_w']={k:round(float(v),2) for k,v in zip(f['features'],f['model'][-1].coef_[0])}
json.dump(out,open('data.json','w'),ensure_ascii=False)
print({k:(v if k not in('brent_m','conc_scatter') else '...') for k,v in out.items()})
