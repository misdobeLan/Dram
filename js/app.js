// DRAM ETF 监控数据（来源：Roundhill Investments 官网，As of 06/21/2026）
const holdings = [
    {
        rank: 1,
        name: 'Micron Technology Inc',
        ticker: 'MU',
        market: 'US',
        weight: 27.57,
        description: '美国最大记忆体制造商，覆盖 DRAM、NAND 与 HBM 产品线。',
        segment: 'DRAM / NAND / HBM',
        change: 0.0,
        color: '#2d7dff',
        futu_code: null
    },
    {
        rank: 2,
        name: 'SK hynix',
        ticker: '000660.KS',
        market: 'Korea',
        weight: 26.87,
        description: '全球 HBM 与 DRAM 龙头，NVIDIA AI 芯片 HBM 核心供应商。',
        segment: 'HBM / DRAM',
        change: 0.0,
        color: '#00f0ff',
        futu_code: null
    },
    {
        rank: 3,
        name: 'Samsung Electronics Co',
        ticker: '005930.KS',
        market: 'Korea',
        weight: 17.64,
        description: '全球最大记忆体厂商，积极推进 HBM4 与 NVIDIA 认证。',
        segment: 'DRAM / NAND / HBM',
        change: 0.0,
        color: '#00ff9d',
        futu_code: null
    },
    {
        rank: 4,
        name: 'Kioxia Holdings',
        ticker: '285A / KI5.SG',
        market: 'Japan / Singapore',
        weight: 8.00,
        description: 'NAND 闪存巨头，由东芝记忆体业务重组而来。',
        segment: 'NAND Flash',
        change: 0.0,
        color: '#f59e0b',
        futu_code: null
    },
    {
        rank: 5,
        name: 'Sandisk',
        ticker: 'SNDK',
        market: 'US',
        weight: 5.52,
        description: '分拆自 Western Digital，专注 NAND 与消费级存储。',
        segment: 'NAND / SSD',
        change: 0.0,
        color: '#ff4d6d',
        futu_code: null
    },
    {
        rank: 6,
        name: 'Western Digital',
        ticker: 'WDC',
        market: 'US',
        weight: 4.36,
        description: '硬盘与 NAND 存储解决方案供应商。',
        segment: 'HDD / NAND',
        change: 0.0,
        color: '#ec4899',
        futu_code: null
    },
    {
        rank: 7,
        name: 'Seagate Technology Holdings',
        ticker: 'STX',
        market: 'US / Ireland',
        weight: 4.27,
        description: '全球 HDD 龙头，积极布局 AI 数据中心海量冷存储。',
        segment: 'HDD',
        change: 0.0,
        color: '#a855f7',
        futu_code: null
    },
    {
        rank: 8,
        name: 'Nanya Technology',
        ticker: '2408.TW',
        market: 'Taiwan',
        weight: 3.27,
        description: '台湾 DRAM 制造商，专注利基型记忆体市场。',
        segment: 'DRAM',
        change: 0.0,
        color: '#14b8a6',
        futu_code: null
    },
    {
        rank: 9,
        name: 'Winbond Electronics',
        ticker: '2344.TW',
        market: 'Taiwan',
        weight: 2.08,
        description: '利基型 DRAM、NOR Flash 与行动记忆体供应商。',
        segment: 'Specialty Memory',
        change: 0.0,
        color: '#6366f1',
        futu_code: null
    },
    {
        rank: 10,
        name: 'SOUTH KOREA',
        ticker: 'KRW',
        market: 'Cash',
        weight: 0.00,
        description: '韩元现金部位。',
        segment: 'Cash',
        change: 0.0,
        color: '#8b9ab0',
        futu_code: null,
        is_cash: true
    },
    {
        rank: 11,
        name: 'NEW TAIWAN',
        ticker: 'TWD',
        market: 'Cash',
        weight: 0.00,
        description: '新台币现金部位。',
        segment: 'Cash',
        change: 0.0,
        color: '#8b9ab0',
        futu_code: null,
        is_cash: true
    }
];

