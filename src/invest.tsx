import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { RaisePage } from './features/raise/RaisePage'
import { installAnalytics } from './lib/investorAnalytics'

installAnalytics()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RaisePage />
  </StrictMode>,
)
