export interface Stock {
  ticker: string;
  name: string;
  sector: string;
  exchange: string;
  price: number;
  change: number;
  changePct: number;
  fiveDay: number;
  volume: number;
  series: number[];
  sentiment: 'pos' | 'neg' | 'neu';
  sentScore: number;
  newsCount24h: number;
  confidence: 'high' | 'med' | 'low';
  confidencePct: number;
}

export interface IndexData {
  name: string;
  value: number;
  change: number;
  changePct: number;
  series: number[];
}

export interface Macro {
  id: string;
  title: string;
  impact: 'pos' | 'neg' | 'neu';
  sector: string;
}

export interface NewsItemData {
  id: string;
  title: string;
  src: string;
  url: string;
  tickers: string[];
  tone: 'pos' | 'neg' | 'neu';
  sentScore: number;
  minutesAgo: number;
  conf: 'high' | 'med' | 'low';
  confPct: number;
  filterStatus: 'filtered' | 'pending' | 'analyzed';
  sector: string;
}

export interface Alert {
  id: string;
  sev: 'high' | 'med' | 'info';
  t: string;
  m: string;
  tickers?: string[];
  when: string;
}

export interface Job {
  id: string;
  src: string;
  url: string;
  status: 'done' | 'running' | 'retry' | 'failed';
  total: number;
  filteredOut: number;
  analyzed: number;
  durationMs: number;
  traceId: string;
  lastRun: string;
  tier: string;
}

export interface LLMModel {
  name: string;
  vendor: string;
  role: string;
  tokens24h: number;
  cost24h: number;
  share: number;
}

export interface KGNode {
  id: string;
  type: 'Event' | 'Sector' | 'Stock' | 'Leader' | 'Macro' | 'Company';
  label: string;
  short?: string;
  size?: number;
}

export interface KGEdge {
  s: string;
  t: string;
  kind: string;
  w: number;
}

