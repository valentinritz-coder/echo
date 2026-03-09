import { LifeLine } from './components/LifeLine'

function App() {
  return (
    <div className="lab">
      <div className="lab-glow" aria-hidden />
      <main className="lab-main">
        <section className="lab-hero" aria-label="Présentation de la Life Line">
          <p className="lab-eyebrow">ECHO</p>
          <h1 className="lab-headline">Votre vie, d'un seul regard.</h1>
          <p className="lab-subtext">
            Les zones <span className="lab-subtext-highlight">plus lumineuses</span> contiennent davantage de souvenirs.
          </p>
          <LifeLine />
        </section>
      </main>
    </div>
  )
}

export default App
