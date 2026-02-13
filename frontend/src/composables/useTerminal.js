import { ref, watch, nextTick, onUnmounted } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

export function useTerminal({ authToken, buildWsUrl, t }) {
  const showTerminal = ref(false)
  const terminalConnected = ref(false)
  const terminalMode = ref('normal') // 'normal' | 'minimized' | 'maximized'
  let termInstance = null
  let termFitAddon = null
  let termWs = null
  let termResizeObserver = null
  let termPopoutWindow = null
  let termContainer = null  // direct DOM reference

  // ─── helpers ───

  function safeFit() {
    try { if (termFitAddon && termInstance) termFitAddon.fit() } catch (_) {}
  }

  function sendResize() {
    if (termWs && termWs.readyState === WebSocket.OPEN && termInstance) {
      termWs.send(JSON.stringify({ type: 'resize', cols: termInstance.cols, rows: termInstance.rows }))
    }
  }

  function fitAndResize() {
    safeFit()
    sendResize()
  }

  // ─── websocket ───

  function connectTerminal() {
    console.log('[Terminal] connectTerminal called, termInstance:', !!termInstance, 'authToken:', !!authToken.value)
    if (termWs) { try { termWs.close() } catch (_) {} termWs = null }
    if (!authToken.value) { console.warn('[Terminal] no authToken, aborting connect'); return }

    const wsUrl = buildWsUrl(`/api/ws/terminal?token=${encodeURIComponent(authToken.value)}`)
    console.log('[Terminal] connecting to', wsUrl)
    termWs = new WebSocket(wsUrl)

    termWs.onopen = () => {
      console.log('[Terminal] ws onopen, termInstance:', !!termInstance, 'termFitAddon:', !!termFitAddon)
      terminalConnected.value = true
      fitAndResize()
    }
    termWs.onmessage = (e) => {
      if (termInstance) termInstance.write(e.data)
    }
    termWs.onclose = (ev) => {
      console.log('[Terminal] ws onclose, code:', ev.code, 'reason:', ev.reason)
      terminalConnected.value = false
    }
    termWs.onerror = (ev) => {
      console.error('[Terminal] ws onerror', ev)
      terminalConnected.value = false
    }
  }

  // ─── xterm lifecycle ───

  function destroyTermInstance() {
    if (termResizeObserver) { termResizeObserver.disconnect(); termResizeObserver = null }
    if (termInstance) { termInstance.dispose(); termInstance = null }
    termFitAddon = null
    termContainer = null
  }

  function openTerminal() {
    const container = document.getElementById('xterm-container')
    console.log('[Terminal] openTerminal called, container:', container)
    if (!container) {
      console.warn('[Terminal] openTerminal: container #xterm-container not found! Aborting.')
      return
    }
    const rect = container.getBoundingClientRect()
    console.log('[Terminal] container rect:', rect.width, 'x', rect.height)

    // Tear down any previous instance (e.g. after close→reopen)
    destroyTermInstance()
    termContainer = container

    termInstance = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace",
      theme: {
        background: '#1e1e1e', foreground: '#d4d4d4', cursor: '#d4d4d4',
        selectionBackground: '#264f78', black: '#1e1e1e', red: '#f44747',
        green: '#6a9955', yellow: '#d7ba7d', blue: '#569cd6',
        magenta: '#c586c0', cyan: '#4ec9b0', white: '#d4d4d4',
      },
      scrollback: 5000,
      allowProposedApi: true,
    })

    termFitAddon = new FitAddon()
    termInstance.loadAddon(termFitAddon)
    termInstance.loadAddon(new WebLinksAddon())

    termInstance.open(container)
    console.log('[Terminal] xterm opened in container, cols:', termInstance.cols, 'rows:', termInstance.rows)

    termInstance.onData((data) => {
      if (termWs && termWs.readyState === WebSocket.OPEN) termWs.send(data)
    })

    termResizeObserver = new ResizeObserver(() => {
      if (showTerminal.value && terminalMode.value !== 'minimized') fitAndResize()
    })
    termResizeObserver.observe(container)

    // The ResizeObserver fires almost immediately when the container goes from
    // display:none → visible, which triggers fit(). But as extra insurance do
    // an explicit fit + connect after a rAF so the browser has flushed layout.
    requestAnimationFrame(() => {
      const rect2 = container.getBoundingClientRect()
      console.log('[Terminal] rAF: container rect:', rect2.width, 'x', rect2.height)
      safeFit()
      console.log('[Terminal] rAF: after fit, cols:', termInstance?.cols, 'rows:', termInstance?.rows)
      connectTerminal()
      if (termInstance) termInstance.focus()
    })
  }

  function refitTerminal() {
    if (!termFitAddon || !termInstance) return
    nextTick(() => requestAnimationFrame(() => {
      fitAndResize()
      if (termInstance) termInstance.focus()
    }))
  }

  function closeTerminal() {
    showTerminal.value = false
    terminalMode.value = 'normal'
    if (termWs) { try { termWs.close() } catch (_) {} termWs = null }
    destroyTermInstance()
    terminalConnected.value = false
    if (termPopoutWindow && !termPopoutWindow.closed) termPopoutWindow.close()
    termPopoutWindow = null
  }

  // ─── popout ───

  function popoutTerminal() {
    if (!authToken.value) return
    // Tear down in-page terminal
    if (termWs) { try { termWs.close() } catch (_) {} termWs = null }
    destroyTermInstance()
    terminalConnected.value = false
    showTerminal.value = false
    terminalMode.value = 'normal'

    const wsUrl = buildWsUrl(`/api/ws/terminal?token=${encodeURIComponent(authToken.value)}`)
    const w = 920, h = 620
    const left = (screen.width - w) / 2, top = (screen.height - h) / 2
    const popup = window.open('', '_blank',
      `width=${w},height=${h},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no,resizable=yes`)
    if (!popup) return
    termPopoutWindow = popup

    let xtermCss = ''
    try {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            const text = rule.cssText
            if (text.includes('xterm') || text.includes('.xterm')) {
              xtermCss += text + '\n'
            }
          }
        } catch (_) {}
      }
    } catch (_) {}

    popup.document.write(`<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>${t('terminal_title')}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;background:#1e1e1e}
#term{width:100%;height:100%}
${xtermCss}
</style>
</head><body><div id="term"></div></body></html>`)
    popup.document.close()

    const setupPopupTerminal = () => {
      try {
        if (popup.closed) return
        const container = popup.document.getElementById('term')
        if (!container) { setTimeout(setupPopupTerminal, 100); return }

        const term = new Terminal({
          cursorBlink: true, fontSize: 14,
          fontFamily: "'JetBrains Mono','Fira Code','Cascadia Code',Menlo,Monaco,'Courier New',monospace",
          theme: { background:'#1e1e1e', foreground:'#d4d4d4', cursor:'#d4d4d4',
            selectionBackground:'#264f78', black:'#1e1e1e', red:'#f44747',
            green:'#6a9955', yellow:'#d7ba7d', blue:'#569cd6',
            magenta:'#c586c0', cyan:'#4ec9b0', white:'#d4d4d4' },
          scrollback: 5000,
        })
        const fit = new FitAddon()
        term.loadAddon(fit)
        term.open(container)
        fit.fit()

        const ws = new WebSocket(wsUrl)
        ws.onopen = () => {
          fit.fit()
          ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
        }
        ws.onmessage = (e) => term.write(e.data)
        ws.onclose = () => { term.write('\r\n\x1b[31m[disconnected]\x1b[0m\r\n') }
        term.onData((data) => {
          if (ws.readyState === WebSocket.OPEN) ws.send(data)
        })
        const ro = new popup.ResizeObserver(() => {
          fit.fit()
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
          }
        })
        ro.observe(container)
        popup.addEventListener('beforeunload', () => {
          ro.disconnect(); ws.close(); term.dispose()
        })
        term.focus()
      } catch (e) {
        if (!popup.closed) setTimeout(setupPopupTerminal, 150)
      }
    }
    setTimeout(setupPopupTerminal, 200)
  }

  // ─── watchers ───

  watch(showTerminal, (val) => {
    console.log('[Terminal] watch showTerminal:', val, 'mode:', terminalMode.value)
    if (val && terminalMode.value !== 'minimized') {
      nextTick(() => {
        console.log('[Terminal] nextTick: about to openTerminal')
        openTerminal()
      })
    }
  })

  watch(terminalMode, (mode, oldMode) => {
    if (oldMode === 'minimized' && mode !== 'minimized') {
      nextTick(() => refitTerminal())
    } else if (mode === 'normal' || mode === 'maximized') {
      nextTick(() => refitTerminal())
    }
  })

  onUnmounted(() => {
    closeTerminal()
  })

  return {
    showTerminal,
    terminalConnected,
    terminalMode,
    connectTerminal,
    openTerminal,
    refitTerminal,
    closeTerminal,
    popoutTerminal,
  }
}
