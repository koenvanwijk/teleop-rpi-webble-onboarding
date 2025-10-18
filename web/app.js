const UUID_SERVICE = '12345678-1234-5678-1234-56789abc0000';
const UUID_TOKEN   = '12345678-1234-5678-1234-56789abc0001';
const UUID_CMD     = '12345678-1234-5678-1234-56789abc0002';
const UUID_SSID    = '12345678-1234-5678-1234-56789abc0003';
const UUID_PASS    = '12345678-1234-5678-1234-56789abc0004';
const UUID_RESP    = '12345678-1234-5678-1234-56789abc0005';

let device, server, service, ch = {};

function qs(s){return document.querySelector(s)}

async function connect() {
  try{
    device = await navigator.bluetooth.requestDevice({
      filters: [{ services:[UUID_SERVICE] }]
    });
    qs('#dev').textContent = 'Gekozen: ' + device.name;
    server = await device.gatt.connect();
    service = await server.getPrimaryService(UUID_SERVICE);
    ch.token = await service.getCharacteristic(UUID_TOKEN);
    ch.cmd   = await service.getCharacteristic(UUID_CMD);
    ch.ssid  = await service.getCharacteristic(UUID_SSID);
    ch.pass  = await service.getCharacteristic(UUID_PASS);
    ch.resp  = await service.getCharacteristic(UUID_RESP);

    // Auto-fill token from URL
    const url = new URL(window.location.href);
    const t = url.searchParams.get('token');
    if (t && !qs('#token').value) qs('#token').value = t;

    await sendToken();
    await scan();
    await status();
  }catch(e){
    qs('#dev').textContent = 'Fout: ' + e;
  }
}

async function sendToken(){
  const token = qs('#token').value.trim();
  if(!token){ alert('Token ontbreekt'); return; }
  await ch.token.writeValue(new TextEncoder().encode(token));
}

async function scan(){
  await ch.cmd.writeValue(new TextEncoder().encode('scan'));
  const resp = await ch.resp.readValue();
  const obj = JSON.parse(new TextDecoder().decode(resp));
  const sel = qs('#ssid');
  sel.innerHTML = '';
  (obj.ssids||[]).forEach(s=>{
    const opt = document.createElement('option');
    opt.textContent = s;
    opt.value = s;
    sel.appendChild(opt);
  });
}

async function connectWifi(){
  const ssid = qs('#ssid').value;
  const pass = qs('#pass').value;
  if(!ssid || !pass){ alert('SSID en wachtwoord nodig'); return; }
  await ch.ssid.writeValue(new TextEncoder().encode(ssid));
  await ch.pass.writeValue(new TextEncoder().encode(pass));
  await ch.cmd.writeValue(new TextEncoder().encode('connect'));
  const resp = await ch.resp.readValue();
  const obj = JSON.parse(new TextDecoder().decode(resp));
  qs('#status').textContent = obj.ok ? 'Verbonden (probeer status)' : ('Fout: ' + (obj.error||'onbekend'));
}

async function status(){
  await ch.cmd.writeValue(new TextEncoder().encode('status'));
  const resp = await ch.resp.readValue();
  const obj = JSON.parse(new TextDecoder().decode(resp));
  if(obj.ok){
    const s = obj.status||{};
    qs('#status').textContent = `SSID=${s.ssid||'-'} IP=${s.ip||'-'}`;
  }else{
    qs('#status').textContent = 'Error: ' + (obj.error||'?');
  }
}

qs('#btnConnect').addEventListener('click', connect);
qs('#btnScan').addEventListener('click', scan);
qs('#btnConnectWifi').addEventListener('click', connectWifi);
qs('#btnStatus').addEventListener('click', status);

// Autofill token from URL if present
const url = new URL(window.location.href);
const t = url.searchParams.get('token');
if (t) qs('#token').value = t;
