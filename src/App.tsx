import { DemoShell } from './features/demo/DemoShell';

export default function App() {
  if (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('page') === 'raise') {
    const base = import.meta.env.BASE_URL || '/';
    window.location.replace(`${base}invest/`);
    return null;
  }

  return <DemoShell />;
}
