export default function Home() {
  return (
    <>
      <header className="bar">
        <div className="container bar-inner">
          <span className="logo">
            hacklet<span className="accent">_league</span>
          </span>
          <a className="bar-link" href="#signup">[ get updates ]</a>
        </div>
      </header>

      <main>
        <section className="container hero">
          <p className="prompt">
            hacklet@league:~$ ./about --season-1<span className="cursor">█</span>
          </p>
          <h1 className="headline">The fuzz is what separates hacklets from slop.</h1>
          <p className="readout">build 24:00 &middot; one AI &middot; ship it &middot; then defend it</p>
          <p className="sub">
            24 minutes. One AI. Build a web app, then watch attackers try to break it.
            The people who win can steer a model and catch its mistakes before they ship.
          </p>
          <div className="actions">
            <a className="btn" href="#signup">[ get updates ]</a>
          </div>
        </section>

        <hr className="rule" />

        <section className="container block">
          <h2 className="h2"># the format</h2>
          <p className="body">
            <strong className="hl">
              Hackathon, but minutes instead of hours. With a crowd watching.
            </strong>{" "}
            You get 24 minutes and one mid-tier AI to build a working web app and write it
            up. No web search, no second AI, no pasting from Stack Overflow. What&rsquo;s left
            is how well you drive the model, and whether you catch it when it&rsquo;s wrong.
          </p>
          <p className="body">
            At zero, the network drops and your code freezes. A commit grabs exactly what was
            there at the buzzer, and that&rsquo;s your submission. Then it gets attacked.
          </p>
        </section>

        <hr className="rule" />

        <section className="container band">
          <p className="band-line">
            <span className="dim">//</span> the models do the typing. the judgment is yours.
          </p>
          <p className="band-sub">
            A model will write you a demo in a minute. Whether it survives a real attacker is
            the harder question, and the more interesting one. That doesn&rsquo;t get easier as
            the models improve. It&rsquo;s the part we score.
          </p>
        </section>

        <hr className="rule" />

        <section className="container block" id="signup">
          <h2 className="h2"># season one is coming</h2>
          <p className="body">
            I&rsquo;m still building this. Leave your email and I&rsquo;ll let you know when there&rsquo;s a
            season to sign up for.
          </p>
          <form
            className="signup-form"
            action="https://buttondown.com/api/emails/embed-subscribe/iansun20"
            method="post"
            target="popupwindow"
          >
            <label className="sr-only" htmlFor="bd-email">email address</label>
            <span className="form-prompt">subscribe:~$</span>
            <input
              id="bd-email"
              type="email"
              name="email"
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
            <input type="hidden" name="embed" defaultValue="1" />
            <button type="submit" className="btn">[ notify me ]</button>
          </form>
        </section>
      </main>

      <footer className="foot">
        <div className="container bar-inner">
          <span className="logo">
            hacklet<span className="accent">_league</span>
          </span>
          <span className="muted">in development &middot; 2026</span>
        </div>
      </footer>
    </>
  );
}