let newsItems = [
    {
        source: 'Morningstar',
        date: '2026-05-21',
        title: '投资者蜂拥而入这只 ETF，但持仓估值已偏高',
        summary: 'DRAM 在 45 天内资产规模突破近百亿美元，但 Morningstar 分析师认为主要持仓估值已偏高，且行业具备商品周期属性。',
        url: 'https://www.morningstar.com/funds/memory-etf-has-been-hit-with-investors-they-shouldnt-forget-fundamentals',
        tickers: ['DRAM']
    },
    {
        source: 'Barron\'s',
        date: '2026-05-15',
        title: '这只记忆体芯片 ETF 涨势惊人，芯片股热潮只是部分原因',
        summary: 'DRAM 自上市以来上涨约 85%，资金流入与三大核心持仓（Micron、SK Hynix、Samsung）的强势表现共同推动。',
        url: 'https://www.barrons.com/articles/memory-chip-stock-etf-sandisk-micron-a7f40b97',
        tickers: ['DRAM', 'MU', '000660.KS', '005930.KS']
    },
    {
        source: 'AOL / Yahoo Finance',
        date: '2026-05-26',
        title: 'Micron、Sandisk 等记忆体芯片股暴涨，推动这只新 ETF 飙升',
        summary: '记忆体芯片成为 AI 供应链最紧绷环节，DRAM 成为史上增长最快的 ETF 之一，30 个交易日内资产突破百亿美元。',
        url: 'https://www.aol.com/articles/scorching-runs-memory-chip-stocks-135416000.html',
        tickers: ['DRAM', 'MU', 'SNDK']
    },
    {
        source: 'Roundhill Investments',
        date: '2026',
        title: 'Roundhill Memory ETF（DRAM）官方介绍',
        summary: '官方资料显示 DRAM 为主动管理型 ETF，通过股票与总收益互换投资全球记忆体公司，覆盖 HBM、DRAM、NAND、NOR、HDD 等。',
        url: 'https://www.roundhillinvestments.com/etf/dram/',
        tickers: ['DRAM']
    },
    {
        source: 'Quiver Quantitative / Globe Newswire',
        date: '2026-06-01',
        title: 'Micron 在 COMPUTEX 2026 展示 AI 优化记忆体与储存方案',
        summary: 'Micron 展示完整 AI 记忆体与储存产品组合，包括 HBM4 36GB、256GB SOCAMM2 与数据中心 SSD，强调记忆体带宽与容量已成为系统效能核心。',
        url: 'https://www.quiverquant.com/news/Micron+Technology+Showcases+AI-Optimized+Memory+and+Storage+Solutions+at+COMPUTEX+2026',
        tickers: ['MU']
    },
    {
        source: 'Aju Press',
        date: '2026-06-19',
        title: 'SK hynix 在 HPE Discover 2026 展示先进 AI 记忆体产品组合',
        summary: 'SK hynix 展出 HBM4、HBM3E、DDR5 服务器记忆体与 CXL 记忆体模块，强化与 HPE 在全球 AI 基础设施领域的合作。',
        url: 'https://m.ajupress.com/amp/20260619145938099',
        tickers: ['000660.KS']
    },
    {
        source: 'Digital Today',
        date: '2026-02-12',
        title: '三星电子开始 HBM4 量产出货，2026 年 HBM 销售额料将翻三倍',
        summary: '三星电子率先开始 HBM4 量产出货，采用 1c DRAM 与 4nm 基础裸片，传输速度达 11.7Gbps，预计 2026 年 HBM 销售额将增长三倍以上。',
        url: 'https://www.digitaltoday.co.kr/en/view/3806/samsung-electronics-begins-mass-production-shipments-of-hbm4-triples-hbm-sales-outlook',
        tickers: ['005930.KS']
    },
    {
        source: 'TrendForce',
        date: '2026-02-13',
        title: 'Kioxia 第三财季营收创纪录，确认 2026 年 NAND 产能售罄',
        summary: 'Kioxia 财报创纪录，并确认 2026 年 NAND 产能已售罄；AI 需求推动数据中心 SSD 销售，与 SanDisk 的合资协议也延长至 2034 年。',
        url: 'https://www.trendforce.com/news/2026/02/13/news-kioxia-posts-record-%C2%A5543-6b-q3-fy25-revenue-confirms-2026-nand-fully-booked',
        tickers: ['285A / KI5.SG', 'SNDK']
    },
    {
        source: 'AInvest',
        date: '2026-01-16',
        title: '把握 AI 驱动的记忆体与储存超级周期：SanDisk 与 Seagate',
        summary: '分析指出 SanDisk 与 Seagate 是 AI 储存超级周期的关键受惠者：SanDisk 的 BiCS8 NAND 与数据中心 SSD 获 hyperscaler 认证，Seagate 的 HAMR 硬盘则承接海量冷储存需求。',
        url: 'https://www.ainvest.com/news/capitalizing-ai-driven-memory-storage-supercycle-sandisk-seagate-2026-plays-2601',
        tickers: ['SNDK', 'STX']
    },
    {
        source: 'Futu / Zhitong Finance',
        date: '2026-01-28',
        title: 'Seagate 财报全面超预期，称 2026 年产能已售罄',
        summary: 'Seagate 财报全面超预期，并透露 2026 年近线 HDD 产能已售罄；AI 数据中心对高容量硬盘的需求持续引爆「储存超级周期」。',
        url: 'https://news.futunn.com/en/post/68002313/surging-hdd-demand-reinforces-storage-super-cycle-narrative-seagate-stxus',
        tickers: ['STX', 'WDC']
    },
    {
        source: 'Chief Group',
        date: '2026-01-14',
        title: 'AI 狂热持续，储存股升势能否持续？',
        summary: 'SanDisk、Western Digital、Seagate、Micron 等美国数据储存相关股票在 2025–2026 年初大幅领涨，AI 数据爆炸式增长带动 NAND、企业级 SSD 与硬盘需求急增。',
        url: 'https://www.chiefgroup.com.hk/en/financial/media?id=13481',
        tickers: ['SNDK', 'WDC', 'STX', 'MU']
    },
    {
        source: '01.co',
        date: '2026-04-15',
        title: '南亚科技 2026 年 Q1：利基型 DRAM 供应紧张确认，NAND 巨头入股锁定货源',
        summary: '南亚科技 Q1 2026 营收同比增长 583%，毛利率跃升至 67.9%；SanDisk、SK hynix、Kioxia 等 NAND 大厂参与私募，锁定长期 DRAM 供应。',
        url: 'https://www.01.co/research/nanya-tech-q1-2026-legacy-dram-squeeze',
        tickers: ['2408.TW', 'SNDK', '000660.KS', '285A / KI5.SG']
    },
    {
        source: 'TrendForce',
        date: '2026-02-11',
        title: '华邦电子预计 DRAM 价格到 2026 年 6 月将上涨近 4 倍，产能已预订至 2027 年',
        summary: '华邦电子预期本季 DRAM 价格暴涨 90–95%，至 2026 年中累计涨幅接近 4 倍；2027 年 DRAM 产能已提前预售，资本支出创历史新高。',
        url: 'https://www.trendforce.com/news/2026/02/11/news-winbond-expects-dram-prices-to-jump-nearly-4x-by-june-2026-capacity-booked-through-2027',
        tickers: ['2344.TW']
    },
    {
        source: 'TrendForce',
        date: '2026-05-18',
        title: '2026 年 Q1 记忆体价格飙升：三星 ASP 跳涨 146%，SK hynix DRAM 上涨逾 60%',
        summary: '三星与 SK hynix 财报揭示 2026 年 Q1 记忆体价格飙升：三星记忆体 ASP 跳涨约 146%，SK hynix DRAM ASP 上涨 60% 中段，HBM4 与 DDR5 需求强劲。',
        url: 'https://www.trendforce.com/news/2026/05/18/news-memory-supercycle-drives-1q26-price-surge-samsung-flags-146-asp-jump-sk-hynix-sees-mid-60-dram-gains',
        tickers: ['005930.KS', '000660.KS']
    },
    {
        source: 'Naver 财经 / Tokenpost',
        date: '2026-06-21',
        title: '【专栏】资金放水、AI 狂奔，只有比特币按兵不动',
        summary: 'Naver 财经要闻：SK hynix 与 Samsung 已站上 AI 战争的核心供应链；AI 加速器没有韩国记忆体就无法正常运转，利川、清州、平泽、龙仁正成为华盛顿与北京科技博弈的重要变量。',
        url: 'https://www.tokenpost.kr/news/insights/371485',
        tickers: ['005930.KS', '000660.KS']
    },
    {
        source: 'Naver 财经 / 韩国金融新闻',
        date: '2026-06-21',
        title: '金勇范：半导体繁荣果实不应流入房地产，应调整持有与转让税',
        summary: 'Naver 财经要闻：全球 AI 投资爆发推高半导体需求，Samsung 与 SK hynix 营业利润暴增；政府正考虑调整持有税与转让税，防止半导体繁荣红利过度涌入房地产。',
        url: 'http://www.fnnews.com/news/202606212114166178',
        tickers: ['005930.KS', '000660.KS']
    },
    {
        source: 'Naver 财经 / 京乡新闻',
        date: '2026-06-21',
        title: '录取线超越首尔大学自然科学系的「三电尼克斯」半导体合约学科',
        summary: 'Naver 财经要闻：保证 Samsung 与 SK hynix 就业的「半导体合约学科」录取线已超越首尔大学自然科学系；AI 记忆体产业人才争夺战白热化，折射出「三电尼克斯」（Samsung + SK hynix）的市场地位。',
        url: 'https://www.khan.co.kr/article/202606212113005',
        tickers: ['005930.KS', '000660.KS']
    }
];

