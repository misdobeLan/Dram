// DRAM ETF 监控数据
const holdings = [
    {
        rank: 1,
        name: 'SK Hynix',
        ticker: '000660.KS',
        market: 'Korea',
        weight: 28.2,
        description: '全球 HBM 与 DRAM 龙头，NVIDIA AI 芯片 HBM 核心供应商。',
        segment: 'HBM / DRAM',
        change: 125.0,
        color: '#00f0ff'
    },
    {
        rank: 2,
        name: 'Micron Technology',
        ticker: 'MU',
        market: 'US',
        weight: 24.9,
        description: '美国最大记忆体制造商，覆盖 DRAM、NAND 与 HBM 产品线。',
        segment: 'DRAM / NAND / HBM',
        change: 89.5,
        color: '#2d7dff'
    },
    {
        rank: 3,
        name: 'Samsung Electronics',
        ticker: '005930.KS',
        market: 'Korea',
        weight: 20.9,
        description: '全球最大记忆体厂商，积极推进 HBM4 与 NVIDIA 认证。',
        segment: 'DRAM / NAND / HBM',
        change: 62.3,
        color: '#00ff9d'
    },
    {
        rank: 4,
        name: 'Kioxia Holdings',
        ticker: '285A / KI5.SG',
        market: 'Japan / Singapore',
        weight: 6.5,
        description: 'NAND 闪存巨头，由东芝记忆体业务重组而来。',
        segment: 'NAND Flash',
        change: 48.7,
        color: '#f59e0b'
    },
    {
        rank: 5,
        name: 'SanDisk',
        ticker: 'SNDK',
        market: 'US',
        weight: 5.1,
        description: '分拆自 Western Digital，专注 NAND 与消费级存储。',
        segment: 'NAND / SSD',
        change: 94.2,
        color: '#ff4d6d'
    },
    {
        rank: 6,
        name: 'Seagate Technology',
        ticker: 'STX',
        market: 'US / Ireland',
        weight: 4.4,
        description: '全球 HDD 龙头，积极布局 AI 数据中心海量冷存储。',
        segment: 'HDD',
        change: 31.4,
        color: '#a855f7'
    },
    {
        rank: 7,
        name: 'Western Digital',
        ticker: 'WDC',
        market: 'US',
        weight: 4.0,
        description: '硬盘与 NAND 存储解决方案供应商。',
        segment: 'HDD / NAND',
        change: 26.8,
        color: '#ec4899'
    },
    {
        rank: 8,
        name: 'Nanya Technology',
        ticker: '2408.TW',
        market: 'Taiwan',
        weight: 3.3,
        description: '台湾 DRAM 制造商，专注利基型记忆体市场。',
        segment: 'DRAM',
        change: 18.5,
        color: '#14b8a6'
    },
    {
        rank: 9,
        name: 'Winbond Electronics',
        ticker: '2344.TW',
        market: 'Taiwan',
        weight: 2.1,
        description: '利基型 DRAM、NOR Flash 与行动记忆体供应商。',
        segment: 'Specialty Memory',
        change: 22.1,
        color: '#6366f1'
    }
];

const newsItems = [
    {
        source: 'Morningstar',
        date: '2026-05-21',
        title: 'Investors Are Flocking to This ETF, but Its Holdings Look Overvalued',
        summary: 'DRAM 在 45 天内资产规模突破近百亿美元，但 Morningstar 分析师认为主要持仓估值已偏高，且行业具备商品周期属性。',
        url: 'https://www.morningstar.com/funds/memory-etf-has-been-hit-with-investors-they-shouldnt-forget-fundamentals'
    },
    {
        source: 'Barron\'s',
        date: '2026-05-15',
        title: 'This Memory Chip ETF Is Off the Charts. The Chip Stock Boom Is Only Part of It.',
        summary: 'DRAM 自上市以来上涨约 85%，资金流入与三大核心持仓（Micron、SK Hynix、Samsung）的强势表现共同推动。',
        url: 'https://www.barrons.com/articles/memory-chip-stock-etf-sandisk-micron-a7f40b97'
    },
    {
        source: 'AOL / Yahoo Finance',
        date: '2026-05-26',
        title: 'Scorching runs for memory chip stocks like Micron and Sandisk have sent this new ETF soaring',
        summary: '记忆体芯片成为 AI 供应链最紧绷环节，DRAM 成为史上增长最快的 ETF 之一，30 个交易日内资产突破百亿美元。',
        url: 'https://www.aol.com/articles/scorching-runs-memory-chip-stocks-135416000.html'
    },
    {
        source: 'Roundhill Investments',
        date: '2026',
        title: 'Roundhill Memory ETF (DRAM) 官方介绍',
        summary: '官方资料显示 DRAM 为主动管理型 ETF，通过股票与总收益互换投资全球记忆体公司，包括 HBM、DRAM、NAND、NOR、HDD 等。',
        url: 'https://www.roundhillinvestments.com/etf/dram/'
    }
];

