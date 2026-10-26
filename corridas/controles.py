import os, sys
# Uso: python corridas/controles.py CARPETA_RIVALES_DATOS  (despues de analizar.py; agregado despues de ver resultados)
__file__ = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'analizar.py')
src=open(__file__).read()
exec(compile(src[:src.index("# senales")],__file__,"exec")); exec(src[src.index("def ols_cluster"):src.index("# informe")].rsplit("#",1)[0])
S=pd.read_csv(os.path.dirname(__file__) + '/senales.csv.gz',dtype={'evento':str}); O=pd.read_csv(os.path.dirname(__file__) + '/ops.csv.gz',dtype={'evento':str})
gano={}
for eid,ev in EVENTOS.items():
    g=cj.set_index('condition_id').loc[ev['cids']].precio_final_si.values
    if (g=='1').sum()==1: gano[eid]=ev['centros'][list(g).index('1')]
S['real']=S.evento.map(gano)
ok=S.real.notna()
for nom,y in (("final - E(W)",S.real-S.E_W),):
    b,se,n=ols_cluster(S.db.values[ok],y.values[ok],S.evento.values[ok]); print(nom,'beta',round(b,3),'t',round(b/se,1),n)
# error del mercado vs del modelo como predictor: correlacion de db con resto
# controles prueba B sin costos
def nc(row,h,sign=1):
    ev=EVENTOS[row.evento]; k=row.caja
    x=precio(ev['cids'][k],row.W+h*3600)
    return (x-row.p_W)/row.p_W if x is not None else np.nan
for h in (1,3,6):
    r=np.array([nc(r,h) for r in O.itertuples()]); mu,se,n=media_cluster(r,O.evento.values); print('sin costos',h,round(100*mu,1),round(mu/se,1))
# control: caja vecina del lado contrario, sin costos y con costos (+1c/-1c)
res={1:[],3:[],6:[]}; resc={1:[],3:[],6:[]};gs=[]
for r in O.itertuples():
    ev=EVENTOS[r.evento]; pw=precios_evento(ev,r.W); k=int(np.argmax(pw))-(1 if r.db>0 else -1)
    if not(0<=k<len(pw)) or not(0.05<=pw[k]<=0.6): continue
    gs.append(r.evento)
    for h in (1,3,6):
        x=precio(ev['cids'][k],r.W+h*3600)
        res[h].append((x-pw[k])/pw[k] if x is not None else np.nan)
for h in (1,3,6):
    mu,se,n=media_cluster(np.array(res[h]),np.array(gs)); print('contrario sin costos',h,round(100*mu,1),round(mu/se,1),n)
# hasta resolucion, con costo de entrada
won=[]
for r in O.itertuples():
    ev=EVENTOS[r.evento]; cid=ev['cids'][r.caja]
    v=cj.set_index('condition_id').loc[cid].precio_final_si
    won.append((float(v)-r.compra)/r.compra)
mu,se,n=media_cluster(np.array(won),O.evento.values); print('hasta resolucion',round(100*mu,1),round(mu/se,1),n)
# todas las cajas 5-60 sin señal: deriva media a 3h (control de rebote)
import random
random.seed(1); dr=[];gg=[]
for f in S.sample(1500,random_state=1).itertuples():
    ev=EVENTOS[f.evento]; pw=precios_evento(ev,f.W)
    for k in range(len(pw)):
        if 0.05<=pw[k]<=0.6:
            x=precio(ev['cids'][k],f.W+3*3600)
            if x is not None: dr.append((x-pw[k])/pw[k]); gg.append(f.evento)
mu,se,n=media_cluster(np.array(dr),np.array(gg)); print('todas las cajas 5-60 a 3h',round(100*mu,1),round(mu/se,1),n)