// 备用模拟净值数据（当后端不可用时回退）
function generateFallbackPriceData() {
    const startDate = new Date('2026-04-02');
    const endDate = new Date('2026-06-19');
    const dates = [];
    const prices = [];
    let price = 25.0;

    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        if (d.getDay() === 0 || d.getDay() === 6) continue;
        const volatility = 0.025;
        const trend = 0.008;
        const change = (Math.random() - 0.45) * volatility + trend;
        price = Math.max(price * (1 + change), 20);
        dates.push(d.toISOString().split('T')[0]);
        prices.push(parseFloat(price.toFixed(2)));
    }

    return { dates, prices };
}

// 渲染持仓表格
function renderHoldingsTable() {
    const tbody = document.getElementById('holdings-table-body');
    tbody.innerHTML = holdings.map(h => `
        <tr class="holding-row" data-ticker="${h.ticker}">
            <td class="py-4 px-6 text-dram-muted font-mono">${h.rank}</td>
            <td class="py-4 px-4">
                <div class="holding-name">${h.name}</div>
                <div class="text-xs text-dram-muted mt-0.5">${h.segment}</div>
            </td>
            <td class="py-4 px-4">
                <span class="holding-ticker">${h.ticker}</span>
            </td>
            <td class="py-4 px-4 text-sm text-dram-muted">${h.market}</td>
            <td class="py-4 px-4 text-right">
                <div class="font-mono font-bold text-lg">${h.weight.toFixed(1)}%</div>
                <div class="w-full bg-white/10 rounded-full h-1.5 mt-1.5">
                    <div class="weight-bar" style="width: ${h.weight}%"></div>
                </div>
            </td>
            <td class="py-4 px-6 text-right">
                <div class="font-mono font-bold rt-price">—</div>
                <div class="font-mono font-bold text-sm rt-change">—</div>
            </td>
        </tr>
    `).join('');
}

