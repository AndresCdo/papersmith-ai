# Open the dashboard from Windows with Ubuntu on WSL

In Ubuntu, start the dashboard from an initialized workspace:

```sh
smith ui .
```

Open `http://localhost:8080/` in a Windows browser. With the default loopback
bind, Windows and WSL2 ordinarily share localhost; keep the Ubuntu process
running while you use the dashboard. If your WSL networking configuration does
not forward localhost, check the WSL network settings before exposing the
server on another interface.

When Ubuntu has no browser handler, `smith ui` asks Windows Explorer to open
the URL in the Windows default browser. If a browser is already configured in
Ubuntu, it is used instead. `--no-browser` skips automatic opening altogether:
open the displayed dashboard URL manually in Windows. If the support terminal
is enabled, use the **login URL printed by the command** rather than the bare
root URL to activate its cookie; keep that URL private because it contains a
per-server secret. To avoid issuing a terminal login URL, start with
`smith ui . --no-browser --no-terminal` and open `http://localhost:8080/`.

If Windows does not open automatically, check that Windows interop is enabled
and `explorer.exe` is available from Ubuntu (`command -v explorer.exe`). Browser
launch failure does not stop the HTTP server; you can still paste the URL into
a Windows browser.