export const STOCKS: Omit<Stock, 'price' | 'change' | 'changePct' | 'fiveDay' | 'volume' | 'series' | 'sentiment' | 'sentScore' | 'newsCount24h' | 'confidence' | 'confidencePct'>[] = [
  // Ngân hàng
  { ticker: 'VCB',  name: 'Ngân hàng TMCP Ngoại thương VN', sector: 'Ngân hàng', exchange: 'HSX' },
  { ticker: 'TCB',  name: 'Ngân hàng Techcombank',           sector: 'Ngân hàng', exchange: 'HSX' },
  { ticker: 'MBB',  name: 'Ngân hàng Quân đội',              sector: 'Ngân hàng', exchange: 'HSX' },
  { ticker: 'CTG',  name: 'Vietinbank',                      sector: 'Ngân hàng', exchange: 'HSX' },
  { ticker: 'BID',  name: 'BIDV',                            sector: 'Ngân hàng', exchange: 'HSX' },

  // Bất động sản
  { ticker: 'VHM',  name: 'Vinhomes',                        sector: 'Bất động sản', exchange: 'HSX' },
  { ticker: 'VIC',  name: 'Vingroup',                        sector: 'Bất động sản', exchange: 'HSX' },
  { ticker: 'NVL',  name: 'Novaland',                        sector: 'Bất động sản', exchange: 'HSX' },
  { ticker: 'DXG',  name: 'Đất Xanh',                        sector: 'Bất động sản', exchange: 'HSX' },
  { ticker: 'KDH',  name: 'Khang Điền',                      sector: 'Bất động sản', exchange: 'HSX' },

  // Thép
  { ticker: 'HPG',  name: 'Tập đoàn Hòa Phát',               sector: 'Thép',          exchange: 'HSX' },
  { ticker: 'HSG',  name: 'Hoa Sen',                         sector: 'Thép',          exchange: 'HSX' },
  { ticker: 'NKG',  name: 'Nam Kim',                         sector: 'Thép',          exchange: 'HSX' },

  // Bán lẻ / FMCG
  { ticker: 'MWG',  name: 'Thế Giới Di Động',                sector: 'Bán lẻ',        exchange: 'HSX' },
  { ticker: 'MSN',  name: 'Masan Group',                     sector: 'FMCG',          exchange: 'HSX' },
  { ticker: 'VNM',  name: 'Vinamilk',                        sector: 'FMCG',          exchange: 'HSX' },
  { ticker: 'PNJ',  name: 'Phú Nhuận Jewelry',               sector: 'Bán lẻ',        exchange: 'HSX' },
  { ticker: 'FRT',  name: 'FPT Retail',                      sector: 'Bán lẻ',        exchange: 'HSX' },

  // Công nghệ / Viễn thông
  { ticker: 'FPT',  name: 'FPT Corp',                        sector: 'Công nghệ',     exchange: 'HSX' },
  { ticker: 'CMG',  name: 'CMC Corp',                        sector: 'Công nghệ',     exchange: 'HSX' },
  { ticker: 'VGI',  name: 'Viettel Global',                  sector: 'Viễn thông',    exchange: 'UPCoM' },

  // Năng lượng / Dầu khí
  { ticker: 'GAS',  name: 'PV Gas',                          sector: 'Dầu khí',       exchange: 'HSX' },
  { ticker: 'PLX',  name: 'Petrolimex',                      sector: 'Dầu khí',       exchange: 'HSX' },
  { ticker: 'POW',  name: 'PV Power',                        sector: 'Năng lượng',    exchange: 'HSX' },
  { ticker: 'BSR',  name: 'Lọc hóa dầu Bình Sơn',            sector: 'Dầu khí',       exchange: 'UPCoM' },

  // Chứng khoán
  { ticker: 'SSI',  name: 'Chứng khoán SSI',                 sector: 'Chứng khoán',   exchange: 'HSX' },
  { ticker: 'VND',  name: 'VNDIRECT',                        sector: 'Chứng khoán',   exchange: 'HSX' },
  { ticker: 'HCM',  name: 'Chứng khoán TP.HCM',              sector: 'Chứng khoán',   exchange: 'HSX' },

  // Hàng không / Vận tải
  { ticker: 'HVN',  name: 'Vietnam Airlines',                sector: 'Hàng không',    exchange: 'HSX' },
  { ticker: 'ACV',  name: 'Cảng hàng không VN',              sector: 'Hàng không',    exchange: 'UPCoM' },
];

export const BASE_PRICE: Record<string, number> = {
  VCB: 92.4, TCB: 28.6, MBB: 26.5, CTG: 41.2, BID: 51.8,
  VHM: 44.0, VIC: 41.5, NVL: 13.2, DXG: 17.8, KDH: 32.4,
  HPG: 28.9, HSG: 22.1, NKG: 19.6,
  MWG: 65.2, MSN: 72.5, VNM: 68.4, PNJ: 96.7, FRT: 184.5,
  FPT: 138.2, CMG: 56.8, VGI: 89.4,
  GAS: 78.6, PLX: 41.5, POW: 13.4, BSR: 21.8,
  SSI: 32.8, VND: 19.6, HCM: 28.4,
  HVN: 19.8, ACV: 109.2,
};

function seedRand(seed: number) {
  let s = seed;
  return function () {
    s = (s * 1664525 + 1013904223) | 0;
    return ((s >>> 0) % 100000) / 100000;
  };
}

function generateSpark(ticker: string, scenario: string, n = 32) {
  const rand = seedRand(ticker.charCodeAt(0) * 137 + ticker.charCodeAt(1) * 19 + (scenario.charCodeAt(0) || 0));
  const base = BASE_PRICE[ticker] || 30;
  let drift: number;
  let vol: number;
  switch (scenario) {
    case 'down':     drift = -0.0024; vol = 0.012; break;
    case 'volatile': drift = 0.0002;  vol = 0.028; break;
    case 'crisis':   drift = -0.006;  vol = 0.035; break;
    case 'up':
    default:         drift = 0.003;   vol = 0.011;
  }
  const out: number[] = [];
  let v = base * (1 - drift * n * 0.5);
  for (let i = 0; i < n; i++) {
    v = v * (1 + drift + (rand() - 0.5) * vol);
    out.push(v);
  }
  return out;
}

