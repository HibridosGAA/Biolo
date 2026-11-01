#!/usr/bin/env python3
"""Convierte el PDF del banco de preguntas IB Biologia NM en una web de practica.
Uso:  python generar.py "archivo.pdf"
Requiere: poppler (pdftoppm), tesseract, y  pip install pillow numpy scipy pytesseract
Salida: carpeta banco/ (data.js + img/*.webp). Copia index.html junto a banco/ y abrelo."""
import sys,os,re,json,glob,shutil,subprocess
import numpy as np
from PIL import Image,ImageOps
from scipy import ndimage as ndi
import pytesseract
PDF=sys.argv[1]; OUT='banco'; TMP='_pag'
NOM={'1.1':'Introducción a las células','1.2':'Ultraestructura de las células','1.3':'Estructura de las membranas','1.4':'Transporte de membrana','1.5':'El origen de las células','1.6':'División celular','2.1':'Moléculas para el metabolismo','2.2':'Agua','2.3':'Glúcidos y lípidos','2.4':'Proteínas','2.5':'Enzimas','2.6':'Estructura del ADN y el ARN','2.7':'Replicación, transcripción y traducción del ADN','2.8':'Respiración celular','2.9':'Fotosíntesis','3.1':'Genes','3.2':'Cromosomas','3.3':'Meiosis','3.4':'Herencia','3.5':'Modificación genética y biotecnología','4.1':'Especies, comunidades y ecosistemas','4.2':'Flujo de energía','4.3':'Ciclo del carbono','4.4':'Cambio climático','5.1':'Pruebas de la evolución','5.2':'Selección natural','5.3':'Clasificación de la biodiversidad','5.4':'Cladística','6.1':'Digestión y absorción','6.2':'El sistema sanguíneo','6.3':'Defensa contra las enfermedades infecciosas','6.4':'Intercambio de gases','6.5':'Neuronas y sinapsis','6.6':'Hormonas, homeostasis y reproducción'}
UNI={'1':'Biología celular','2':'Biología molecular','3':'Genética','4':'Ecología','5':'Evolución y biodiversidad','6':'Fisiología humana'}
os.makedirs(TMP,exist_ok=True); os.makedirs(OUT+'/img',exist_ok=True)
from concurrent.futures import ProcessPoolExecutor
NP=int(subprocess.run(['pdfinfo',PDF],capture_output=True,text=True).stdout.split('Pages:')[1].split()[0])
def rend(r): subprocess.run(['pdftoppm','-f',str(r[0]),'-l',str(r[1]),'-r','110','-png',PDF,TMP+'/p'],check=True)
if len(glob.glob(TMP+'/p-*.png'))<NP:
    print('Convirtiendo',NP,'páginas...'); W_=max(1,os.cpu_count() or 1); st=-(-NP//(W_*2))
    with ProcessPoolExecutor(W_) as ex: list(ex.map(rend,[(i,min(i+st-1,NP)) for i in range(1,NP+1,st)]))
files=sorted(glob.glob(TMP+'/p-*.png'))
def clasifica(im):
    W,H=im.size
    h=pytesseract.image_to_string(im.crop((0,int(.03*H),W,int(.10*H))))
    m=re.search(r'Tema\s*(\d)\s*\.\s*(\d)',h)
    if not m: return None
    s=pytesseract.image_to_string(im.crop((0,int(.115*H),W,int(.20*H))))
    return f'{m[1]}.{m[2]}',bool(re.match(r'\s*R[eo]spuestas?\s*[:;.]?',s,re.I))
def cl_f(f): return clasifica(Image.open(f).convert('L'))
with ProcessPoolExecutor(max(1,os.cpu_count() or 1)) as ex: CL=list(ex.map(cl_f,files,chunksize=4))
T={}
for k,(f,c) in enumerate(zip(files,CL),1):
    if c is None:
        if k>4: print('  aviso: pág',k,'sin tema, se omite')
        continue
    t,esresp=c; d=T.setdefault(t,{'q':[],'a':None})
    (d.__setitem__('a',f) if esresp else d['q'].append(f))
def inicios(im):
    W,H=im.size; a=np.array(im.convert('L'))<140
    top,bot=int(.115*H),int(.90*H); sub=a[top:bot]; r=np.where(sub.sum(1)>0)[0]
    cend=top+(r.max() if len(r) else 0)
    lab,_=ndi.label(a[top:bot,:int(.2*W)]); m=[]
    for ys,xs in ndi.find_objects(lab):
        h=ys.stop-ys.start; w=xs.stop-xs.start
        if .06*W<xs.start<.11*W and 8<h<24 and w<.02*W+8: m.append(top+int(ys.start))
    m.sort(); o=[]
    for s in m:
        if not o or s-o[-1]>20: o.append(s)
    return o,cend
def trim(c):
    a=np.array(c.convert('L'))<170; r=np.where(a.sum(1)>0)[0]
    return c.crop((0,max(r[0]-6,0),c.width,c.height)) if len(r) else c
def sin_nota(c):
    a=np.array(c.convert('L'))<170; r=np.where(a.sum(1)>0)[0]
    if not len(r): return c
    runs=[];s=pr=r[0]
    for y in r[1:]:
        if y-pr>14: runs.append((s,pr)); s=y
        pr=y
    runs.append((s,pr))
    return c.crop((0,0,c.width,runs[-1][0]-6)) if len(runs)>1 and runs[-1][1]-runs[-1][0]<25 else c
def une(a,b):
    g=Image.new('RGB',(a.width,a.height+b.height+10),'white'); g.paste(a,(0,0)); g.paste(b,(0,a.height+10)); return g
def filas(g):
    r=(g<140).sum(1)>0; out=[]; s0=None
    for y,v in enumerate(r):
        if v and s0 is None: s0=y
        if not v and s0 is not None:
            if y-s0>8: out.append((s0,y))
            s0=None
    return out
CLAVE66="ADADBBBDDBDCDCBCBDDDCADBBDBDBBCACDD"   # clave conocida del tema 6.6 (verificada a mano) para calibrar las letras
def glifo(row):
    lab,n=ndi.label(row<140)
    if not n: return None
    sl=ndi.find_objects(lab); k=max(range(n),key=lambda i:sl[i][1].stop); ys,xs=sl[k]
    g=Image.fromarray(row[ys,xs]); return np.array(g.resize((24,24),Image.LANCZOS),dtype=float)/255
def filas_resp(f):
    pg=int(re.findall(r'(\d+)\.png',f)[0]); base=TMP+'/r'
    subprocess.run(['pdftoppm','-f',str(pg),'-l',str(pg),'-r','250','-gray','-png',PDF,base],check=True)
    p=glob.glob(base+'*.png')[0]; im=np.array(Image.open(p).convert('L')); os.remove(p)
    H,W=im.shape; rows=[]
    for ci,(x0,x1) in enumerate(((0,.42),(.42,1))):
        col=im[int(.11*H):int(.91*H),int(x0*W):int(x1*W)]; fs=filas(col)
        if ci==0 and fs: fs=fs[1:]
        rows+=[glifo(col[a:b]) for a,b in fs]
    return rows
PLANT={}
def respuestas(f):
    if not PLANT and '6.6' in T and T['6.6']['a']:
        g=filas_resp(T['6.6']['a'])
        for l in 'ABCD': PLANT[l]=np.mean([x for x,c in zip(g,CLAVE66) if c==l and x is not None],axis=0)
    res={}
    for i,g in enumerate(filas_resp(f),1):
        res[i]='?' if g is None else min(PLANT,key=lambda l:((g-PLANT[l])**2).sum())
    return res
DATA=[]; rev=[]
for t in sorted(T,key=lambda s:tuple(map(int,s.split('.')))):
    d=T[t]; crops=[]; pend=None
    for pi,f in enumerate(d['q']):
        im=Image.open(f).convert('RGB'); W,H=im.size; m,cend=inicios(im)
        x0,x1=int(.065*W),int(.94*W)
        if pend is not None and (not m or m[0]>250):
            y1=(m[0]-14) if m else cend+10
            crops[-1]=une(sin_nota(crops[-1]),trim(im.crop((x0,int(.115*H),x1,y1))))
        for i,s in enumerate(m):
            e=(m[i+1]-14) if i+1<len(m) else cend+10
            crops.append(im.crop((x0,s-8,x1,e)))
        pend=True
    resp=respuestas(d['a']) if d['a'] else {}
    n=len(crops); faltan=[i for i in range(1,n+1) if resp.get(i,'?')=='?']
    if not d['a'] or faltan or len(resp)!=n: rev.append(f'Tema {t}: {n} preguntas detectadas, {len(resp)} respuestas leídas, faltan {faltan}')
    qs=[]
    for i,c in enumerate(crops,1):
        p=f'img/{t}-{i:02d}.webp'; c.save(f'{OUT}/{p}',quality=80,method=6)
        qs.append({'n':i,'a':resp.get(i,'?'),'img':p})
    DATA.append({'id':t,'nombre':NOM.get(t,''),'unidad':t.split('.')[0],'unidadNombre':UNI.get(t[0],''),'preguntas':qs})
    print(f'Tema {t}: {n} preguntas, {len(resp)} respuestas')
open(OUT+'/data.js','w',encoding='utf-8').write('const DATA='+json.dumps(DATA,ensure_ascii=False)+';')
open('revisar.txt','w',encoding='utf-8').write('\n'.join(rev) or 'Todo coincide: preguntas y respuestas.')
print('\nListo. Revisa revisar.txt'); print('\n'.join(rev) or 'Sin problemas de conteo.')
