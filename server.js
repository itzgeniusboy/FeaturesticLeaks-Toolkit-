const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const HTML_FILE = path.join(__dirname, 'index.html');

const server = http.createServer((req, res) => {
  if (req.url === '/api/status' || req.url === '/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'online',
      app: 'FeaturesticLeaks PAK & LUA Master Suite',
      version: '2.7.0',
      python: 'Python 3.10',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Serve index.html for all page routes
  fs.readFile(HTML_FILE, 'utf8', (err, content) => {
    if (err) {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end('<h1>FeaturesticLeaks Engine Online</h1>');
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(content);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[FeaturesticLeaks] Preview server listening on port ${PORT}`);
});