function pctChange(arr: number[]) {
  return ((arr[arr.length - 1] - arr[0]) / arr[0]) * 100;
}

function buildStocks(scenario: string): Stock[] {
  return STOCKS.map((s) => {
    const series = generateSpark(s.ticker, scenario);
    const price = series[series.length - 1];
    const open = series[series.length - 2] || price;
    const change = price - open;
    const changePct = (change / open) * 100;
    // 5-day change
    const fiveDay = pctChange(series.slice(-5));
    // sentiment per ticker shifts with scenario
    let sentiment: 'pos' | 'neg' | 'neu';
    const r = seedRand(s.ticker.charCodeAt(0) * 53)();
    if (scenario === 'up')        sentiment = r > 0.25 ? 'pos' : (r > 0.05 ? 'neu' : 'neg');
    else if (scenario === 'down') sentiment = r > 0.7  ? 'pos' : (r > 0.4  ? 'neu' : 'neg');
    else if (scenario === 'crisis') sentiment = r > 0.85 ? 'pos' : (r > 0.55 ? 'neu' : 'neg');
    else                          sentiment = r > 0.6  ? 'pos' : (r > 0.3  ? 'neu' : 'neg');

    const sentScore = sentiment === 'pos' ? 0.4 + r * 0.55 : sentiment === 'neg' ? -(0.4 + r * 0.55) : (r - 0.5) * 0.5;
    return {
      ...s,
      price: +price.toFixed(2),
      change: +change.toFixed(2),
      changePct: +changePct.toFixed(2),
      fiveDay: +fiveDay.toFixed(2),
      volume: Math.round((seedRand(s.ticker.charCodeAt(0) * 191)() * 18 + 1) * 1e6),
      series,
      sentiment,
      sentScore: +sentScore.toFixed(2),
      newsCount24h: Math.round(seedRand(s.ticker.charCodeAt(1) * 211)() * 24 + 1),
      confidence: (['high', 'med', 'low'] as const)[Math.floor(r * 3) % 3],
      confidencePct: Math.round(60 + r * 38),
    };
  });
}

function buildIndices(scenario: string): IndexData[] {
  function ix(name: string, baseVal: number, seed: string) {
    const series = generateSpark(name + seed, scenario, 64);
    const factor = baseVal / series[0];
    const scaled = series.map(v => v * factor);
    const last = scaled[scaled.length - 1];
    const prev = scaled[scaled.length - 8];
    const change = last - prev;
    const pct = (change / prev) * 100;
    return { name, value: +last.toFixed(2), change: +change.toFixed(2), changePct: +pct.toFixed(2), series: scaled };
  }
  return [
    ix('VN-Index', 1287.4, 'VNI'),
    ix('VN30',     1342.6, 'VN30'),
    ix('HNX-Index', 234.8, 'HNX'),
    ix('UPCoM',     91.3,  'UP'),
  ];
}

const MACRO_BANK_UP: Macro[] = [
  { id: 'm1', title: 'NHNN giữ nguyên lãi suất điều hành 4.5%, định hướng nới lỏng có kiểm soát', impact: 'pos', sector: 'Ngân hàng' },
  { id: 'm2', title: 'FED phát tín hiệu cắt giảm lãi suất 25bp trong tháng 6/2026', impact: 'pos', sector: 'Vĩ mô' },
  { id: 'm3', title: 'PMI sản xuất Việt Nam tháng 5 đạt 53.2 — tháng thứ 7 trên ngưỡng mở rộng', impact: 'pos', sector: 'Sản xuất' },
  { id: 'm4', title: 'Khối ngoại mua ròng phiên thứ 8 liên tiếp, tổng giá trị 4.2 nghìn tỷ đồng', impact: 'pos', sector: 'Dòng tiền' },
];

