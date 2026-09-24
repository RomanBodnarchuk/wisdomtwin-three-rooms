import { useEffect, useState } from 'react';
import { DemoShell } from './features/demo/DemoShell';
import { RaisePage } from './features/raise/RaisePage';

function isRaiseRoute(): boolean {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location.search).get('page') === 'raise';
}

export default function App() {
  const [raise, setRaise] = useState(isRaiseRoute);

  useEffect(() => {
    const sync = () => setRaise(isRaiseRoute());
    window.addEventListener('popstate', sync);
    return () => window.removeEventListener('popstate', sync);
  }, []);

  if (raise) return <RaisePage />;
  return <DemoShell />;
}
