"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { request } from "@/lib/http";
import type { ChapterRole, ChapterStaffRow } from "@/lib/api";

const ROLE_LABEL: Record<ChapterRole, string> = {
  owner: "Owner",
  organizer: "Organizer",
  judge: "Judge",
};
const ALL_ROLES: ChapterRole[] = ["owner", "organizer", "judge"];

function toggle(list: ChapterRole[], role: ChapterRole): ChapterRole[] {
  return list.includes(role) ? list.filter((r) => r !== role) : [...list, role];
}

export default function ChapterStaffPage() {
  const slug = useParams<{ slug: string }>().slug;
  const [staff, setStaff] = useState<ChapterStaffRow[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "notmanager">("loading");
  const [error, setError] = useState<string | null>(null);

  const [add, setAdd] = useState<{ email: string; roles: ChapterRole[] }>({
    email: "",
    roles: ["organizer"],
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editRoles, setEditRoles] = useState<ChapterRole[]>([]);
  const [editStatus, setEditStatus] = useState("active");

  async function refetch() {
    const res = await request<ChapterStaffRow[]>(
      `/api/chapter-staff/?chapter=${slug}`,
      "GET",
    );
    if (res.status === 403 || res.status === 401) {
      setState("notmanager");
      return;
    }
    if (res.ok && res.data) {
      setStaff(res.data);
      setState("ready");
    }
  }

  useEffect(() => {
    refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  async function addStaff(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (add.roles.length === 0) {
      setError("Pick at least one role.");
      return;
    }
    const res = await request("/api/chapter-staff/", "POST", {
      chapter: slug,
      email: add.email,
      roles: add.roles,
    });
    if (res.status === 201) {
      setAdd({ email: "", roles: ["organizer"] });
      refetch();
    } else {
      setError(res.errors[0] ?? "Could not add that person.");
    }
  }

  function startEdit(s: ChapterStaffRow) {
    setEditingId(s.id);
    setEditRoles(s.roles);
    setEditStatus(s.status);
    setError(null);
  }

  async function saveEdit(s: ChapterStaffRow) {
    setError(null);
    if (editRoles.length === 0) {
      setError("A staff member needs at least one role.");
      return;
    }
    const res = await request(`/api/chapter-staff/${s.id}/`, "PATCH", {
      roles: editRoles,
      status: editStatus,
    });
    if (res.ok) {
      setEditingId(null);
      refetch();
    } else {
      setError(res.errors[0] ?? "Could not save changes.");
    }
  }

  async function removeStaff(s: ChapterStaffRow) {
    if (!window.confirm(`Remove ${s.email} from this chapter's staff?`)) return;
    setError(null);
    const res = await request(`/api/chapter-staff/${s.id}/`, "DELETE");
    if (res.ok) refetch();
    else setError(res.errors[0] ?? "Could not remove that person.");
  }

  if (state === "loading") {
    return (
      <main className="container block">
        <p className="body">Loading…</p>
      </main>
    );
  }
  if (state === "notmanager") {
    return (
      <main className="container block">
        <h1 className="page-title"># chapter staff</h1>
        <p className="note">// you don&apos;t manage this chapter.</p>
      </main>
    );
  }

  return (
    <main className="container block">
      <p className="prompt">/chapters/{slug}/staff</p>
      <h1 className="page-title"># chapter staff</h1>
      <p className="subtitle">// owners &amp; organizers run the chapter; judges form its corps.</p>

      {error && <p className="form-error">{error}</p>}

      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>who</th>
              <th>roles</th>
              <th>status</th>
              <th>actions</th>
            </tr>
          </thead>
          <tbody>
            {staff.map((s) => (
              <tr key={s.id}>
                <td>
                  {s.display_name ? `${s.display_name} (${s.email})` : s.email}
                </td>
                {editingId === s.id ? (
                  <>
                    <td>
                      <div className="actions">
                        {ALL_ROLES.map((r) => (
                          <label key={r} className="check">
                            <input
                              type="checkbox"
                              checked={editRoles.includes(r)}
                              onChange={() => setEditRoles((rs) => toggle(rs, r))}
                            />{" "}
                            {ROLE_LABEL[r]}
                          </label>
                        ))}
                      </div>
                    </td>
                    <td>
                      <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                        <option value="active">active</option>
                        <option value="suspended">suspended</option>
                        <option value="pending">pending</option>
                      </select>
                    </td>
                    <td>
                      <div className="row-actions">
                        <button type="button" className="linkbtn" onClick={() => saveEdit(s)}>
                          save
                        </button>
                        <button
                          type="button"
                          className="linkbtn-danger"
                          onClick={() => setEditingId(null)}
                        >
                          cancel
                        </button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{s.roles.map((r) => ROLE_LABEL[r]).join(", ") || "—"}</td>
                    <td>{s.status}</td>
                    <td>
                      <div className="row-actions">
                        <button type="button" className="linkbtn" onClick={() => startEdit(s)}>
                          edit
                        </button>
                        <button
                          type="button"
                          className="linkbtn-danger"
                          onClick={() => removeStaff(s)}
                        >
                          remove
                        </button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="h2"># add staff</h2>
      <p className="note">// the person must already have a HackLet account.</p>
      <form className="form" onSubmit={addStaff}>
        <label className="field">
          <span>email *</span>
          <input
            type="email"
            value={add.email}
            onChange={(e) => setAdd((f) => ({ ...f, email: e.target.value }))}
            required
          />
        </label>
        <div className="field">
          <span>roles</span>
          <div className="actions">
            {ALL_ROLES.map((r) => (
              <label key={r} className="check">
                <input
                  type="checkbox"
                  checked={add.roles.includes(r)}
                  onChange={() => setAdd((f) => ({ ...f, roles: toggle(f.roles, r) }))}
                />{" "}
                {ROLE_LABEL[r]}
              </label>
            ))}
          </div>
        </div>
        <button className="btn" type="submit">
          [ add staff ]
        </button>
      </form>

      <p className="note">
        <Link href="/dashboard">&larr; dashboard</Link>
        {"  ·  "}
        <Link href={`/chapters/${slug}`}>chapter page</Link>
      </p>
    </main>
  );
}