const MACRO_BANK_DOWN: Macro[] = [
  { id: 'm5', title: 'CPI tháng 5 tăng 4.6% so với cùng kỳ, vượt mục tiêu kiểm soát của Chính phủ', impact: 'neg', sector: 'Vĩ mô' },
  { id: 'm6', title: 'NHNN bán ra 1.8 tỷ USD dự trữ ngoại hối để ổn định tỷ giá', impact: 'neg', sector: 'Vĩ mô' },
  { id: 'm7', title: 'Khối ngoại bán ròng tháng thứ 4 liên tiếp, áp lực rút vốn ETF',          impact: 'neg', sector: 'Dòng tiền' },
  { id: 'm8', title: 'Lợi suất trái phiếu Chính phủ 10 năm vượt 4.2%, mức cao nhất 14 tháng',  impact: 'neg', sector: 'Vĩ mô' },
];

const MACRO_BANK_CRISIS: Macro[] = [
  { id: 'm9',  title: 'Chứng khoán toàn cầu lao dốc sau dữ liệu việc làm Mỹ kém, S&P 500 giảm 3.8%', impact: 'neg', sector: 'Vĩ mô' },
  { id: 'm10', title: 'NHNN khẩn cấp họp về biện pháp giữ ổn định thanh khoản hệ thống ngân hàng',    impact: 'neg', sector: 'Ngân hàng' },
  { id: 'm11', title: 'Giá vàng SJC tăng 4.2 triệu/lượng trong phiên, sát mốc 110 triệu',             impact: 'neu', sector: 'Vĩ mô' },
  { id: 'm12', title: 'UBCKNN cảnh báo 12 mã chứng khoán có dấu hiệu thao túng giá',                   impact: 'neg', sector: 'Pháp lý' },
];

function buildMacros(scenario: string): Macro[] {
  if (scenario === 'up')       return MACRO_BANK_UP.concat(MACRO_BANK_DOWN.slice(0, 1));
  if (scenario === 'down')     return MACRO_BANK_DOWN.concat(MACRO_BANK_UP.slice(0, 1));
  if (scenario === 'crisis')   return MACRO_BANK_CRISIS.concat(MACRO_BANK_DOWN.slice(0, 2));
  return MACRO_BANK_UP.slice(0, 2).concat(MACRO_BANK_DOWN.slice(0, 2));
}

const NEWS_TEMPLATES = [
  { tone: 'pos' as const, src: 'CafeF',       fmt: (t: any) => `${t.ticker} báo lãi quý I/2026 tăng ${randPct(15,42)}%, vượt kế hoạch năm`, },
  { tone: 'pos' as const, src: 'Vietstock',   fmt: (t: any) => `${t.ticker}: HĐQT thông qua chia cổ tức tiền mặt ${randPct(10,25)}%, lịch chốt 28/06`, },
  { tone: 'pos' as const, src: 'NDH',         fmt: (t: any) => `Khối ngoại mua ròng ${randPct(80,420)} tỷ đồng cổ phiếu ${t.ticker} trong tuần`, },
  { tone: 'pos' as const, src: 'VnEconomy',   fmt: (t: any) => `${t.ticker} ký thỏa thuận hợp tác chiến lược với đối tác Hàn Quốc, dự kiến doanh thu tăng ${randPct(8,18)}%`, },
  { tone: 'pos' as const, src: 'ĐTCK',        fmt: (t: any) => `Báo cáo SSI: nâng khuyến nghị ${t.ticker} lên MUA, giá mục tiêu ${randInt(20,200)} đồng`, },
  { tone: 'neg' as const, src: 'CafeF',       fmt: (t: any) => `${t.ticker} báo lỗ quý I/2026, biên lợi nhuận gộp giảm ${randPct(3,9)} điểm phần trăm`, },
  { tone: 'neg' as const, src: 'Vietstock',   fmt: (t: any) => `${t.ticker}: cổ đông lớn đăng ký bán ${randPct(2,8)}% vốn, cổ phiếu chịu áp lực`, },
  { tone: 'neg' as const, src: 'Tuổi Trẻ',    fmt: (t: any) => `Khối ngoại bán ròng ${randPct(120,580)} tỷ đồng cổ phiếu ${t.ticker} trong tuần`, },
  { tone: 'neg' as const, src: 'NDH',         fmt: (t: any) => `${t.ticker} bị UBCKNN xử phạt ${randPct(60,400)} triệu vì công bố thông tin không đầy đủ`, },
  { tone: 'neu' as const, src: 'Vietstock',   fmt: (t: any) => `${t.ticker} công bố tài liệu ĐHCĐ thường niên 2026, kế hoạch lợi nhuận đi ngang`, },
  { tone: 'neu' as const, src: 'CafeF',       fmt: (t: any) => `${t.ticker}: thay đổi nhân sự cấp cao, bổ nhiệm Phó Tổng Giám đốc mới`, },
  { tone: 'neu' as const, src: 'VnBusiness',  fmt: (t: any) => `${t.ticker} hoàn tất phát hành ${randPct(200,800)} tỷ trái phiếu doanh nghiệp, kỳ hạn 3 năm`, },
];

