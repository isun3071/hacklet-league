import { AsciiRule } from "@/components/AsciiRule";
import { FuzzWave } from "@/components/FuzzWave";
import { Icon } from "@/components/Icon";
import { TimelineBar, type Phase } from "@/components/TimelineBar";

const VIBE_PHASES: Phase[] = [
  { name: "opening", mins: 5, time: "5m", tone: "muted" },
  { name: "build", mins: 24, time: "24m", tone: "accent" },
  { name: "defend", mins: 18, time: "18m", tone: "danger" },
  { name: "pitch", mins: 15, time: "5–30m", tone: "muted" },
  { name: "awards", mins: 8, time: "8m", tone: "muted" },
];

const UNSLOP_PHASES: Phase[] = [
  { name: "opening", mins: 5, time: "5m", tone: "muted" },
  { name: "remediate", mins: 24, time: "24m", tone: "accent" },
  { name: "defend", mins: 18, time: "18m", tone: "danger" },
  { name: "pitch", mins: 15, time: "5–30m", tone: "muted" },
  { name: "awards", mins: 8, time: "8m", tone: "muted" },
];

export default function Home() {
  return (
    <main>
      {/* SECTION 1: HERO */}
      <section className="container hero">
        <FuzzWave />
        <h1 className="headline">
          24 minutes of competitive vibecoding. no slop survives.
        </h1>
        <p className="readout">build with AI • defend it • pitch it • under pressure</p>
        <p className="sub">
          We took a hackathon and messed up the units. Now we only get 24 minutes to build.
          AI included. The winners can steer it and avoid catastrophic bugs on stage.
        </p>
      </section>

      <AsciiRule />

      {/* SECTION 2: DICTIONARY ENTRY */}
      <section className="container block" id="define">
        <div className="dict">
          <p className="dict-head">
            hack<span className="dict-sep">•</span>let
            <span className="dict-ipa">(hæk-lət)</span>
            <span className="dict-pos">n.</span>
          </p>
          <ol className="dict-defs">
            <li>
              An app built in a very short amount of time, typically with AI assistance:{" "}
              <em>My roommate built a hacklet while waiting for his flight.</em>
            </li>
            <li>
              A tightly compressed hackathon with an audience possibility:{" "}
              <em>Come attend a hacklet; it lasts no longer than a cs club meeting.</em>
            </li>
          </ol>
        </div>
      </section>

      <AsciiRule />

      {/* SECTION 3: HOW IT WORKS */}
      <section className="container block" id="how">
        <h2 className="h2"># how it works</h2>
        <p className="body">
          HackLet League runs two formats. Both compress engineering into 24 minutes with AI,
          both run the same QA catalog at time expiry, both score across resilience and
          communication. They differ in what you do during the build phase.
        </p>
        <pre className="codeblock">{`$ ./hacklet --formats
  vibe     build a working web app from scratch
  unslop   diagnose and fix a broken ai-generated app (the kind
           you'd call "slop")`}</pre>

        <h3 className="h3">
          <span className="icon-label">
            <Icon name="vibe" /> ## HackLet Vibe: build from scratch
          </span>
        </h3>
        <p className="body">Build a working web app with AI assistance of your own choice.</p>
        <TimelineBar phases={VIBE_PHASES} />
        <pre className="codeblock">{`$ ./hacklet --format vibe --timeline
  5 min     opening · round prep
  24 min    build · ai-assisted building (aka vibecoding)
  18 min    defend · qa testing + pitch prep
  5-30 min  pitch · judging
  8 min     awards · closing`}</pre>
        <p className="body">
          HackLet Vibe is akin to a traditional hackathon except with time compressed to
          minutes instead of hours. As AI is ubiquitous, HackLet Vibe tests if you can build
          apps of function, instead of apps of just form.
        </p>

        <h3 className="h3">
          <span className="icon-label">
            <Icon name="unslop" /> ## HackLet Unslop: fix the slop (hence the name ;) )
          </span>
        </h3>
        <p className="body">
          Receive a broken AI-written codebase at the beginning. Figure out what&rsquo;s wrong
          across multiple dimensions and improve upon it. Ship a defended version.
        </p>
        <TimelineBar phases={UNSLOP_PHASES} />
        <pre className="codeblock">{`$ ./hacklet --format unslop --timeline
  5 min     opening · broken codebase revealed
  24 min    remediate · ai-assisted diagnosis and repair
  18 min    defend · same qa testing + pitch prep
  5-30 min  pitch · same judging
  8 min     awards · closing`}</pre>
        <p className="body">
          HackLet Unslop reflects the reality of engineering work: working with existing
          codebases that may or may not be functioning ideally. HackLet Unslop tests if you
          can deal with existing code you see at work... under pressure.
        </p>
      </section>

      <AsciiRule />

      {/* SECTION 4: CTA / NEWSLETTER SIGNUP */}
      <section className="container block" id="signup">
        <h2 className="h2"># First HackLet coming soon</h2>
        <p className="body">
          I&rsquo;m still building this. Leave your email and I&rsquo;ll let you know when
          there&rsquo;s a HackLet to sign up for.
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
  );
}
