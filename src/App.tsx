import { useState } from 'react';
import { DemoShell } from './features/demo/DemoShell';
import { LiveHuddleModal } from './features/huddle/LiveHuddleModal';

export default function App() {
  const [liveSandbox, setLiveSandbox] = useState(
    () =>
      typeof window !== 'undefined' &&
      new URLSearchParams(window.location.search).get('mode') === 'live',
  );

  if (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('page') === 'raise') {
    const base = import.meta.env.BASE_URL || '/';
    window.location.replace(`${base}invest/`);
    return null;
  }

  if (liveSandbox) {
    return (
      <LiveHuddleModal
        onExitLiveMode={() => {
          if (typeof window !== 'undefined') {
            const url = new URL(window.location.href);
            url.searchParams.delete('mode');
            window.history.replaceState({}, '', url.toString());
          }
          setLiveSandbox(false);
        }}
      />
    );
  }

  return <DemoShell />;
}