// 渲染持仓卡片（排除现金部位）
function renderHoldingCards() {
    const container = document.getElementById('holding-cards');
    container.innerHTML = holdings.filter(h => !h.is_cash).map(h => `
        <div class="holding-card" data-card-ticker="${h.ticker}">
            <div class="flex items-start justify-between mb-4">
                <div>
                    <h3 class="font-display font-bold text-xl">${h.name}</h3>
                    <span class="holding-ticker text-sm">${h.ticker}</span>
                </div>
                <span class="country-badge">${h.market}</span>
            </div>
            <p class="text-dram-muted text-sm leading-relaxed mb-4">${h.description}</p>
            <div class="flex items-center justify-between pt-4 border-t border-white/10">
                <div>
                    <p class="text-xs text-dram-muted font-mono mb-1">PRICE</p>
                    <p class="font-mono font-bold text-2xl rt-card-price" style="color: ${h.color}">—</p>
                </div>
                <div class="text-right">
                    <p class="text-xs text-dram-muted font-mono mb-1">CHANGE</p>
                    <p class="font-mono font-bold rt-card-change">—</p>
                </div>
            </div>
        </div>
    `).join('');
}

// 将 ticker 映射为持仓显示名称
function getHoldingName(ticker) {
    if (ticker === 'DRAM') return 'DRAM ETF';
    const h = holdings.find(h => h.ticker === ticker);
    return h ? h.name : ticker;
}

