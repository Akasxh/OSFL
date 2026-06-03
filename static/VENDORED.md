# Vendored third-party assets

These browser libraries are committed under `static/` so the dashboard runs with
**zero network access** (no CDN dependency). Both are MIT-licensed; their license texts
are in `static/THIRD_PARTY_LICENSES/`. The `sha384` below is the integrity pin for the
exact committed bytes (`openssl dgst -sha384 -binary <file> | openssl base64 -A`).

| File | Library | Version | Source | License | Integrity (sha384) |
|------|---------|---------|--------|---------|--------------------|
| `alpine.min.js` | Alpine.js | 3.14.1 | https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js | MIT | `l8f0VcPi/M1iHPv8egOnY/15TDwqgbOR1anMIJWvU6nLRgZVLTLSaNqi/TOoT5Fh` |
| `tailwind.js` | Tailwind CSS (Play CDN) | 3.x | https://cdn.tailwindcss.com | MIT | `mS5Uq7sE90lgbBDN8xgf34ibEgbZo4gB3tfLY40ZRle+M188BQw8onzNHg6GUZaA` |

Notes:
- `tailwind.js` is the **Play CDN** build (an in-browser JIT compiler). It is convenient
  for a self-contained demo but is not a production CSS pipeline; a real deployment would
  precompile with the Tailwind CLI. It does not pin a patch version, hence the hash pin.
- Served locally from `static/`, so Subresource Integrity on the `<script>` tag does not
  apply; the hashes here are the provenance record instead.
