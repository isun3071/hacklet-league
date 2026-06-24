import Link from "next/link";
import { NewsletterSignup } from "@/components/NewsletterSignup";

export const metadata = {
  title: "About — HackLet League",
  description: "the story behind HackLet, the founder, how it works, and where the project is.",
};

export default function AboutPage() {
  return (
    <main className="container block">
      <p className="prompt">/about</p>
      <h1 className="page-title"># our story</h1>

      <p className="body">{`AI can build apps in hours. Increasing numbers of CS professionals rely on AI for coding. As famed AI researcher Andrej Karpathy said in 2025:`}</p>
      <blockquote className="callout">{`"There's a new kind of coding I call 'vibe coding', where you fully give in to the vibes, embrace exponentials, and forget that the code even exists. It's possible because the LLMs are getting too good."`}</blockquote>

      <p className="body">{`Can it build apps in minutes though? That was the question that started HackLet.`}</p>
      <p className="body">{`I was watching FMWC for Microsoft Excel, MasterChef, and the like, i.e. competitions that televise everyday skills under time pressure. I wondered if AI software engineering could work the same way. Could you watch engineers 'vibecode' on stage and find it as interesting as the Super Bowl? (That was a stretch, but you get the point.)`}</p>
      <p className="body">{`While watching a CS club meeting conduct a "speed pitch", where you got 10 minutes to come up with an app idea and present it, I saw the room light up and come alive. While scrolling on LinkedIn feeds, there was no shortage of viral apps made in hours with AI, apps that would take weeks or months otherwise. That was the proof of concept on the time compression.`}</p>
      <p className="body">{`And then I decided to take another look at the hackathons I competed in. What if, we messed up the units? So instead of 24 hours, it was 24 minutes?`}</p>

      <h2 className="h2">## about the founder</h2>
      <p className="body">{`I'm Ian Sun. I finished my BA in CS at Boston University in May 2026 and start a masters degree in CS/Cybersecurity there this fall. I'm IT Support at the BU Help Center and Internal Development Director at UPE.`}</p>
      <p className="body">{`I have spoken in several cybersecurity conferences concerning human layer security and behavioral risk. I introduced the "Dissonance Test" at SecureWorld Financial Services in 2025, returned to SecureWorld Boston in April 2026 with the bounded vs. unbounded deception lens, hosted sessions at RSAC 2026, debuted the "Deception Disruption Framework" at Layer 8 in June 2026, and co-presented "When Labs Have Stakes" at the NICE Conference with Dr. Faisal Abdullah, the latter of which concerns building instinctive operational judgment in up-and-coming practitioners where failures have cascading consequences.`}</p>
      <p className="body">{`HackLet started June 2, 2026 out of curiosity about whether building with AI could be televised and turned into a competition. Hackathons exist, but they have a rather complicated relationship with AI. HackLet embraces it, and tests whether engineers can create a working web app in a very short amount of time. And to ensure HackLet is not a slop machine, we fuzz every app that goes our way. (Not just because I have a cybersecurity background.)`}</p>
      <p className="body">
        (you can learn more about me at{" "}
        <a href="https://isun3071.github.io" target="_blank" rel="noopener noreferrer">
          isun3071.github.io
        </a>
        )
      </p>

      <h2 className="h2">## how it works</h2>
      <p className="body">{`HackLet compresses building into 24 minutes with AI. When time's up, our fuzzer runs against the submissions. Broken inputs, crashes, denial of service, the OWASP Top 10, and the like, are deployed. In other words, our fuzzer tests the same ways live production code breaks. In this manner, no slop survives.`}</p>
      <p className="body">{`In fact, we have a "slop score" to measure that. Lower is better, just like golf. The goal is to see if rapid AI software development can produce working code, or if it's doomed to produce slop.`}</p>
      <p className="body">{`We have two formats: HackLet Vibe (vibecoding from scratch, like a hackathon), and HackLet Unslop (fixing AI codebase slop, hence the name). Both go through the same fuzzer. HackLet Unslop specifically addresses what most software engineering work is, which is maintaining and fixing existing codebases.`}</p>
      <p className="body">{`HackLet aims to have three tiers of events. Starting with tier C, the entry-level tier, equivalent to hackathons. Anyone can run these, and it lasts no longer than an hour-long club meeting. At tier B, events use AI models that HackLet provides, with written attestation of anti-cheating codes. And at tier A, events use controlled workstations and are broadcast live, with results feeding into global rankings. The higher the tier, the more rigorous the verification, and therefore, the more reliable an achievement there is.`}</p>

      <h2 className="h2">## where we are</h2>
      <p className="body">{`HackLet started June 2, 2026 and our platform shipped publicly within weeks. Right now the fuzzer is in the works, and pilot events will follow after that.`}</p>

      <h2 className="h2">## how to engage</h2>
      <p className="body">{`If you want notification when there's a HackLet to sign up for, the newsletter form is below.`}</p>
      <p className="body">
        If you want to run a chapter, judge, sponsor, or contribute to the catalog,{" "}
        <Link href="/contact">reach out</Link>.
      </p>
      <p className="body">{`Or if you just want to watch the project evolve, the platform operates publicly.`}</p>
      <NewsletterSignup />
      <p className="body">{`Happy vibecoding!`}</p>
    </main>
  );
}
