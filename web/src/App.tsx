import './theme.css'
import { ToastHost } from './components'
import { Playground } from './screens/Playground'

const ROUTES: Record<string, () => JSX.Element> = {
  '/playground': Playground,
}

export function App() {
  const Screen = ROUTES[window.location.pathname] ?? Playground
  return (
    <>
      <Screen />
      <ToastHost />
    </>
  )
}