// 从后端动态加载新闻，失败则保留静态兜底
async function loadNews() {
    try {
        const res = await fetch('/api/news');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.items && data.items.length > 0) {
            newsItems = data.items;
            renderNews();
            console.info(`News loaded: ${data.items.length} items (dynamic=${data.dynamic})`);
        }
    } catch (e) {
        console.warn('Failed to load dynamic news, using fallback:', e);
    }
}

// 轻量级前端情感分析兜底（当后端未返回 sentiment 时使用）
function computeSentimentFallback(title = '', summary = '') {
    const text = `${title} ${summary}`;
    const lower = text.toLowerCase();

    const positive = [
        '大涨','飙升','暴涨','翻倍','翻三倍','利好','强劲','超预期','创新高','历史新高',
        '突破','上升','增长','复苏','需求旺盛','供不应求','产能售罄','上调','买入','增持',
        '看好','领涨','领跑','激增','跳涨','走高','上行','上涨','受惠','受益','超级周期',
        '重估','上行空间','涨势','升势','surge','soar','jump','rally','beat','strong',
        'growth','outperform','bullish','upgrade','buy','record','booking','sold out',
        'fully booked','boom','supercycle','upside','gains','rising','surges','soars'
    ];
    const negative = [
        '大跌','暴跌','重挫','下挫','跳水','崩盘','腰斩','亏损','转亏','利空','跌破','下滑',
        '下降','衰退','疲软','低迷','恶化','风险','担忧','恐慌','抛售','卖压','减持','卖出',
        '下调','看空','看跌','唱衰','空头','熊市','跌幅','走低','下行','下跌','回落','不及预期',
        ' miss','逊于预期','裁员','停产','供过于求','库存积压','价格战','产能过剩','延迟',
        '推迟','取消','失败','plunge','crash','collapse','tumble','drop','fall','weak','miss',
        'decline','bearish','downgrade','sell','loss','losses','losing','recession','oversupply',
        'glut','downturn','slump','warning','layoffs'
    ];

    let score = 0;
    let reasons = [];
    positive.forEach(w => {
        if (lower.includes(w.toLowerCase())) { score += 0.7; reasons.push(w); }
    });
    negative.forEach(w => {
        if (lower.includes(w.toLowerCase())) { score -= 0.7; reasons.push(w); }
    });

    if (score > 0.25) return { sentiment: 'bullish', score: Math.min(1, score), reasons: reasons.slice(0,5) };
    if (score < -0.25) return { sentiment: 'bearish', score: Math.max(-1, score), reasons: reasons.slice(0,5) };
    return { sentiment: 'neutral', score: 0, reasons: [] };
}

