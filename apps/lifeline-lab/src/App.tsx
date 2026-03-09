import { LifeLine } from './components/LifeLine'

function App() {
  return (
    <div className="lab">
      <div className="lab-glow" aria-hidden />
      <main className="lab-main">
        <div className="lab-preview">
          <LifeLine />
        </div>
      </main>
    </div>
  )
}

export default App
