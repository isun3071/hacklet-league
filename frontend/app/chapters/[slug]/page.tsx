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
      <p className="readout">
        tier {chapter.tier} &middot; {chapter.mode}
        {chapter.institutional_affiliation ? ` · ${chapter.institutional_affiliation}` : ""}
      </p>
      {chapter.location_text && <p className="body">{chapter.location_text}</p>}
      <p className="body">{chapter.description || "No description yet."}</p>
      {chapter.website_url && (
        <p className="body">
          <a href={chapter.website_url} rel="noopener noreferrer">
            {chapter.website_url}
          </a>
        </p>
      )}
      <p className="note">
        <Link href="/chapters">&larr; all chapters</Link>
      </p>
    </main>
  );
}
