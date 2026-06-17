import Link from "next/link";
import { notFound } from "next/navigation";
import { getChapter } from "@/lib/api";

export const dynamic = "force-dynamic";

// Owner-only banner per non-public lifecycle state (see chapters/models.py).
// A verified chapter has no entry here -> no banner.
const STATUS_BANNER: Record<string, { icon: string; label: string; text: string }> = {
  pending: {
    icon: "⏳",
    label: "Pending approval",
    text: "this chapter is awaiting review by a league admin and isn't public yet.",
  },
  suspended: {
    icon: "⛔",
    label: "Suspended",
    text: "this chapter's verification was revoked, so it isn't public — contact the league to restore it.",
  },
  unverified: {
    icon: "✗",
    label: "Not approved",
    text: "this chapter was reviewed and not approved; you can revise it and resubmit.",
  },
};

export default async function ChapterPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const chapter = await getChapter(slug);
  if (!chapter) notFound();

  const banner = STATUS_BANNER[chapter.verification_status];

  return (
    <main className="container block">
      <p className="prompt">/chapters/{chapter.slug}</p>
      <h1 className="page-title">{chapter.name}</h1>

      {banner && (
        <p className="status-banner">
          {banner.icon} <strong>{banner.label}</strong> — {banner.text} You (its creator)
          can see this page; the public can&apos;t until it&apos;s verified.
        </p>
      )}

      <div className="panel">
        <dl className="kv">
          <div>
            <dt>tier</dt>
            <dd>{chapter.tier}</dd>
          </div>
          <div>
            <dt>mode</dt>
            <dd>{chapter.mode}</dd>
          </div>
          {chapter.location_text && (
            <div>
              <dt>where</dt>
              <dd>{chapter.location_text}</dd>
            </div>
          )}
          {chapter.institutional_affiliation && (
            <div>
              <dt>affiliation</dt>
              <dd>{chapter.institutional_affiliation}</dd>
            </div>
          )}
          {chapter.website_url && (
            <div>
              <dt>site</dt>
              <dd>
                <a href={chapter.website_url} rel="noopener noreferrer">
                  {chapter.website_url}
                </a>
              </dd>
            </div>
          )}
        </dl>
        <p className="chapter-desc">{chapter.description || "No description yet."}</p>
      </div>

      <p className="note">
        <Link href="/chapters">&larr; all chapters</Link>
      </p>
    </main>
  );
}
