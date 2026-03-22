## GitHub Copilot Chat

- Extension: 0.39.2 (prod)
- VS Code: 1.111.0 (ce099c1ed25d9eb3076c11e4a280f3eb52b4fbeb)
- OS: win32 10.0.26200 x64
- GitHub Account: osayande-infosec

## Network

User Settings:
```json
  "http.systemCertificatesNode": true,
  "github.copilot.advanced.debug.useElectronFetcher": true,
  "github.copilot.advanced.debug.useNodeFetcher": false,
  "github.copilot.advanced.debug.useNodeFetchFetcher": true
```

Connecting to https://api.github.com:
- DNS ipv4 Lookup: 140.82.113.6 (11 ms)
- DNS ipv6 Lookup: Error (21 ms): getaddrinfo ENOTFOUND api.github.com
- Proxy URL: None (2 ms)
- Electron fetch (configured): HTTP 200 (95 ms)
- Node.js https: HTTP 200 (103 ms)
- Node.js fetch: HTTP 200 (103 ms)

Connecting to https://api.githubcopilot.com/_ping:
- DNS ipv4 Lookup: 140.82.113.21 (10 ms)
- DNS ipv6 Lookup: Error (49 ms): getaddrinfo ENOTFOUND api.githubcopilot.com
- Proxy URL: None (10 ms)
- Electron fetch (configured): HTTP 200 (113 ms)
- Node.js https: HTTP 200 (102 ms)
- Node.js fetch: HTTP 200 (115 ms)

Connecting to https://copilot-proxy.githubusercontent.com/_ping:
- DNS ipv4 Lookup: 4.249.131.160 (26 ms)
- DNS ipv6 Lookup: Error (20 ms): getaddrinfo ENOTFOUND copilot-proxy.githubusercontent.com
- Proxy URL: None (16 ms)
- Electron fetch (configured): HTTP 200 (142 ms)
- Node.js https: HTTP 200 (212 ms)
- Node.js fetch: HTTP 200 (184 ms)

Connecting to https://mobile.events.data.microsoft.com: HTTP 404 (82 ms)
Connecting to https://dc.services.visualstudio.com: HTTP 404 (222 ms)
Connecting to https://copilot-telemetry.githubusercontent.com/_ping: HTTP 200 (131 ms)
Connecting to https://copilot-telemetry.githubusercontent.com/_ping: HTTP 200 (163 ms)
Connecting to https://default.exp-tas.com: HTTP 400 (159 ms)

Number of system certificates: 109

## Documentation

In corporate networks: [Troubleshooting firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).