function randPct(a: number, b: number) { return Math.round(a + Math.random() * (b - a)); }
function randInt(a: number, b: number) { return Math.round((a + Math.random() * (b - a)) * 1000); }

function buildNews(scenario: string, stocks: Stock[]): NewsItemData[] {
  const rand = seedRand((scenario.charCodeAt(0) || 0) * 13 + 41);
  let toneBias: ('pos' | 'neg' | 'neu')[];
  if (scenario === 'up')       toneBias = ['pos','pos','pos','neu','pos','neg','pos','neu','pos','pos','pos','neu'];
  else if (scenario === 'down')toneBias = ['neg','neg','neu','neg','pos','neg','neu','neg','pos','neg','neu','neg'];
  else if (scenario === 'crisis') toneBias = ['neg','neg','neg','neg','neg','neu','neg','neg','neg','neg','neu','neg'];
  else                        toneBias = ['neu','pos','neg','neu','pos','neg','pos','neu','neg','pos','neu','neg'];

  const items: NewsItemData[] = [];
  for (let i = 0; i < 32; i++) {
    const tone = toneBias[i % toneBias.length];
    const candidates = NEWS_TEMPLATES.filter(t => t.tone === tone);
    const tpl = candidates[Math.floor(rand() * candidates.length)];
    const stock = stocks[Math.floor(rand() * stocks.length)];
    const sentScore = tone === 'pos' ? +(0.5 + rand() * 0.45).toFixed(2)
                    : tone === 'neg' ? +(-(0.5 + rand() * 0.45)).toFixed(2)
                    :                  +((rand() - 0.5) * 0.5).toFixed(2);
    const minutesAgo = Math.floor(2 + i * (6 + rand() * 10));
    const confChoices = ['high','high','med','med','low'] as const;
    const conf = confChoices[Math.floor(rand() * confChoices.length)];
    const confPct = conf === 'high' ? 85 + Math.round(rand() * 13) : conf === 'med' ? 65 + Math.round(rand() * 18) : 40 + Math.round(rand() * 20);
    const filterStatus = i % 11 === 5 ? 'filtered' as const : (i % 17 === 3 ? 'pending' as const : 'analyzed' as const);
    items.push({
      id: 'n' + i,
      title: tpl.fmt(stock),
      src: tpl.src,
      url: '#',
      tickers: [stock.ticker].concat(rand() > 0.7 ? [stocks[Math.floor(rand() * stocks.length)].ticker] : []),
      tone,
      sentScore,
      minutesAgo,
      conf, confPct,
      filterStatus,
      sector: stock.sector,
    });
  }
  items.sort((a, b) => a.minutesAgo - b.minutesAgo);
  return items;
}