function getSentimentBadge(item) {
    const sentiment = item.sentiment || computeSentimentFallback(item.title, item.summary);
    const labels = { bullish: '利好', bearish: '利空', neutral: '中性' };
    const colors = {
        bullish: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
        bearish: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
        neutral: 'bg-slate-500/15 text-slate-400 border-slate-500/30'
    };
    const cls = colors[sentiment.sentiment] || colors.neutral;
    const title = sentiment.reasons && sentiment.reasons.length
        ? `触发词：${sentiment.reasons.join('、')}\n得分：${sentiment.score.toFixed(2)}`
        : '情感得分：0（中性）';
    return `<span class="px-2 py-0.5 rounded text-xs font-medium border ${cls}" title="${title.replace(/"/g, '&quot;')}">${labels[sentiment.sentiment] || '中性'}</span>`;
}

// 渲染新闻（按日期倒序排列）
function renderNews() {
    const container = document.getElementById('news-grid');
    const sortedNews = [...newsItems].sort((a, b) => {
        // 没有具体月日的条目（如 '2026'）统一视为该年最早，排在最后
        const da = a.date.length >= 7 ? a.date : `${a.date}-00-00`;
        const db = b.date.length >= 7 ? b.date : `${b.date}-00-00`;
        return db.localeCompare(da);
    });
    container.innerHTML = sortedNews.map(item => {
        const tags = (item.tickers || []).map(ticker => {
            const name = getHoldingName(ticker);
            return `<span class="news-ticker" title="${name}">${ticker}</span>`;
        }).join('');
        const sentimentBadge = getSentimentBadge(item);
        return `
        <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="news-card group block">
            <div class="flex items-center justify-between mb-3">
                <span class="news-source">${item.source}</span>
                <div class="flex items-center gap-2">
                    ${sentimentBadge}
                    <span class="text-xs text-dram-muted font-mono">${item.date}</span>
                </div>
            </div>
            <h3 class="font-display font-bold text-lg mb-2 group-hover:text-dram-cyan transition-colors">${item.title}</h3>
            <p class="text-dram-muted text-sm leading-relaxed mb-3">${item.summary}</p>
            <div class="flex flex-wrap gap-2 mb-4">${tags}</div>
            <div class="flex items-center text-dram-cyan text-sm font-medium">
                阅读全文
                <svg class="w-4 h-4 ml-1 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
            </div>
        </a>
    `}).join('');
}

