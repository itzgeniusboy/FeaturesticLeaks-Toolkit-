const http = require('http');

const PORT = 3000;

const server = http.createServer((req, res) => {
  if (req.url === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'online', bot: '24/7 Engine Active' }));
  }

  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FeaturesticLeaks v2.5.0 - VIP Engine</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #0b0f19; color: #f3f4f6; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 32px; max-width: 550px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; }
        .badge { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; display: inline-block; margin-bottom: 16px; }
        h1 { font-size: 24px; font-weight: 700; margin-bottom: 8px; color: #ffffff; }
        p { color: #9ca3af; font-size: 14px; line-height: 1.6; margin-bottom: 24px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; text-align: left; margin-bottom: 24px; }
        .stat-box { background: #1f2937; padding: 12px 16px; border-radius: 8px; border: 1px solid #374151; }
        .stat-title { font-size: 11px; text-transform: uppercase; color: #6b7280; font-weight: 600; letter-spacing: 0.5px; }
        .stat-val { font-size: 14px; font-weight: 600; color: #e5e7eb; margin-top: 4px; }
        .footer { font-size: 12px; color: #6b7280; border-top: 1px solid #1f2937; padding-top: 16px; }
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">● Engine Online</span>
        <h1>⚡ FEATURESTIC LEAKS v2.5.0</h1>
        <p>VIP Modding Tool & Exploit Suite for PAK, OBB & LUA Bytecode Manipulation.</p>
        
        <div class="grid">
            <div class="stat-box">
                <div class="stat-title">Platform</div>
                <div class="stat-val">Termux & GitHub Actions</div>
            </div>
            <div class="stat-box">
                <div class="stat-title">Telegram Bot</div>
                <div class="stat-val">24/7 Active Listener</div>
            </div>
            <div class="stat-box">
                <div class="stat-title">Interactive UI</div>
                <div class="stat-val">Persistent Touch Buttons</div>
            </div>
            <div class="stat-box">
                <div class="stat-title">API Keys</div>
                <div class="stat-val">Per-User Multi Key</div>
            </div>
        </div>

        <div class="footer">
            Developed by @L359D • FeaturesticLeaks VIP Suite
        </div>
    </div>
</body>
</html>
  `);
});

server.listen(PORT, () => {
  console.log(`FeaturesticLeaks status server running on port ${PORT}`);
});