function buildAlerts(scenario: string, _news: NewsItemData[], _stocks: Stock[]): Alert[] {
  const alerts: Alert[] = [];
  if (scenario === 'crisis') {
    alerts.push({ id: 'a1', sev: 'high', t: 'Chuỗi rủi ro lây lan phát hiện: dòng tiền rút khỏi ngân hàng → bất động sản → chứng khoán', m: 'KG path · 3 hops · 12 mã liên đới', tickers: ['VCB','TCB','VHM','SSI'], when: '2 phút trước' });
    alerts.push({ id: 'a2', sev: 'high', t: 'Khối ngoại bán ròng tăng đột biến, tổng giá trị vượt 1.4 nghìn tỷ trong 60 phút',         m: 'Trigger · volume > μ + 2.5σ',     tickers: ['VHM','HPG','MSN'],   when: '14 phút trước' });
    alerts.push({ id: 'a3', sev: 'med',  t: 'Sentiment ngành Ngân hàng giảm mạnh: 18 tin tiêu cực / 24 giờ',                            m: 'Sentiment delta · −0.62',          tickers: ['VCB','TCB','MBB','BID'], when: '38 phút trước' });
  } else if (scenario === 'down') {
    alerts.push({ id: 'a1', sev: 'med',  t: 'Khối ngoại bán ròng ngành Thép phiên thứ 4 liên tiếp',                                     m: 'Sector flow · −890 tỷ tổng',       tickers: ['HPG','HSG','NKG'],   when: '12 phút trước' });
    alerts.push({ id: 'a2', sev: 'med',  t: 'NVL giảm sàn 6.9%, khối lượng gấp 3.2× trung bình 20 phiên',                              m: 'Anomaly · price + volume',         tickers: ['NVL'],               when: '40 phút trước' });
    alerts.push({ id: 'a3', sev: 'info', t: 'Sentiment vĩ mô chuyển sang tiêu cực — CPI tháng 5 vượt mục tiêu',                         m: 'Macro impact · 23 mã ảnh hưởng',   tickers: ['VHM','VIC','MWG'],   when: '1 giờ trước' });
  } else if (scenario === 'up') {
    alerts.push({ id: 'a1', sev: 'info', t: 'Dòng tiền lan tỏa: 6/9 ngành tăng đồng pha trong phiên',                                   m: 'Sector rotation healthy',          tickers: ['VCB','FPT','MWG'],   when: '8 phút trước' });
    alerts.push({ id: 'a2', sev: 'info', t: 'FPT vượt đỉnh lịch sử, sentiment tích cực 14 tin / 24 giờ',                                m: 'Breakout · 138.2 đ',                tickers: ['FPT'],               when: '24 phút trước' });
  } else {
    alerts.push({ id: 'a1', sev: 'med',  t: 'Phân hóa mạnh giữa ngành Ngân hàng và Bất động sản',                                       m: 'Sector dispersion · σ = 2.4%',      tickers: ['VCB','VHM'],          when: '18 phút trước' });
    alerts.push({ id: 'a2', sev: 'info', t: 'Sentiment trung tính, độ phân tán cao — chờ tín hiệu xác nhận',                            m: 'Confidence · MEDIUM',               tickers: [],                     when: '45 phút trước' });
  }
  return alerts;
}

export const WATCHLIST = ['VCB','FPT','HPG','MWG','VNM','VHM','SSI','VIC'];

