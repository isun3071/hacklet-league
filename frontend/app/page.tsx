import Link from "next/link";
import { AsciiRule } from "@/components/AsciiRule";
import { FuzzWave } from "@/components/FuzzWave";
import { Icon } from "@/components/Icon";
import { NewsletterSignup } from "@/components/NewsletterSignup";
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

const UNDERSPEC_PHASES: Phase[] = [
  { name: "opening", mins: 5, time: "5m", tone: "muted" },
  { name: "interpret + build", mins: 24, time: "24m", tone: "accent" },
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
        {/* Hierarchy is size + brightness: the tagline is the focal point, the rest step down
            (see .hero-* in globals.css). */}
        <h1 className="hero-line hero-tagline">move fast, break nothing.</h1>
        <p className="hero-line hero-descriptor">
          a rapid app building league with automated stress testing
        </p>
        <p className="hero-line hero-body">
          We took a hackathon and messed up the units. You have 24{" "}
          <s className="struck">hours</s> minutes to build, and then everything you built
          gets put to the test.
        </p>
        <div className="actions">
          <Link className="btn" href="#signup">
            [ get notified ]
          </Link>
          <Link className="textlink" href="#how">
            how it works &rarr;
          </Link>
        </div>
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
          HackLet League runs three formats. All three compress engineering into 24 minutes with
          AI, all three run the same QA catalog at time expiry, all three score across slop and
          communication. They differ in what you do during the build phase.
        </p>
        <p className="note">
          <Link href="/scoring">see exactly how scoring works &rarr;</Link>
        </p>
        <pre className="codeblock">{`$ ./hacklet --formats
  vibe            build a working web app from scratch
  unslop          diagnose and fix a broken ai-generated app (the
                  kind you'd call "slop")
  underspecified  build to a vague client brief, and defend how you
                  read it`}</pre>

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

        <h3 className="h3">
          <span className="icon-label">
            <Icon name="underspecified" /> ## HackLet Underspecified: read the brief
          </span>
        </h3>
        <p className="body">
          Get a vague, half-formed client brief. Work out what they actually need, build it, and
          defend the call you made. The brief does not hand you the answer, and reading it wrong
          is part of the test.
        </p>
        <TimelineBar phases={UNDERSPEC_PHASES} />
        <pre className="codeblock">{`$ ./hacklet --format underspecified --timeline
  5 min     opening · the vague brief drops
  24 min    interpret + build · decide what it means, then ship it
  18 min    defend · same qa testing + pitch prep
  5-30 min  pitch · defend how you read the brief
  8 min     awards · closing`}</pre>
        <p className="body">
          HackLet Underspecified tests the thing a real client meeting tests: turning an unclear
          ask into a defensible plan. Most engineering that fails does not fail because the code
          was bad. It fails because someone built the wrong thing well.
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
        <NewsletterSignup />
      </section>
    </main>
  );
}