// 模拟价格数据：2026-04-02 至 2026-06-19
function generatePriceData() {
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
        <tr class="holding-row">
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
                <span class="font-mono font-bold text-dram-green">+${h.change.toFixed(1)}%</span>
            </td>
        </tr>
    `).join('');
}

// 渲染持仓卡片
function renderHoldingCards() {
    const container = document.getElementById('holding-cards');
    container.innerHTML = holdings.map(h => `
        <div class="holding-card">
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
                    <p class="text-xs text-dram-muted font-mono mb-1">WEIGHT</p>
                    <p class="font-mono font-bold text-2xl" style="color: ${h.color}">${h.weight.toFixed(1)}%</p>
                </div>
                <div class="text-right">
                    <p class="text-xs text-dram-muted font-mono mb-1">RETURN</p>
                    <p class="font-mono font-bold text-dram-green">+${h.change.toFixed(1)}%</p>
                </div>
            </div>
        </div>
    `).join('');
}

// 渲染新闻
function renderNews() {
    const container = document.getElementById('news-grid');
    container.innerHTML = newsItems.map(item => `
        <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="news-card group block">
            <div class="flex items-center justify-between mb-3">
                <span class="news-source">${item.source}</span>
                <span class="text-xs text-dram-muted font-mono">${item.date}</span>
            </div>
            <h3 class="font-display font-bold text-lg mb-2 group-hover:text-dram-cyan transition-colors">${item.title}</h3>
            <p class="text-dram-muted text-sm leading-relaxed">${item.summary}</p>
            <div class="mt-4 flex items-center text-dram-cyan text-sm font-medium">
                阅读全文
                <svg class="w-4 h-4 ml-1 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
            </div>
        </a>
    `).join('');
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
                legend: {
                    display: false
                },
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
const priceData = generatePriceData();

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
            interaction: {
                intersect: false,
                mode: 'index'
            },
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
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#8b9ab0',
                        font: { family: 'JetBrains Mono', size: 10 },
                        maxTicksLimit: 6
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#8b9ab0',
                        font: { family: 'JetBrains Mono', size: 10 },
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

// 模拟实时价格
function simulateLivePrice() {
    const priceEl = document.getElementById('etf-price');
    const changeEl = document.getElementById('etf-change');
    let basePrice = 47.85;
    let baseChange = 3.24;

    setInterval(() => {
        const move = (Math.random() - 0.5) * 0.15;
        basePrice = Math.max(basePrice + move, 40);
        baseChange += move * 0.1;
        
        priceEl.textContent = `$${basePrice.toFixed(2)}`;
        changeEl.textContent = `${baseChange >= 0 ? '+' : ''}${baseChange.toFixed(2)}%`;
        changeEl.className = `px-2.5 py-1 rounded-lg font-mono font-bold text-sm ${baseChange >= 0 ? 'bg-dram-green/15 text-dram-green' : 'bg-dram-red/15 text-dram-red'}`;
    }, 3500);
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

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    renderHoldingsTable();
    renderHoldingCards();
    renderNews();
    initHoldingsChart();
    initPriceChart('all');
    simulateLivePrice();
    initMobileMenu();
    initTimeFilters();
    initScrollAnimations();
});