// 初始化持仓饼图
function initHoldingsChart() {
    const ctx = document.getElementById('holdingsChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: holdings.map(h => h.ticker),
            datasets: [{
                data: holdings.map(h => h.weight),
                backgroundColor: holdings.map(h => h.color),
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '65%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(5, 7, 10, 0.9)',
                    titleColor: '#e8eef7',
                    bodyColor: '#8b9ab0',
                    borderColor: 'rgba(0, 240, 255, 0.2)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.parsed.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}

// 价格走势图
let priceChart;
let priceData = generateFallbackPriceData();

async function loadHoldingsConfig() {
    try {
        const res = await fetch('/api/holdings');
        if (!res.ok) return;
        const data = await res.json();
        if (data.holdings) {
            data.holdings.forEach(h => {
                const local = holdings.find(lh => lh.ticker === h.ticker);
                if (local) {
                    local.futu_code = h.futu_code;
                    local.yahoo_code = h.yahoo_code;
                }
            });
        }
        if (data.etf_code || data.etf_yahoo) {
            const etfHolding = holdings.find(h => h.ticker === 'DRAM');
            if (etfHolding) {
                etfHolding.futu_code = data.etf_code;
                etfHolding.yahoo_code = data.etf_yahoo;
            } else {
                holdings.unshift({
                    rank: 0, name: 'Roundhill Memory ETF', ticker: 'DRAM',
                    market: 'US', weight: 0, description: '', segment: 'ETF',
                    change: 0, color: '#00f0ff', futu_code: data.etf_code, yahoo_code: data.etf_yahoo
                });
            }
        }
    } catch (e) {
        console.warn('Failed to load holdings config:', e);
    }
}

async function loadRealPriceData() {
    try {
        const etfCode = holdings.find(h => h.ticker === 'DRAM')?.futu_code;
        const code = etfCode || 'US.DRAM';
        const res = await fetch(`/api/kline?code=${encodeURIComponent(code)}&ktype=1d&num=300`);
        if (!res.ok) return false;
        const data = await res.json();
        if (!data.records || data.records.length === 0) return false;
        priceData = {
            dates: data.records.map(r => r.time_key.split(' ')[0]),
            prices: data.records.map(r => r.close)
        };
        return true;
    } catch (e) {
        console.warn('Failed to load real kline data:', e);
        return false;
    }
}

function initPriceChart(range = 'all') {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    let filteredDates = priceData.dates;
    let filteredPrices = priceData.prices;
    
    if (range === '1m') {
        filteredDates = priceData.dates.slice(-22);
        filteredPrices = priceData.prices.slice(-22);
    } else if (range === '2w') {
        filteredDates = priceData.dates.slice(-10);
        filteredPrices = priceData.prices.slice(-10);
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 360);
    gradient.addColorStop(0, 'rgba(0, 240, 255, 0.2)');
    gradient.addColorStop(1, 'rgba(0, 240, 255, 0)');

    if (priceChart) {
        priceChart.destroy();
    }

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: filteredDates,
            datasets: [{
                label: 'DRAM Price ($)',
                data: filteredPrices,
                borderColor: '#00f0ff',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#00f0ff',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(5, 7, 10, 0.9)',
                    titleColor: '#e8eef7',
                    bodyColor: '#00f0ff',
                    borderColor: 'rgba(0, 240, 255, 0.2)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ` $${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#8b9ab0', font: { family: 'JetBrains Mono', size: 10 }, maxTicksLimit: 6 }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#8b9ab0', font: { family: 'JetBrains Mono', size: 10 }, callback: function(value) { return '$' + value; } }
                }
            }
        }
    });
}

// 移动端菜单
function initMobileMenu() {
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    const links = menu.querySelectorAll('.mobile-nav-link');
    let isOpen = false;

    btn.addEventListener('click', () => {
        isOpen = !isOpen;
        menu.style.transform = isOpen ? 'translateX(0)' : 'translateX(100%)';
    });

    links.forEach(link => {
        link.addEventListener('click', () => {
            isOpen = false;
            menu.style.transform = 'translateX(100%)';
        });
    });
}

// 时间筛选
function initTimeFilters() {
    const buttons = document.querySelectorAll('.time-filter');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => {
                b.classList.remove('active', 'bg-dram-cyan/20', 'text-dram-cyan', 'border-dram-cyan/30');
                b.classList.add('bg-white/5', 'text-dram-muted', 'border-white/10');
            });
            btn.classList.add('active', 'bg-dram-cyan/20', 'text-dram-cyan', 'border-dram-cyan/30');
            btn.classList.remove('bg-white/5', 'text-dram-muted', 'border-white/10');
            initPriceChart(btn.dataset.range);
        });
    });
}

// 滚动动画
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('section > div, .metric-card, .holding-card, .news-card').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
}

// 暴露 holdings 给 realtime.js
window.holdings = holdings;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    renderHoldingsTable();
    renderHoldingCards();
    renderNews();

    // 尝试从后端动态加载最新资讯，失败则继续使用静态 curated 新闻
    await loadNews();

    initHoldingsChart();

    // 先获取后端解析的富途代码映射
    await loadHoldingsConfig();

    // 尝试加载真实 K 线，失败则回退到模拟数据
    await loadRealPriceData();
    initPriceChart('all');

    initMobileMenu();
    initTimeFilters();
    initScrollAnimations();

    // 启动实时行情（若后端不可用，会自动降级并显示状态）
    if (window.realtime && window.realtime.init) {
        await window.realtime.init();
    }
});