export const KG_NODES: KGNode[] = [
  // macro events
  { id: 'fed-cut',   type: 'Event',  label: 'FED cắt lãi suất',           short: 'FED',  size: 22 },
  { id: 'cpi-up',    type: 'Event',  label: 'CPI tháng 5 vượt mục tiêu',  short: 'CPI',  size: 18 },
  { id: 'sbv-rate',  type: 'Event',  label: 'NHNN giữ nguyên lãi suất',   short: 'SBV',  size: 18 },
  { id: 'fx-pressure', type: 'Event', label: 'Áp lực tỷ giá USD/VND',     short: 'FX',   size: 16 },
  { id: 'foreign-sell', type: 'Event', label: 'Khối ngoại bán ròng',     short: '$out', size: 18 },

  // sectors
  { id: 'bank',     type: 'Sector', label: 'Ngân hàng',     size: 24 },
  { id: 're',       type: 'Sector', label: 'Bất động sản',  size: 22 },
  { id: 'steel',    type: 'Sector', label: 'Thép',          size: 20 },
  { id: 'retail',   type: 'Sector', label: 'Bán lẻ',        size: 20 },
  { id: 'tech',     type: 'Sector', label: 'Công nghệ',     size: 18 },
  { id: 'oil',      type: 'Sector', label: 'Dầu khí',       size: 18 },
  { id: 'brokerage',type: 'Sector', label: 'Chứng khoán',   size: 18 },

  // stocks (tickers)
  { id: 'VCB', type: 'Stock', label: 'VCB', size: 18 },
  { id: 'TCB', type: 'Stock', label: 'TCB', size: 16 },
  { id: 'MBB', type: 'Stock', label: 'MBB', size: 14 },
  { id: 'BID', type: 'Stock', label: 'BID', size: 16 },
  { id: 'VHM', type: 'Stock', label: 'VHM', size: 18 },
  { id: 'VIC', type: 'Stock', label: 'VIC', size: 16 },
  { id: 'NVL', type: 'Stock', label: 'NVL', size: 14 },
  { id: 'HPG', type: 'Stock', label: 'HPG', size: 18 },
  { id: 'HSG', type: 'Stock', label: 'HSG', size: 14 },
  { id: 'MWG', type: 'Stock', label: 'MWG', size: 16 },
  { id: 'PNJ', type: 'Stock', label: 'PNJ', size: 14 },
  { id: 'FPT', type: 'Stock', label: 'FPT', size: 18 },
  { id: 'GAS', type: 'Stock', label: 'GAS', size: 14 },
  { id: 'SSI', type: 'Stock', label: 'SSI', size: 14 },

  // leaders
  { id: 'leader-pnq', type: 'Leader', label: 'Phạm Nhật Vượng', size: 14 },
  { id: 'leader-tnt', type: 'Leader', label: 'Trần Đình Long',  size: 14 },
];

export const KG_EDGES: KGEdge[] = [
  // FED cut → positive for everything (broad)
  { s: 'fed-cut', t: 'foreign-sell', kind: 'REDUCES', w: 0.65 },
  { s: 'fed-cut', t: 'fx-pressure',  kind: 'REDUCES', w: 0.55 },
  { s: 'fed-cut', t: 'bank',         kind: 'IMPACTS_POS', w: 0.45 },

  // CPI up → fx pressure → SBV
  { s: 'cpi-up',     t: 'fx-pressure', kind: 'AMPLIFIES', w: 0.75 },
  { s: 'fx-pressure',t: 'sbv-rate',    kind: 'PRESSURES', w: 0.55 },
  { s: 'fx-pressure',t: 'foreign-sell',kind: 'AMPLIFIES', w: 0.62 },

  // SBV → bank
  { s: 'sbv-rate', t: 'bank', kind: 'IMPACTS_POS', w: 0.7 },

  // Foreign-sell → sectors
  { s: 'foreign-sell', t: 're',        kind: 'IMPACTS_NEG', w: 0.6 },
  { s: 'foreign-sell', t: 'bank',      kind: 'IMPACTS_NEG', w: 0.5 },
  { s: 'foreign-sell', t: 'brokerage', kind: 'IMPACTS_NEG', w: 0.7 },

  // sector membership
  { s: 'VCB', t: 'bank', kind: 'BELONGS_TO', w: 1 },
  { s: 'TCB', t: 'bank', kind: 'BELONGS_TO', w: 1 },
  { s: 'MBB', t: 'bank', kind: 'BELONGS_TO', w: 1 },
  { s: 'BID', t: 'bank', kind: 'BELONGS_TO', w: 1 },

  { s: 'VHM', t: 're',   kind: 'BELONGS_TO', w: 1 },
  { s: 'VIC', t: 're',   kind: 'BELONGS_TO', w: 1 },
  { s: 'NVL', t: 're',   kind: 'BELONGS_TO', w: 1 },

  { s: 'HPG', t: 'steel', kind: 'BELONGS_TO', w: 1 },
  { s: 'HSG', t: 'steel', kind: 'BELONGS_TO', w: 1 },

  { s: 'MWG', t: 'retail', kind: 'BELONGS_TO', w: 1 },
  { s: 'PNJ', t: 'retail', kind: 'BELONGS_TO', w: 1 },

  { s: 'FPT', t: 'tech',     kind: 'BELONGS_TO', w: 1 },
  { s: 'GAS', t: 'oil',      kind: 'BELONGS_TO', w: 1 },
  { s: 'SSI', t: 'brokerage',kind: 'BELONGS_TO', w: 1 },

  // leaders
  { s: 'leader-pnq', t: 'VIC', kind: 'MANAGES', w: 1 },
  { s: 'leader-pnq', t: 'VHM', kind: 'INFLUENCES', w: 0.7 },
  { s: 'leader-tnt', t: 'HPG', kind: 'MANAGES', w: 1 },

  // cross-relations
  { s: 're', t: 'bank', kind: 'CORRELATES', w: 0.45 },
  { s: 'steel', t: 're', kind: 'SUPPLIES', w: 0.5 },
];

