"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { request } from "@/lib/http";
import type { Chapter } from "@/lib/api";

// Owner-facing copy for each lifecycle state (see chapters/models.py).
const STATUS: Record<string, { label: string; cls: string; blurb: string }> = {
  pending: {
    label: "pending review",
    cls: "badge-pending",
    blurb: "awaiting review by a league admin",
  },
  verified: {
    label: "verified",
    cls: "badge-verified",
    blurb: "approved and public in the directory",
  },
  suspended: {
    label: "suspended",
    cls: "badge-suspended",
    blurb: "verification revoked — contact the league to restore it",
  },
  unverified: {
    label: "not approved",
    cls: "badge-unverified",
    blurb: "reviewed and not approved — you can revise and resubmit",
  },
};

export default function DashboardPage() {
  const [chapters, setChapters] = useState<Chapter[] | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "unauth">("loading");

  useEffect(() => {
    request<Chapter[]>("/api/chapters/mine/", "GET").then((res) => {
      if (res.status === 200 && Array.isArray(res.data)) {
        setChapters(res.data);
        setState("ready");
      } else {
        setState("unauth");
      }
    });
  }, []);

  async function onDelete(c: Chapter) {
    if (
      !window.confirm(
        `Delete "${c.name}"? This permanently removes the chapter and can't be undone.`,
      )
    ) {
      return;
    }
    const res = await request(`/api/chapters/${c.slug}/`, "DELETE");
    if (res.ok) {
      setChapters((prev) => (prev ? prev.filter((x) => x.id !== c.id) : prev));
    } else {
      window.alert("Could not delete that chapter. Please try again.");
    }
  }

  if (state === "loading") {
    return (
      <main className="container block">
        <p className="body">Loading…</p>
      </main>
    );
  }

  if (state === "unauth") {
    return (
      <main className="container block">
        <h1 className="page-title"># dashboard</h1>
        <p className="body">
          You need to <Link href="/auth/login">log in</Link> to manage your chapters.
        </p>
      </main>
    );
  }

  const list = chapters ?? [];

  return (
    <main className="container block">
      <h1 className="page-title"># dashboard</h1>
      <p className="subtitle">// your chapters</p>

      {list.length === 0 ? (
        <p className="note">
          // you haven&apos;t created a chapter yet.{" "}
          <Link href="/chapters/new">apply to create one &rarr;</Link>
        </p>
      ) : (
        <>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>chapter</th>
                  <th>tier</th>
                  <th>status</th>
                  <th>actions</th>
                </tr>
              </thead>
              <tbody>
                {list.map((c) => {
                  const s = STATUS[c.verification_status] ?? {
                    label: c.verification_status,
                    cls: "badge-unverified",
                    blurb: "",
                  };
                  return (
                    <tr key={c.id}>
                      <td>
                        <Link href={`/chapters/${c.slug}`}>{c.name}</Link>
                      </td>
                      <td>{c.tier}</td>
                      <td>
                        <span className={`badge ${s.cls}`}>{s.label}</span>
                        {s.blurb && <span className="badge-blurb"> — {s.blurb}</span>}
                      </td>
                      <td>
                        <div className="row-actions">
                          <Link href={`/chapters/${c.slug}/edit`}>edit</Link>
                          <button
                            type="button"
                            className="linkbtn-danger"
                            onClick={() => onDelete(c)}
                          >
                            delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="note">
            <Link href="/chapters/new">+ apply to create another chapter</Link>
          </p>
        </>
      )}
    </main>
  );
}
