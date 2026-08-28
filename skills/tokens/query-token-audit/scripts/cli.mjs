#!/usr/bin/env node
// query-token-audit CLI — self-contained, zero-dep, Node >= 22
// Usage: node cli.mjs '<json_params>'
//
// Params: { binanceChainId, contractAddress }
//   binanceChainId  — "56" (BSC), "1" (ETH), "8453" (Base), "CT_501" (Solana)
//   contractAddress — token contract address

import { randomUUID } from 'node:crypto';

const TIMEOUT_MS = 10_000;
const UA = 'binance-web3/1.4 (Skill)';

async function call(url, body) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  let res;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'source': 'agent',
        'Accept-Encoding': 'identity',
        'User-Agent': UA,
      },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
  } catch {
    clearTimeout(timer);
    console.error('Network request failed');
    process.exit(3);
  }
  clearTimeout(timer);
  const data = await res.json();
  if (res.status >= 400) {
    console.error(`HTTP ${res.status}`);
    console.log(JSON.stringify(data, null, 2));
    process.exit(1);
  }
  return data;
}

// ---- CLI ----
if (process.argv.includes('--help') || process.argv.includes('-h') || !process.argv[2]) {
  console.log('Usage: node cli.mjs \'<json_params>\'\n');
  console.log('Params:');
  console.log('  binanceChainId  — "56" (BSC), "1" (ETH), "8453" (Base), "CT_501" (Solana)');
  console.log('  contractAddress — token contract address');
  process.exit(0);
}

let params = {};
try {
  params = JSON.parse(process.argv[2]);
} catch {
  console.error('Invalid JSON params');
  process.exit(1);
}

if (!params.binanceChainId || !params.contractAddress) {
  console.error('Missing required params: binanceChainId, contractAddress');
  process.exit(1);
}

params.requestId = randomUUID();

try {
  const result = await call(
    'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/security/token/audit',
    params,
  );
  console.log(JSON.stringify(result, null, 2));
} catch (err) {
  console.error(err.message);
  process.exit(err.exitCode || 1);
}
