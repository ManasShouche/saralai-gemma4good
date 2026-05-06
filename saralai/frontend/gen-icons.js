// Generates minimal PNG icons for SaralAI PWA using only Node built-ins.
// Colors: paper #FAF7F2 bg, accent #D9542B circle, white S letterform
const fs = require("fs");
const zlib = require("zlib");
const path = require("path");

function buildPng(size) {
  const w = size, h = size;
  // Raw RGBA pixel data
  const pixels = Buffer.alloc(w * h * 4);

  const bgR = 0xFA, bgG = 0xF7, bgB = 0xF2;
  const acR = 0xD9, acG = 0x54, acB = 0x2B;
  const cx = w / 2, cy = h / 2;
  const outerR = w * 0.40;
  const innerR = w * 0.28;

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      const dx = x - cx, dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist <= outerR) {
        // Accent circle
        pixels[i]   = acR;
        pixels[i+1] = acG;
        pixels[i+2] = acB;
        pixels[i+3] = 255;
        // White S approximation — simplified rectangular S shape
        const nx = (x - cx) / outerR;  // -1..1
        const ny = (y - cy) / outerR;  // -1..1
        const sw = 0.50, sh = 0.78;    // S bounding box in normalized space
        if (Math.abs(nx) < sw && Math.abs(ny) < sh) {
          // Three horizontal bars of the S
          const barH = 0.12;
          const inTop    = ny < -sh/2 + barH;
          const inMid    = Math.abs(ny) < barH;
          const inBot    = ny > sh/2 - barH;
          const inLeft   = nx < 0;
          const inRight  = nx > 0;
          // Vertical connector: top-right and bottom-left
          const inTopRight  = ny < 0 && inRight && ny > -sh/2 && ny < -barH;
          const inBotLeft   = ny > 0 && inLeft  && ny > barH  && ny < sh/2;
          if (inTop || inMid || inBot || inTopRight || inBotLeft) {
            pixels[i]   = 255;
            pixels[i+1] = 255;
            pixels[i+2] = 255;
            pixels[i+3] = 255;
          }
        }
      } else {
        // Paper background
        pixels[i]   = bgR;
        pixels[i+1] = bgG;
        pixels[i+2] = bgB;
        pixels[i+3] = 255;
      }
    }
  }

  // Pack scanlines: each row prefixed with filter byte 0 (None)
  const raw = Buffer.alloc(h * (1 + w * 4));
  for (let y = 0; y < h; y++) {
    raw[y * (1 + w * 4)] = 0;  // filter None
    pixels.copy(raw, y * (1 + w * 4) + 1, y * w * 4, (y + 1) * w * 4);
  }
  const compressed = zlib.deflateSync(raw);

  function chunk(type, data) {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length, 0);
    const typeB = Buffer.from(type);
    const crc = crc32(Buffer.concat([typeB, data]));
    const crcB = Buffer.alloc(4);
    crcB.writeInt32BE(crc, 0);
    return Buffer.concat([len, typeB, data, crcB]);
  }

  const IHDR_data = Buffer.alloc(13);
  IHDR_data.writeUInt32BE(w, 0);
  IHDR_data.writeUInt32BE(h, 4);
  IHDR_data[8] = 8;  // bit depth
  IHDR_data[9] = 2;  // color type RGB
  IHDR_data[10] = 0; // compression
  IHDR_data[11] = 0; // filter
  IHDR_data[12] = 0; // interlace

  // Override color type to RGBA
  IHDR_data[9] = 6;

  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const IEND = chunk("IEND", Buffer.alloc(0));
  return Buffer.concat([sig, chunk("IHDR", IHDR_data), chunk("IDAT", compressed), IEND]);
}

// CRC-32
function crc32(buf) {
  let crc = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) {
    crc ^= buf[i];
    for (let j = 0; j < 8; j++) {
      crc = (crc & 1) ? (crc >>> 1) ^ 0xEDB88320 : crc >>> 1;
    }
  }
  return (crc ^ 0xFFFFFFFF) | 0;
}

const out = path.join(__dirname, "public");
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, "icon-192.png"), buildPng(192));
fs.writeFileSync(path.join(out, "icon-512.png"), buildPng(512));
fs.writeFileSync(path.join(out, "icon-maskable-512.png"), buildPng(512));
console.log("Icons generated in public/");
