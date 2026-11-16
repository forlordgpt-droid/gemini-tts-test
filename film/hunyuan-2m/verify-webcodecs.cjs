// Verify the exact browser encoding path required by the Hunyuan film.
// WebCodecs must run in a trustworthy origin; blank pages are not a valid export test.
const http = require('node:http');
const { chromium } = require('playwright');

async function main() {
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end('<!doctype html><html><head><meta charset="utf-8"></head><body>Hunyuan export capability check</body></html>');
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  let browser;
  try {
    // The 'chromium' channel selects the full Chromium's modern headless mode.
    browser = await chromium.launch({
      channel: 'chromium',
      headless: true,
      args: ['--enable-unsafe-swiftshader']
    });
    const page = await browser.newPage();
    const blank = await page.evaluate(() => ({
      url: location.href,
      secure: isSecureContext,
      VideoEncoder: typeof VideoEncoder
    }));
    await page.goto('http://127.0.0.1:' + server.address().port + '/', { waitUntil: 'load' });
    const result = await page.evaluate(async () => {
      const report = {
        url: location.origin,
        secure: isSecureContext,
        webgl2: !!document.createElement('canvas').getContext('webgl2'),
        VideoEncoder: typeof VideoEncoder,
        VideoFrame: typeof VideoFrame,
        audioEncoder: typeof AudioEncoder,
        h264Supported: false,
        encodedChunks: 0,
        encodedBytes: 0
      };
      if (typeof VideoEncoder !== 'function') return report;
      const config = {
        codec: 'avc1.420028',
        width: 1920,
        height: 1080,
        framerate: 30,
        bitrate: 5000000
      };
      const support = await VideoEncoder.isConfigSupported(config);
      report.h264Supported = support.supported;
      if (!support.supported) return report;
      const errors = [];
      const encoder = new VideoEncoder({
        output: chunk => { report.encodedChunks++; report.encodedBytes += chunk.byteLength; },
        error: error => errors.push(String(error))
      });
      encoder.configure(config);
      const canvas = document.createElement('canvas');
      canvas.width = 1920; canvas.height = 1080;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#126b75';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#ffe697';
      ctx.fillRect(100, 100, 600, 400);
      const frame = new VideoFrame(canvas, { timestamp: 0 });
      encoder.encode(frame, { keyFrame: true });
      frame.close();
      await encoder.flush();
      encoder.close();
      report.encoderErrors = errors;
      return report;
    });
    console.log('about:blank diagnostic:', JSON.stringify(blank));
    console.log('localhost browser export test:', JSON.stringify(result));
    if (!result.secure || !result.webgl2 || result.VideoEncoder !== 'function' ||
        !result.h264Supported || result.encodedChunks < 1 || result.encodedBytes < 1 ||
        result.encoderErrors?.length) {
      throw new Error('Required WebGL2 / WebCodecs 1920x1080 H.264 export check failed');
    }
    console.log('PASS: full Chromium served via trustworthy localhost can encode 1920x1080 H.264 using WebCodecs');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => {
  console.error('WebCodecs preflight error:', error.stack || String(error));
  process.exitCode = 1;
});
