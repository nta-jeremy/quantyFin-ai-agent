import { useState, useEffect, useMemo } from 'react';
import { SideRail, Topbar } from './components/SharedUI';
import { Screens } from './components/ScreenComponents';
import { buildData } from './lib/mockData';
import {
  useTweaks,
  TweaksPanel,
  TweakSection,
  TweakRadio,
  TweakToggle,
} from './components/TweaksPanel';

function App() {
  // Tweaks (returns [values, setTweak])
  const [tweaks, setTweak] = useTweaks({
    theme: 'light',
    scenario: 'volatile',
    showConfidence: true,
  });

  // Auth gate — default authed so reviewers land in the app
  const [authed, setAuthed] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem('qf_auth');
      if (v == null) {
        localStorage.setItem('qf_auth', '1');
        return true;
      }
      return v === '1';
    } catch {
      return true;
    }
  });

  const [screen, setScreen] = useState<string>('dashboard');
  const [ticker, setTicker] = useState<string>('FPT');

  // Apply theme + confidence class
  useEffect(() => {
    document.body.classList.toggle('qf-dark', tweaks.theme === 'dark');
    document.body.classList.toggle('qf-no-conf', !tweaks.showConfidence);
  }, [tweaks.theme, tweaks.showConfidence]);

  const data = useMemo(() => buildData(tweaks.scenario), [tweaks.scenario]);

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
        data={data}
        onNav={setScreen}
        onTicker={onTicker}
        scenario={tweaks.scenario}
      />
    );
  } else if (screen === 'kg') {
    body = <Screens.KG onTicker={onTicker} />;
  } else if (screen === 'stock') {
    body = <Screens.Stock data={data} ticker={ticker} onTicker={onTicker} />;
  } else if (screen === 'news') {
    body = <Screens.News data={data} onTicker={onTicker} />;
  } else if (screen === 'chat') {
    body = <Screens.Chat onTicker={onTicker} />;
  } else if (screen === 'alerts') {
    body = <Screens.Alerts data={data} onTicker={onTicker} />;
  } else if (screen === 'jobs') {
    body = <Screens.Jobs data={data} />;
  } else if (screen === 'settings') {
    body = <Screens.Settings />;
  }

  return (
    <div className="app-shell">
      <SideRail active={screen} onNav={setScreen} alertCount={data.alerts.length} />
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
