import Link from "next/link";

export const metadata = {
  title: "Contact — HackLet League",
  description: "get in touch to run a chapter, judge, sponsor, or contribute to the catalog.",
};

const EMAIL = "iansun20@gmail.com";

const OPTIONS: { label: string; subject: string }[] = [
  { label: "run a chapter", subject: "[HackLet] running a chapter" },
  { label: "judge / join the corps", subject: "[HackLet] judging" },
  { label: "sponsor", subject: "[HackLet] sponsorship" },
  { label: "contribute to the catalog", subject: "[HackLet] catalog contribution" },
  { label: "something else", subject: "[HackLet] hello" },
];

export default function ContactPage() {
  return (
    <main className="container block">
      <p className="prompt">/contact</p>
      <h1 className="page-title"># contact</h1>
      <p className="subtitle">
        // want to run a chapter, judge, sponsor, or help build the catalog? get in touch.
      </p>

      <p className="body">{`Email me directly. Pick the closest reason to pre-fill the subject, or just write.`}</p>

      <div className="actions">
        {OPTIONS.map((o) => (
          <a
            key={o.subject}
            className="btn"
            href={`mailto:${EMAIL}?subject=${encodeURIComponent(o.subject)}`}
          >
            [ {o.label} ]
          </a>
        ))}
      </div>

      <p className="note">
        or copy the address: <a href={`mailto:${EMAIL}`}>{EMAIL}</a>
      </p>
      <p className="note">
        just want to follow along? the newsletter form is on the{" "}
        <Link href="/about">about page</Link>, and the platform operates publicly.
      </p>
    </main>
  );
}
