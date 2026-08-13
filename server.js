const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const os = require('os');

const PORT = process.env.PORT || 3000;

function runPythonCommand(cmd) {
  return new Promise((resolve) => {
    exec(cmd, { cwd: __dirname, timeout: 30000 }, (error, stdout, stderr) => {
      resolve({
        success: !error,
        code: error ? error.code : 0,
        stdout: stdout || '',
        stderr: stderr || (error ? error.message : '')
      });
    });
  });
}

function getSystemStats() {
  const totalMem = (os.totalmem() / (1024 * 1024 * 1024)).toFixed(2);
  const freeMem = (os.freemem() / (1024 * 1024 * 1024)).toFixed(2);
  const usedMem = (totalMem - freeMem).toFixed(2);
  return {
    platform: `${os.type()} ${os.arch()}`,
    uptimeSeconds: Math.floor(os.uptime()),
    nodeVersion: process.version,
    memory: { totalMem: `${totalMem} GB`, freeMem: `${freeMem} GB`, usedMem: `${usedMem} GB` },
    cpus: os.cpus().length
  };
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;

  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Route: /api/status
  if (pathname === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    const pyCheck = await runPythonCommand('python3 --version');
    const stats = getSystemStats();
    res.end(JSON.stringify({
      status: 'online',
      app: 'FeaturesticLeaks PAK & LUA Master Suite',
      version: '2.7.0',
      python: pyCheck.stdout.trim() || pyCheck.stderr.trim() || 'Python 3 Available',
      stats
    }));
    return;
  }

  // Route: /api/run-diagnostic
  if (pathname === '/api/run-diagnostic') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    const type = parsedUrl.searchParams.get('type') || 'full';
    let cmd = 'python3 -m py_compile FeaturesticLeaks.py pak/*.py lua/*.py core/*.py ai/*.py';
    if (type === 'pak') {
      cmd = 'python3 -m py_compile pak/*.py';
    } else if (type === 'lua') {
      cmd = 'python3 -m py_compile lua/*.py';
    } else if (type === 'import') {
      cmd = 'python3 -c "import FeaturesticLeaks; print(\'FeaturesticLeaks imported successfully!\')"';
    }
    const result = await runPythonCommand(cmd);
    res.end(JSON.stringify({ type, ...result }));
    return;
  }

  // Route: /api/docs
  if (pathname === '/api/docs') {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    const docFile = parsedUrl.searchParams.get('file') === 'readme' ? 'README.md' : 'DOCUMENTATION.md';
    const filePath = path.join(__dirname, docFile);
    if (fs.existsSync(filePath)) {
      res.end(fs.readFileSync(filePath, 'utf-8'));
    } else {
      res.end('Documentation file not found.');
    }
    return;
  }

  // Route: / (HTML UI)
  if (pathname === '/' || pathname === '/index.html') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(getDashboardHTML());
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('404 Not Found');
});

function getDashboardHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FeaturesticLeaks Master Suite v2.7 Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-color: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f293d;
      --accent-green: #00ff88;
      --accent-cyan: #00e1ff;
      --accent-purple: #a855f7;
      --accent-yellow: #f59e0b;
      --accent-red: #ef4444;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg-color);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      line-height: 1.6;
    }
    header {
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
      border-bottom: 1px solid var(--card-border);
      padding: 1.5rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-icon {
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.4rem;
      color: #000;
      box-shadow: 0 0 15px rgba(0,255,136,0.3);
    }
    .brand-title {
      font-size: 1.4rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(90deg, #ffffff, #a5f3fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .brand-subtitle {
      font-size: 0.8rem;
      color: var(--accent-green);
      font-weight: 600;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(0, 255, 136, 0.1);
      border: 1px solid rgba(0, 255, 136, 0.3);
      color: var(--accent-green);
      padding: 0.4rem 0.9rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      background-color: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-green);
    }
    main {
      flex: 1;
      max-width: 1280px;
      width: 100%;
      margin: 0 auto;
      padding: 2rem 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }
    .card {
      background-color: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      transition: border-color 0.2s, transform 0.2s;
    }
    .card:hover {
      border-color: rgba(0, 225, 255, 0.4);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .card-desc {
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    .stat-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
    }
    .stat-item {
      display: flex;
      justify-content: space-between;
      padding: 0.4rem 0.6rem;
      background: rgba(255,255,255,0.03);
      border-radius: 6px;
    }
    .btn-group {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .btn {
      font-family: inherit;
      background: linear-gradient(135deg, #1e293b, #0f172a);
      color: var(--text-main);
      border: 1px solid var(--card-border);
      padding: 0.6rem 1.2rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }
    .btn:hover {
      background: linear-gradient(135deg, #334155, #1e293b);
      border-color: var(--accent-cyan);
      color: #fff;
    }
    .btn-primary {
      background: linear-gradient(135deg, #0284c7, #0369a1);
      border-color: #38bdf8;
      color: #fff;
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #0369a1, #075985);
    }
    .terminal-box {
      background-color: #050811;
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      color: var(--accent-green);
      max-height: 350px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .credits {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.85rem;
      padding: 1.5rem;
      border-top: 1px solid var(--card-border);
      margin-top: auto;
    }
    a { color: var(--accent-cyan); text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-icon">⚡</div>
      <div>
        <div class="brand-title">FeaturesticLeaks Master Suite</div>
        <div class="brand-subtitle">Termux / Android Game Reverse Engineering & PAK Suite v2.7</div>
      </div>
    </div>
    <div class="status-badge">
      <span class="status-dot"></span> Server & Diagnostic Engine Online
    </div>
  </header>

  <main>
    <div class="grid">
      <!-- System Overview -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">🖥️ System & Environment</div>
        </div>
        <div class="card-desc">Runtime environment and memory inspection.</div>
        <div class="stat-list" id="sys-stats">
          <div class="stat-item"><span>Status</span><span style="color:var(--accent-green)">Active</span></div>
          <div class="stat-item"><span>Platform</span><span id="stat-platform">Loading...</span></div>
          <div class="stat-item"><span>Node.js</span><span id="stat-node">Loading...</span></div>
          <div class="stat-item"><span>RAM Used</span><span id="stat-ram">Loading...</span></div>
        </div>
      </div>

      <!-- PAK Engine -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">📦 PAK & OBB Engine</div>
        </div>
        <div class="card-desc">High-speed Unreal Engine / Tencent `.pak` container manager.</div>
        <div class="stat-list">
          <div class="stat-item"><span>Large File Limit</span><span style="color:var(--accent-cyan)">200 MB (Streaming)</span></div>
          <div class="stat-item"><span>Crypto</span><span>SM4 / AES Decryption</span></div>
          <div class="stat-item"><span>Compression</span><span>Zstandard / Zlib / Dict</span></div>
        </div>
      </div>

      <!-- Lua Master Suite -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">🌙 Lua Master Suite</div>
        </div>
        <div class="card-desc">Bytecode compilation, decompilation, and script merger engine.</div>
        <div class="stat-list">
          <div class="stat-item"><span>Compiler</span><span style="color:var(--accent-green)">Lua 5.1 / LuaJIT</span></div>
          <div class="stat-item"><span>Security</span><span>String Obfuscator & Auditor</span></div>
          <div class="stat-item"><span>Header Fixer</span><span>Auto-Repair Magic Header</span></div>
        </div>
      </div>
    </div>

    <!-- Diagnostic Control Panel -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">⚡ Interactive Diagnostic Control Center</div>
      </div>
      <div class="card-desc">Run real-time integrity checks, verify Python modules, and test suite functions.</div>
      <div class="btn-group">
        <button class="btn btn-primary" onclick="runDiagnostic('full')">▶️ Full System Integrity Check</button>
        <button class="btn" onclick="runDiagnostic('pak')">📦 Verify PAK Module</button>
        <button class="btn" onclick="runDiagnostic('lua')">🌙 Verify Lua Module</button>
        <button class="btn" onclick="runDiagnostic('import')">🐍 Test Python Import</button>
        <button class="btn" onclick="loadDocs('readme')">📖 View README</button>
        <button class="btn" onclick="loadDocs('doc')">📄 View Manual Docs</button>
      </div>

      <div class="terminal-box" id="terminal-output">Ready. Click a diagnostic button above to run real-time checks...</div>
    </div>
  </main>

  <footer class="credits">
    Developed by <a href="https://t.me/L359D" target="_blank">@L359D</a> | 
    Official Channel: <a href="https://t.me/FeaturesticLeaks" target="_blank">t.me/FeaturesticLeaks</a> | 
    Maintained by <a href="https://t.me/itzraviking" target="_blank">@itzraviking</a>
  </footer>

  <script>
    async function fetchStats() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('stat-platform').textContent = data.stats.platform;
        document.getElementById('stat-node').textContent = data.stats.nodeVersion;
        document.getElementById('stat-ram').textContent = \`\${data.stats.memory.usedMem} / \${data.stats.memory.totalMem}\`;
      } catch (err) {
        console.error('Stats error:', err);
      }
    }

    async function runDiagnostic(type) {
      const term = document.getElementById('terminal-output');
      term.textContent = \`[...] Running diagnostic '\${type}'...\n\`;
      try {
        const res = await fetch(\`/api/run-diagnostic?type=\${type}\`);
        const data = await res.json();
        if (data.success) {
          term.style.color = '#00ff88';
          term.textContent = \`[✅ SUCCESS] Diagnostic '\${type}' completed clean with exit code 0.\n\n\${data.stdout || '(No error logs found)'}\`;
        } else {
          term.style.color = '#ef4444';
          term.textContent = \`[✖ ERROR] Diagnostic '\${type}' returned exit code \${data.code}:\n\n\${data.stderr || data.stdout}\`;
        }
      } catch (err) {
        term.style.color = '#ef4444';
        term.textContent = \`[✖ FAILED] API call failed: \${err.message}\`;
      }
    }

    async function loadDocs(file) {
      const term = document.getElementById('terminal-output');
      term.style.color = '#00e1ff';
      term.textContent = \`[...] Loading \${file}...\n\`;
      try {
        const res = await fetch(\`/api/docs?file=\${file}\`);
        const text = await res.text();
        term.textContent = text;
      } catch (err) {
        term.style.color = '#ef4444';
        term.textContent = \`[✖ FAILED] Could not load docs: \${err.message}\`;
      }
    }

    fetchStats();
    setInterval(fetchStats, 10000);
  </script>
</body>
</html>`;
}

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[+] FeaturesticLeaks Server listening on http://0.0.0.0:${PORT}`);
});
