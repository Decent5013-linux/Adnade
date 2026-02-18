import { chromium } from 'playwright';
import https from 'https';

const TARGET_URL = 'https://adnade.net/ptp/?user=zedred&subid=';
const TOTAL_TABS = 30;

const PROXY_SERVER = 'http://gateway.aluvia.io:8080';
let BASE_USERNAME = 'W2VnwvuJ';
let PROXY_PASSWORD = 'TfWwyEJH';

const IP_CHECK_URL = 'https://api.ipify.org?format=json';
const SECRET_URL = 'https://bot.vpsmail.name.ng/secret.txt';

const pages = [];
const workers = [];

function randomSession() {
  return Math.random().toString(36).substring(2, 10);
}

/* ---------- FETCH SECRET CREDS SAFE ---------- */

function fetchSecret(){
  return new Promise(resolve=>{
    const req = https.get(SECRET_URL,res=>{
      let raw="";
      res.on("data",d=>raw+=d);
      res.on("end",()=>{
        const lines = raw.trim().split(/\r?\n/).filter(Boolean);
        if(lines.length>=2)
          resolve({user:lines[0],pass:lines[1]});
        else resolve(null);
      });
    });

    req.on("error",()=>resolve(null));
    req.setTimeout(10000,()=>{
      req.destroy();
      resolve(null);
    });
  });
}

/* ---------- SECRET WATCHER ---------- */

function startSecretWatcher(){
  setInterval(async()=>{
    const s = await fetchSecret();
    if(!s) return;

    if(s.user!==BASE_USERNAME || s.pass!==PROXY_PASSWORD){
      console.log("New proxy creds detected → restarting workers");

      BASE_USERNAME = s.user;
      PROXY_PASSWORD = s.pass;

      await Promise.allSettled(workers.map(w=>w()));
      console.log("All workers restarted with new creds.");
    }

  },300000);
}

/* ---------- WORKER ---------- */

async function createWorker(tabIndex){

  let browser, context, page;
  let lastIP=null;
  let sessionId=randomSession();
  let sessionUsername=`${BASE_USERNAME}-session-${sessionId}`;
  let monitorTimer;
  let retryDelay=1000;

  async function safeClose(){
    try{
      await Promise.race([
        browser?.close(),
        new Promise(r=>setTimeout(r,5000))
      ]);
    }catch{}
  }

  async function launch(){
    try{

      browser = await chromium.launch({
        headless:false,
        proxy:{
          server:PROXY_SERVER,
          username:sessionUsername,
          password:PROXY_PASSWORD
        },
        args:[
          '--no-sandbox',
          '--ignore-certificate-errors',
          '--disable-gpu',
          '--disable-software-rasterizer'
        ]
      });

      context = await browser.newContext({
        ignoreHTTPSErrors:true
      });

      context.setDefaultTimeout(60000);
      context.setDefaultNavigationTimeout(60000);

      page = await context.newPage();
      pages.push(page);

      page.on("close",()=>{
        const i=pages.indexOf(page);
        if(i!==-1) pages.splice(i,1);
      });

      page.setDefaultTimeout(60000);
      page.setDefaultNavigationTimeout(60000);

      await page.goto(TARGET_URL,{
        waitUntil:'domcontentloaded',
        timeout:60000
      }).catch(()=>{});

      const res = await page.request.get(IP_CHECK_URL).catch(()=>null);
      if(res){
        const data = await res.json().catch(()=>null);
        if(data) lastIP=data.ip;
      }

      retryDelay=1000;

      console.log(`Tab ${tabIndex} started | Session ${sessionId} | IP: ${lastIP}`);

    }catch{
      console.log(`Tab ${tabIndex} launch failed. Retrying...`);
      await restart();
    }
  }

  async function restart(){

    clearInterval(monitorTimer);
    await safeClose();

    await new Promise(r=>setTimeout(r,retryDelay));
    retryDelay=Math.min(retryDelay*2,30000);

    sessionId=randomSession();
    sessionUsername=`${BASE_USERNAME}-session-${sessionId}`;
    lastIP=null;

    await launch();
    monitor();
  }

  async function monitor(){

    monitorTimer=setInterval(async()=>{
      try{

        if(!page || page.isClosed()){
          console.log(`Tab ${tabIndex} closed. Restarting`);
          return restart();
        }

        await page.evaluate(()=>1);

        const res = await page.request.get(IP_CHECK_URL).catch(()=>null);
        if(!res) return;

        const data = await res.json().catch(()=>null);
        if(!data) return;

        const currentIP=data.ip;

        if(lastIP && currentIP!==lastIP){
          console.log(`Tab ${tabIndex} IP changed ${lastIP} → ${currentIP}`);
          lastIP=currentIP;

          await page.goto(TARGET_URL,{
            waitUntil:'domcontentloaded',
            timeout:60000
          }).catch(()=>{});
        }

      }catch{
        console.log(`Tab ${tabIndex} crashed. Restarting`);
        await restart();
      }

    },2000);
  }

  workers.push(restart);

  await launch();
  monitor();
}

/* ---------- START ---------- */

(async()=>{

  console.log("Checking secret.txt for initial creds...");
  const init = await fetchSecret();
  if(init){
    BASE_USERNAME=init.user;
    PROXY_PASSWORD=init.pass;
    console.log("Using creds from secret.txt");
  }

  console.log(`Launching ${TOTAL_TABS} workers...`);

  await Promise.all(
    Array.from({length:TOTAL_TABS},(_,i)=>createWorker(i))
  );

  console.log("All workers active.");

  startSecretWatcher();

  process.on("SIGINT",async()=>{
    console.log("\nShutting down...");
    process.exit(0);
  });

})();
        
