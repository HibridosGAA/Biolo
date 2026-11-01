// Servidor sin dependencias: protege toda la web con contraseña. Uso: node server.js
const http=require('http'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const PASS=process.env.APP_PASSWORD;
if(!PASS){console.error('Falta la variable de entorno APP_PASSWORD');process.exit(1)}
const SECRET=process.env.SESSION_SECRET||crypto.createHash('sha256').update('bio-nm|'+PASS).digest('hex');
const PUB=path.join(__dirname,'public'),LOGIN=fs.readFileSync(path.join(__dirname,'login.html'),'utf8');
const YEAR=365*24*3600;  // la sesión dura 1 año y se renueva cada vez que entras
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.json':'application/json','.ico':'image/x-icon','.txt':'text/plain; charset=utf-8'};
const h=s=>crypto.createHash('sha256').update(s).digest();
const sign=e=>crypto.createHmac('sha256',SECRET).update(String(e)).digest('hex');
const token=()=>{const e=Math.floor(Date.now()/1000)+YEAR;return e+'.'+sign(e)};
function valido(req){
  const m=/(?:^|;\s*)sid=([^;]+)/.exec(req.headers.cookie||'');if(!m)return false;
  const [e,sg]=m[1].split('.');if(!e||!sg||+e<Date.now()/1000)return false;
  const a=Buffer.from(sg),b=Buffer.from(sign(e));return a.length===b.length&&crypto.timingSafeEqual(a,b);
}
const seguro=req=>req.socket.encrypted||req.headers['x-forwarded-proto']==='https';
const cookie=(req,v,age)=>`sid=${v}; HttpOnly; SameSite=Lax; Path=/; Max-Age=${age}${seguro(req)?'; Secure':''}`;
const base={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'};
const intentos=new Map();  // límite de intentos por IP: 8 cada 15 minutos
function bloqueado(ip){const n=Date.now(),r=(intentos.get(ip)||[]).filter(t=>n-t<9e5);intentos.set(ip,r);return r.length>=8}
function fallo(ip){const r=intentos.get(ip)||[];r.push(Date.now());intentos.set(ip,r)}
function enviar(res,code,body,extra={}){res.writeHead(code,{...base,'Cache-Control':'no-store',...extra});res.end(body)}
function paginaLogin(res,err,code=200){enviar(res,code,LOGIN.replace('<!--ERR-->',err?`<p class="err" role="alert">${err}</p>`:''),{'Content-Type':'text/html; charset=utf-8'})}
function cuerpo(req){return new Promise(r=>{let d='';req.on('data',c=>{d+=c;if(d.length>2048)req.destroy()});req.on('end',()=>r(d))})}
http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://x'),ip=(req.headers['x-forwarded-for']||req.socket.remoteAddress||'').split(',')[0].trim();
  if(url.pathname==='/healthz')return enviar(res,200,'ok');
  if(url.pathname==='/login'){
    if(req.method==='POST'){
      if(bloqueado(ip))return paginaLogin(res,'Demasiados intentos. Espera unos minutos.',429);
      const p=new URLSearchParams(await cuerpo(req)).get('password')||'';
      if(crypto.timingSafeEqual(h(p),h(PASS))){return enviar(res,302,'',{Location:'/','Set-Cookie':cookie(req,token(),YEAR)})}
      fallo(ip);return paginaLogin(res,'Contraseña incorrecta.',401);
    }
    if(valido(req))return enviar(res,302,'',{Location:'/'});
    return paginaLogin(res,'');
  }
  if(url.pathname==='/logout'&&req.method==='POST')return enviar(res,204,'',{'Set-Cookie':cookie(req,'',0)});
  if(!valido(req)){
    if((req.headers.accept||'').includes('text/html'))return enviar(res,302,'',{Location:'/login'});
    return enviar(res,401,'No autorizado');
  }
  if(req.method!=='GET'&&req.method!=='HEAD')return enviar(res,405,'Método no permitido');
  let rel;try{rel=decodeURIComponent(url.pathname)}catch(e){return enviar(res,400,'Solicitud inválida')}
  if(rel.endsWith('/'))rel+='index.html';
  const f=path.join(PUB,path.normalize(rel));
  if(!f.startsWith(PUB+path.sep))return enviar(res,403,'Prohibido');
  fs.readFile(f,(err,data)=>{
    if(err)return enviar(res,404,'No encontrado');
    const ext=path.extname(f).toLowerCase(),html=ext==='.html';
    const hd={...base,'Content-Type':MIME[ext]||'application/octet-stream','Cache-Control':html?'private, no-cache':'private, max-age=86400'};
    if(html)hd['Set-Cookie']=cookie(req,token(),YEAR);  // renueva la sesión: nunca se cierra mientras uses la app
    res.writeHead(200,hd);res.end(req.method==='HEAD'?undefined:data);
  });
}).listen(process.env.PORT||3000,'0.0.0.0',()=>console.log('Servidor listo en el puerto '+(process.env.PORT||3000)));
