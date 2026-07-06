import { useState, useEffect, useMemo } from 'react';
import { SideRail, Topbar } from '@/components/layout';
import { Screens } from '@/components/ScreenComponents';
import { buildData } from '@/lib/mockData';
import { useAlerts, useDismissAlert } from '@/features/alerts/hooks';
import { useStocks } from '@/features/stock/hooks';
import { useNewsArticles } from '@/features/news/hooks';
import { useTweaks, TweaksPanel, TweakSection, TweakRadio, TweakToggle } from '@/components/TweaksPanel';

function App() {
  const [tweaks, setTweak] = useTweaks({
    theme: 'light',
    scenario: 'volatile',
    showConfidence: true,
  });

  const [authed, setAuthed] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem('qf_auth');
      return v === '1';
    } catch {
      return false;
    }
  });

  const [screen, setScreen] = useState<string>('dashboard');
  const [ticker, setTicker] = useState<string>('FPT');
  const [newsPage, setNewsPage] = useState<number>(1);
  const NEWS_PAGE_SIZE = 20;

  useEffect(() => {
    document.body.setAttribute('data-surface', 'app');
    document.body.classList.toggle('qf-dark', tweaks.theme === 'dark');
    document.body.classList.toggle('dark', tweaks.theme === 'dark');
    document.body.classList.toggle('qf-no-conf', !tweaks.showConfidence);
    return () => {
      document.body.removeAttribute('data-surface');
      document.body.classList.remove('qf-dark', 'dark', 'qf-no-conf');
    };
  }, [tweaks.theme, tweaks.showConfidence]);

  const data = useMemo(() => buildData(tweaks.scenario), [tweaks.scenario]);
  const alertsQuery = useAlerts({ isDismissed: false });
  const dismissAlertMutation = useDismissAlert();
  const activeAlerts = alertsQuery.data ?? [];

  const stocksQuery = useStocks();
  const backendStocks = stocksQuery.data;

  const newsQuery = useNewsArticles({ page: newsPage, limit: NEWS_PAGE_SIZE });

  function onDismissAlert(id: string) {
    dismissAlertMutation.mutate(id);
  }

  const dataWithActiveAlerts = useMemo(() => {
    return { ...data, alerts: activeAlerts, stocks: backendStocks };
  }, [data, activeAlerts, backendStocks]);

  function onTicker(t: string) {
    setTicker(t);
    setScreen('stock');
  }

  function onSignIn() {
    try {
      localStorage.setItem('qf_auth', '1');
    } catch {}
    setAuthed(true);
  }

  function onLogout() {
    try {
      localStorage.setItem('qf_auth', '0');
    } catch {}
    setAuthed(false);
  }

  if (!authed) {
    return (
      <>
        <Screens.Login onSignIn={onSignIn} />
        <QfTweaks tweaks={tweaks} setTweak={setTweak} />
      </>
    );
  }

  let body: React.ReactNode = null;
  if (screen === 'dashboard') {
    body = (
      <Screens.Dashboard
        data={dataWithActiveAlerts}
        onNav={setScreen}
        onTicker={onTicker}
        scenario={tweaks.scenario}
        onDismissAlert={onDismissAlert}
      />
    );
  } else if (screen === 'kg') {
    body = <Screens.KG onTicker={onTicker} />;
  } else if (screen === 'stock') {
    body = <Screens.Stock data={dataWithActiveAlerts} ticker={ticker} onTicker={onTicker} />;
  } else if (screen === 'news') {
    body = (
      <Screens.News
        data={dataWithActiveAlerts}
        onTicker={onTicker}
        items={newsQuery.data?.items}
        page={newsQuery.data?.page ?? newsPage}
        limit={newsQuery.data?.limit ?? NEWS_PAGE_SIZE}
        total={newsQuery.data?.total ?? 0}
        isLoading={newsQuery.isLoading}
        isError={newsQuery.isError}
        onPrevPage={() => setNewsPage((p) => Math.max(1, p - 1))}
        onNextPage={() => setNewsPage((p) => p + 1)}
      />
    );
  } else if (screen === 'chat') {
    body = <Screens.Chat data={dataWithActiveAlerts} onTicker={onTicker} />;
  } else if (screen === 'alerts') {
    body = (
      <Screens.Alerts
        data={dataWithActiveAlerts}
        onTicker={onTicker}
        onDismissAlert={onDismissAlert}
        isLoading={alertsQuery.isLoading}
        isError={alertsQuery.isError}
      />
    );
  } else if (screen === 'jobs') {
    body = <Screens.Jobs data={dataWithActiveAlerts} />;
  } else if (screen === 'crawler') {
    body = <Screens.Crawler data={dataWithActiveAlerts} />;
  } else if (screen === 'ai-health') {
    body = <Screens.AiHealth data={dataWithActiveAlerts} />;
  } else if (screen === 'settings') {
    body = <Screens.Settings />;
  }

  return (
    <div className="app-shell">
      <SideRail active={screen} onNav={setScreen} alertCount={activeAlerts.length} />
      <Topbar
        scenario={tweaks.scenario}
        onScenario={(s) => setTweak('scenario', s)}
        onSearch={() => setScreen('chat')}
        onLogout={onLogout}
        screen={screen}
      />
      <div className="app-main">{body}</div>
      <QfTweaks tweaks={tweaks} setTweak={setTweak} />
    </div>
  );
}

interface QfTweaksProps {
  tweaks: {
    theme: string;
    scenario: string;
    showConfidence: boolean;
  };
  setTweak: (key: any, val?: any) => void;
}

function QfTweaks({ tweaks, setTweak }: QfTweaksProps) {
  return (
    <TweaksPanel title="QuantyFin Tweaks">
      <TweakSection label="Giao diện" />
      <TweakRadio
        label="Theme"
        value={tweaks.theme}
        options={[
          { value: 'light', label: 'Sáng' },
          { value: 'dark', label: 'Tối' },
        ]}
        onChange={(v) => setTweak('theme', v)}
      />
      <TweakToggle
        label="AI confidence chips"
        value={tweaks.showConfidence}
        onChange={(v) => setTweak('showConfidence', v)}
      />
      <TweakSection label="Dữ liệu thị trường" />
      <TweakRadio
        label="Kịch bản"
        value={tweaks.scenario}
        options={[
          { value: 'up', label: 'Tăng' },
          { value: 'down', label: 'Giảm' },
          { value: 'volatile', label: 'Biến động' },
          { value: 'crisis', label: 'Khủng hoảng' },
        ]}
        onChange={(v) => setTweak('scenario', v)}
      />
    </TweaksPanel>
  );
}

export default App;
