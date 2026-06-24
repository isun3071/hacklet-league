import Link from "next/link";

export const metadata = {
  title: "How scoring works — HackLet League",
  description: "exactly how the fuzz catalog deploys and tests your app, and how the slop score works. no surprises on competition day.",
};

const STEPS: { n: string; title: string; body: React.ReactNode }[] = [
  {
    n: "0",
    title: "submit",
    body: (
      <>
        at the 24-minute freeze your code is captured with its <code>Dockerfile</code> and queued
        for testing. Tier C uploads through the portal (3-minute grace for latency); Tier A captures
        straight from your workstation.
      </>
    ),
  },
  {
    n: "1",
    title: "deploy",
    body: (
      <>
        we build your <code>Dockerfile</code> and run your app in an isolated container with{" "}
        <span className="hl">no internet access</span>. we check it answers on <code>$PORT</code>{" "}
        within ~60 seconds. if it never responds, that is a <span className="chip chip-dnf">DNF</span>.
      </>
    ),
  },
  {
    n: "2",
    title: "discover",
    body: (
      <>
        we explore your running app over HTTP (pages, forms, APIs, even JS-rendered routes) to map
        its surface. we only ever see what your app exposes, never your source or your stack.
      </>
    ),
  },
  {
    n: "3",
    title: "match",
    body: (
      <>
        every probe in the catalog that applies to your surface gets queued. probes for features you
        do not have are simply skipped, with no penalty.
      </>
    ),
  },
  {
    n: "4",
    title: "run the probes",
    body: (
      <>
        each probe checks for one specific problem and either finds slop (
        <span className="chip chip-slop">+penalty</span>) or does not (
        <span className="chip chip-clean">0</span>). timing and concurrency checks run several times
        and take the median, so one unlucky moment will not sink you.
      </>
    ),
  },
  {
    n: "5",
    title: "tally",
    body: (
      <>
        we sum the penalties into your slop score, weighted by breadth and severity. one SQL
        injection outweighs a pile of minor issues, and repeating the same small mistake everywhere
        does not stack up linearly.
      </>
    ),
  },
  {
    n: "6",
    title: "results",
    body: (
      <>
        your slop score joins your communication score (pitch + cross-examination), and Best Overall
        is decided by rank across both. your container is then destroyed; nothing you ran sticks
        around.
      </>
    ),
  },
];

export default function ScoringPage() {
  return (
    <main className="container block">
      <p className="prompt">/scoring</p>
      <h1 className="page-title"># how scoring works</h1>
      <p className="subtitle">
        // the fuzz is what separates hacklets from slop. here is exactly how we measure it, so
        nothing is a surprise on competition day.
      </p>

      <h2 className="h2"># the slop score</h2>
      <p className="body">
        scoring is deduction-only. you start at zero (clean) and every probe that finds a problem
        adds slop. passing a probe, or not having the feature it targets, adds nothing.{" "}
        <span className="hl">lower is better, and zero is perfect.</span> it is golf, not basketball.
      </p>
      <p className="body">
        you do not get credit for <em>not</em> having SQL injection. that is the baseline we expect.
        you get penalized for having it.
      </p>
      <p className="callout callout-warn">
        defending 7 of 8 SQL endpoints is not 87% safe. it is a breach through the 8th. the seven
        clean ones add nothing, the one failure adds its full penalty. that is how real security
        works, so that is how slop works.
      </p>

      <h2 className="h2"># what gets tested</h2>
      <p className="body">one catalog, three bundles, run identically against every submission:</p>
      <pre className="codeblock">{`security     sql injection · xss · auth bypass · access control
             csrf · file upload · sensitive-path exposure
qa           crash resistance · error hygiene · http semantics · encoding
performance  speed gates (ttfb/fcp/inp) · load · dos resistance`}</pre>
      <p className="body">
        each penalty scales by how common the flaw is and how bad its worst case is, discounted by
        how hard the fix is in 24 minutes. a competent engineer under a real deadline triages, and
        the scoring credits that judgment instead of demanding perfection.
      </p>

      <h2 className="h2"># the process, step by step</h2>
      <div className="flow">
        <span className="k">submit</span><b>→</b>
        <span className="k">deploy</span><b>→</b>
        <span>discover</span><b>→</b>
        <span>match</span><b>→</b>
        <span>run probes</span><b>→</b>
        <span>tally</span><b>→</b>
        <span>results</span>
      </div>
      <div className="steps">
        {STEPS.map((s) => (
          <div className="step" key={s.n}>
            <div className="stepn">{s.n}</div>
            <h3 className="step-title">{s.title}</h3>
            <p className="step-body">{s.body}</p>
          </div>
        ))}
      </div>

      <h2 className="h2"># your part: a dockerfile</h2>
      <p className="body">
        your submission includes a <code>Dockerfile</code> (we ship starter templates for every
        common stack, so you barely touch it). your app listens on the port we hand it via{" "}
        <code>$PORT</code>. if you need a database, connect to the one we provide at{" "}
        <code>$DATABASE_URL</code>. that is the whole contract.
      </p>
      <p className="callout callout-warn">
        if your app does not deploy and answer HTTP, it is a DNF, the worst possible outcome, ranked
        below everyone who shipped something that actually runs. a thing that runs beats a clever
        thing that does not.
      </p>

      <h2 className="h2"># you can study the catalog</h2>
      <p className="body">
        about 75% of the catalog is public. study it, and self-test against it while you build. the
        other 25% is hidden, so defending only the published probes by name still leaves you exposed.
        genuine defense (parameterized queries, output encoding, real access control) clears the
        public and hidden probes alike, because it fixes the actual flaw rather than the specific
        payload.
      </p>

      <h2 className="h2"># tested the same way, whatever your stack</h2>
      <p className="body">
        once your container answers HTTP, the runner is stack-blind. Flask, Express, Go, Rust, a
        hand-rolled server, it does not matter. the catalog is identical for everyone. your stack
        choice affects how easily you defend (some frameworks handle a lot by default), not what gets
        tested. same ruler for all.
      </p>

      <p className="note">
        <Link href="/#how">&larr; the two formats</Link>
        {"  ·  "}
        <Link href="/leaderboard">leaderboard &rarr;</Link>
      </p>
    </main>
  );
}
