// PNG luminance stats: IHDR -> IDAT concat -> inflate -> unfilter -> sample. 8-bit RGB/RGBA, non-interlaced.
import { readFileSync } from 'fs';
import { inflateSync } from 'zlib';

const [file] = process.argv.slice(2);
const buf = readFileSync(file);
if (buf.readUInt32BE(0) !== 0x89504e47) { console.log(JSON.stringify({ err: 'not png' })); process.exit(1); }

let off = 8, w = 0, h = 0, depth = 0, ctype = 0, interlace = 0;
const idats = [];
while (off < buf.length) {
  const len = buf.readUInt32BE(off);
  const type = buf.toString('ascii', off + 4, off + 8);
  const data = buf.subarray(off + 8, off + 8 + len);
  if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); depth = data[8]; ctype = data[9]; interlace = data[12]; }
  else if (type === 'IDAT') idats.push(data);
  else if (type === 'IEND') break;
  off += 12 + len;
}
if (depth !== 8 || (ctype !== 2 && ctype !== 6) || interlace !== 0) { console.log(JSON.stringify({ err: 'unsupported png', depth, ctype, interlace })); process.exit(1); }
const ch = ctype === 6 ? 4 : 3;
const stride = w * ch;
const raw = inflateSync(Buffer.concat(idats));
const img = Buffer.alloc(h * stride);
const paeth = (a, b, c) => { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); return pa <= pb && pa <= pc ? a : pb <= pc ? b : c; };
for (let y = 0; y < h; y++) {
  const f = raw[y * (stride + 1)];
  const rowIn = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
  const row = img.subarray(y * stride, (y + 1) * stride);
  const prev = y > 0 ? img.subarray((y - 1) * stride, y * stride) : null;
  for (let x = 0; x < stride; x++) {
    const left = x >= ch ? row[x - ch] : 0;
    const up = prev ? prev[x] : 0;
    const ul = prev && x >= ch ? prev[x - ch] : 0;
    let v = rowIn[x];
    if (f === 1) v += left; else if (f === 2) v += up; else if (f === 3) v += (left + up) >> 1; else if (f === 4) v += paeth(left, up, ul);
    row[x] = v & 255;
  }
}
let n = 0, sum = 0, min = 255, max = 0, lit = 0;
const crop = process.argv[3] ? process.argv[3].split(',').map(Number) : [0, 0, w, h];
const [cx, cy, cw, chh] = crop;
const stepX = Math.max(1, Math.floor(cw / 200)), stepY = Math.max(1, Math.floor(chh / 120));
for (let y = cy; y < cy + chh; y += stepY) for (let x = cx; x < cx + cw; x += stepX) {
  const i = y * stride + x * ch;
  const l = (img[i] * 0.2126 + img[i + 1] * 0.7152 + img[i + 2] * 0.0722);
  n++; sum += l; if (l < min) min = l; if (l > max) max = l; if (l > 16) lit++;
}
console.log(JSON.stringify({ w, h, ctype, mean: +(sum / n).toFixed(1), min: +min.toFixed(0), max: +max.toFixed(0), litPct: +((lit / n) * 100).toFixed(1) }));
