// 实时行情接入模块
(function () {
    const API_BASE = window.location.origin;
    const WS_URL = `${API_BASE.replace(/^http/, 'ws')}/ws/quotes`;

    let socket = null;
    let reconnectTimer = null;
    let statusEl = null;

    function createStatusBadge() {
        if (statusEl) return;
        const nav = document.querySelector('nav .flex.items-center.gap-3');
        if (!nav) return;
        statusEl = document.createElement('div');
        statusEl.className = 'hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 transition-colors';
        statusEl.innerHTML = `
            <span class="w-2 h-2 rounded-full bg-dram-muted animate-pulse" id="rt-status-dot"></span>
            <span class="text-xs font-mono text-dram-muted" id="rt-status-text">行情连接中</span>
        `;
        nav.insertBefore(statusEl, nav.firstChild);
    }

    function setStatus(type, text) {
        if (!statusEl) createStatusBadge();
        const dot = document.getElementById('rt-status-dot');
        const label = document.getElementById('rt-status-text');
        if (!dot || !label) return;
        label.textContent = text;
        dot.className = `w-2 h-2 rounded-full animate-pulse ${
            type === 'connected' ? 'bg-dram-green' :
            type === 'error' ? 'bg-dram-red' :
            'bg-dram-muted'
        }`;
    }

    function formatPrice(value) {
        if (value === null || value === undefined || isNaN(value)) return '—';
        return `$${parseFloat(value).toFixed(2)}`;
    }

    function formatChangePct(value) {
        if (value === null || value === undefined || isNaN(value)) return '—';
        const sign = value >= 0 ? '+' : '';
        return `${sign}${parseFloat(value).toFixed(2)}%`;
    }

    function getChangeClass(value) {
        if (value === null || value === undefined || isNaN(value)) return 'bg-white/5 text-dram-muted';
        return value >= 0 ? 'bg-dram-green/15 text-dram-green' : 'bg-dram-red/15 text-dram-red';
    }

    function updateETFCard(quote) {
        const priceEl = document.getElementById('etf-price');
        const changeEl = document.getElementById('etf-change');
        if (!priceEl || !changeEl) return;

        // 尝试匹配 DRAM ETF（可能名字不含 DRAM）
        if (quote.code.includes('DRAM') || /US\.DRAM|HK\.DRAM/i.test(quote.code)) {
            priceEl.textContent = formatPrice(quote.price);
            changeEl.textContent = formatChangePct(quote.change_pct);
            changeEl.className = `px-2.5 py-1 rounded-lg font-mono font-bold text-sm ${getChangeClass(quote.change_pct)}`;
        }
    }

    function updateHolding(ticker, quote) {
        // 表格行
        const rows = document.querySelectorAll(`[data-ticker="${ticker}"]`);
        rows.forEach(row => {
            const priceCell = row.querySelector('.rt-price');
            const changeCell = row.querySelector('.rt-change');
            if (priceCell) priceCell.textContent = formatPrice(quote.price);
            if (changeCell) {
                changeCell.textContent = formatChangePct(quote.change_pct);
                changeCell.className = `rt-change font-mono font-bold ${quote.change_pct >= 0 ? 'text-dram-green' : 'text-dram-red'}`;
            }
        });

        // 卡片
        const cards = document.querySelectorAll(`[data-card-ticker="${ticker}"]`);
        cards.forEach(card => {
            const priceEl = card.querySelector('.rt-card-price');
            const changeEl = card.querySelector('.rt-card-change');
            if (priceEl) priceEl.textContent = formatPrice(quote.price);
            if (changeEl) {
                changeEl.textContent = formatChangePct(quote.change_pct);
                changeEl.className = `rt-card-change font-mono font-bold ${quote.change_pct >= 0 ? 'text-dram-green' : 'text-dram-red'}`;
            }
        });
    }

    function applyQuotes(quotes) {
        quotes.forEach(q => {
            // 根据富途代码或原始 ticker 反向查找持仓
            const holding = window.holdings?.find(h => {
                const futuMatch = h.futu_code && h.futu_code.toUpperCase() === q.code.toUpperCase();
                const tickerMatch = h.ticker.toUpperCase() === q.code.toUpperCase();
                return futuMatch || tickerMatch;
            });
            if (holding) {
                updateHolding(holding.ticker, q);
            }
            // ETF 兜底（富途代码或 Yahoo 代码）
            if (q.code.includes('DRAM') || q.code === 'DRAM') {
                updateETFCard(q);
            }
        });
    }

    async function fetchInitialQuotes() {
        try {
            const res = await fetch(`${API_BASE}/api/quote`);
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            const data = await res.json();
            applyQuotes(data.quotes || []);
            setStatus('connected', '行情已连接');
            return true;
        } catch (e) {
            console.warn('Initial quote fetch failed:', e);
            setStatus('error', '行情断开');
            return false;
        }
    }

    function connectWebSocket() {
        if (socket) return;
        try {
            socket = new WebSocket(WS_URL);
            socket.onopen = () => {
                setStatus('connected', '行情实时推送中');
            };
            socket.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'quotes') {
                        applyQuotes(msg.quotes || []);
                    }
                } catch (e) {
                    console.error('WebSocket message parse error:', e);
                }
            };
            socket.onerror = () => {
                setStatus('error', '行情连接错误');
            };
            socket.onclose = () => {
                socket = null;
                setStatus('error', '行情重连中');
                reconnectTimer = setTimeout(connectWebSocket, 3000);
            };
        } catch (e) {
            console.error('WebSocket init error:', e);
            setStatus('error', '行情不可用');
        }
    }

    function markUnsupportedHoldings() {
        if (!window.holdings) return;
        window.holdings.forEach(h => {
            if (h.ticker === 'DRAM') return;
            const hasSource = h.futu_code || h.yahoo_code;
            if (!hasSource) {
                // 表格
                document.querySelectorAll(`[data-ticker="${h.ticker}"] .rt-price`).forEach(el => {
                    el.textContent = '未开通';
                    el.classList.add('text-dram-muted');
                });
                document.querySelectorAll(`[data-ticker="${h.ticker}"] .rt-change`).forEach(el => {
                    el.textContent = '';
                });
                // 卡片
                document.querySelectorAll(`[data-card-ticker="${h.ticker}"] .rt-card-price`).forEach(el => {
                    el.textContent = '未开通';
                    el.classList.add('text-dram-muted');
                });
                document.querySelectorAll(`[data-card-ticker="${h.ticker}"] .rt-card-change`).forEach(el => {
                    el.textContent = '';
                });
            }
        });
    }

    async function init() {
        createStatusBadge();
        markUnsupportedHoldings();
        const ok = await fetchInitialQuotes();
        if (ok) {
            connectWebSocket();
        } else {
            setStatus('error', '行情未就绪');
        }
    }

    // 暴露全局方法供 app.js 在 K 线数据加载后调用
    window.realtime = { init, fetchInitialQuotes, applyQuotes, formatPrice, formatChangePct };
})();
