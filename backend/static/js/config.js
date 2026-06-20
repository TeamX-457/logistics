// Same-origin by default — works whether you're on localhost:8000 in dev
// or behind a real domain in production. Override only if the API truly
// lives on a different host than the page serving this script.
const BASE_URL = `${window.location.origin}/api`;
const WS_BASE_URL = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`;
