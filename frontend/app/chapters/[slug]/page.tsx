import Link from "next/link";
import { notFound } from "next/navigation";
import { getChapter } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ChapterPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const chapter = await getChapter(slug);
  if (!chapter) notFound();

  return (
    <main className="container block">
      <p className="prompt">/chapters/{chapter.slug}</p>
      <h1 className="page-title">{chapter.name}</h1>

      {chapter.verification_status !== "verified" && (
        <p className="status-banner">
          ⏳ <strong>Pending approval</strong> — this chapter is awaiting review by a
          league admin and isn&apos;t public yet. Only you (its creator) can see this page.
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
