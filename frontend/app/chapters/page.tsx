import Link from "next/link";
import { getChapters, type Chapter } from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Chapters — HackLet League",
};

export default async function ChaptersPage() {
  let chapters: Chapter[] = [];
  let failed = false;
  try {
    chapters = await getChapters();
  } catch {
    failed = true;
  }

  return (
    <main className="container block">
      <h1 className="page-title"># chapters</h1>

      {failed ? (
        <p className="note">// directory temporarily unavailable.</p>
      ) : chapters.length === 0 ? (
        <p className="note">
          // no chapters listed yet. <Link href="/#signup">get notified &rarr;</Link>
        </p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>chapter</th>
                <th>tier</th>
                <th>where</th>
              </tr>
            </thead>
            <tbody>
              {chapters.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link href={`/chapters/${c.slug}`}>{c.name}</Link>
                  </td>
                  <td>{c.tier}</td>
                  <td>{c.location_text || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