function buildJobs(scenario: string): Job[] {
  const sources = ['CafeF','Vietstock','VnEconomy','Tuổi Trẻ','Thanh Niên','VnBusiness','NDH','ĐTCK'];
  return sources.map((src, i) => {
    const rand = seedRand(src.charCodeAt(0) * 17 + (scenario.charCodeAt(0) || 0));
    const r = rand();
    const total = Math.floor(80 + r * 240);
    const filteredOut = Math.floor(total * (0.35 + r * 0.18));
    const analyzed = total - filteredOut - Math.floor(r * 6);
    let status: Job['status'];
    if (scenario === 'crisis' && i === 3) status = 'failed';
    else if (i === 5) status = 'running';
    else if (i === 1 && scenario !== 'up') status = 'retry';
    else status = 'done';
    return {
      id: 'j' + i,
      src,
      url: `https://${src.toLowerCase().replace(/\s+/g, '')}.vn/rss`,
      status,
      total, filteredOut, analyzed,
      durationMs: Math.floor(800 + r * 12000),
      traceId: 'trc_' + (Math.floor(r * 1e8)).toString(16).padStart(8, '0'),
      lastRun: i + ' phút trước',
      tier: i % 3 === 0 ? 'rss' : i % 3 === 1 ? 'search' : 'playwright',
    };
  });
}

export const LLM_MODELS: LLMModel[] = [
  { name: 'Haiku 3.5',  vendor: 'Anthropic', role: 'Extractor',          tokens24h: 184392, cost24h: 0.42, share: 64 },
  { name: 'GPT-4o-mini', vendor: 'OpenAI',   role: 'Sentiment',          tokens24h:  98140, cost24h: 0.18, share: 24 },
  { name: 'Sonnet 4',    vendor: 'Anthropic',role: 'Analyst (review)',   tokens24h:  12640, cost24h: 0.84, share:  9 },
  { name: 'Gemini Flash',vendor: 'Google',   role: 'Fallback',           tokens24h:   4220, cost24h: 0.02, share:  3 },
];

export interface DashboardData {
  stocks: Stock[];
  news: NewsItemData[];
  alerts: Alert[];
  indices: IndexData[];
  macros: Macro[];
  jobs: Job[];
  scenario: string;
}

export function buildData(scenario: string): DashboardData {
  const stocks = buildStocks(scenario);
  const news = buildNews(scenario, stocks);
  const alerts = buildAlerts(scenario, news, stocks);
  const indices = buildIndices(scenario);
  const macros = buildMacros(scenario);
  const jobs = buildJobs(scenario);
  return { stocks, news, alerts, indices, macros, jobs, scenario };
}
