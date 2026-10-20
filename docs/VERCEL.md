# Vercel hackathon preview

Owner-confirmed topology (October 20, 2026): `web` public at `/`, `backend`
internal only. `core` is an imported Python library, not an HTTP service.
No bindings are declared: the Vite frontend runs the existing labeled fixture
simulation entirely in the browser and makes no backend calls. A runtime
binding cannot be read by static browser JavaScript or at Vite build time.

The API's existing `/api` paths do not change. There is intentionally no public
rewrite to the backend. The public UI says fixture simulation, synthetic data,
and no texts leave this app. This preview does not demonstrate live messaging,
Band Desktop, Cognee, or real source ingestion. Those remain in the local
integration environment and the separately labeled demo video.

The web build copies the reviewed `demo/video-out/payrollpilot-demo.mp4` to
`/demo.mp4` for direct playback. Only that final file is included from `demo/`.

Deploy from a sanitized checkout without environment files or private data:
`vercel deploy -y`. For a local services test on unused ports, use
`vercel dev -L`; do not replace the running recording stack.

The internal backend uses ephemeral `/tmp` SQLite by default. This is not a
durable hosted workflow. Full hosting needs persistent state, authentication,
a reachable messaging bridge, and a supported Band runtime. Do not add local
credentials, phone recipients, or private snapshots to this public preview.
