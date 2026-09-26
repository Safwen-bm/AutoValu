"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_ML_URL ?? 'http://localhost:8000';

type Submission = {
  id: string;
  timestamp: string;
  brand: string;
  model: string;
  year: number;
  fuel: string;
  body_style: string;
  car_condition: string;
  trim_level: string;
  mileage_km: number | null;
  engine_cc: number | null;
  user_price: number;
  predicted_price: number;
  segment: string;
  status: string;
  admin_note: string | null;
};

type Stats = {
  total_queries: number;
  submissions: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  top_brands: { brand: string; count: number }[];
};

const fmt = (n: number) => n?.toLocaleString("fr-TN") + " DT";

const diffPct = (user: number, pred: number) => {
  const d = ((user - pred) / pred) * 100;
  return `${d > 0 ? "+" : ""}${d.toFixed(1)}%`;
};

const diffColor = (user: number, pred: number) => {
  const d = ((user - pred) / pred) * 100;
  if (d <= -15) return "#10B981";
  if (d <= 10) return "#D97706";
  if (d <= 25) return "#EA580C";
  return "#DC2626";
};

const badge = (status: string) => {
  const map: Record<string, string> = {
    pending: "#D97706",
    approved: "#10B981",
    rejected: "#DC2626",
  };
  return (
    <span
      style={{
        background: map[status] || "#6B7280",
        color: "white",
        padding: "2px 10px",
        borderRadius: 20,
        fontSize: 12,
        fontWeight: 700,
      }}
    >
      {status}
    </span>
  );
};

export default function AdminPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [authed, setAuthed] = useState(false);

  const [tab, setTab] = useState<"submissions" | "queries" | "stats">(
    "submissions",
  );
  const [filter, setFilter] = useState("pending");
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [queries, setQueries] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState<Record<string, string>>({});

  useEffect(() => {
    const t = sessionStorage.getItem("autovalu_token");
    if (!t) {
      router.push("/admin/login");
      return;
    }
    setToken(t);
    setAuthed(true);
  }, [router]);

  const logout = () => {
    sessionStorage.removeItem("autovalu_token");
    router.push("/admin/login");
  };

  const load = useCallback(async () => {
      if (!token) return;
      setLoading(true);
      try {
        if (tab === "submissions") {
          const res = await fetch(
            `${API}/admin/submissions?secret=${token}&status=${filter}`,
          );
          if (!res.ok) { setLoading(false); return; }
          const data = await res.json();
          setSubmissions(Array.isArray(data) ? data : []);
        } else if (tab === "stats") {
          const res = await fetch(`${API}/admin/stats?secret=${token}`);
          if (!res.ok) { setLoading(false); return; }
          setStats(await res.json());
        } else {
          const res = await fetch(
            `${API}/admin/queries?secret=${token}&limit=100`,
          );
          if (!res.ok) { setLoading(false); return; }
          const data = await res.json();
          setQueries(Array.isArray(data) ? data : []);
        }
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    }, [tab, filter, token]);

  useEffect(() => {
    load();
  }, [load]);

  if (!authed) return null;

  const review = async (id: string, action: "approve" | "reject") => {
    const note = encodeURIComponent(notes[id] || "");
    await fetch(
      `${API}/admin/review?secret=${token}&submission_id=${id}&action=${action}&note=${note}`,
      {
        method: "POST",
      },
    );
    load();
  };

  const s = {
    card: {
      background: "white",
      border: "1px solid #E5E7EB",
      borderRadius: 12,
      padding: 20,
      boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    },
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#F5F7FA",
        fontFamily: "Segoe UI,system-ui,sans-serif",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          background: "#0f172a",
          padding: "18px 32px",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <span style={{ fontSize: 22 }}>🚗</span>
        <div>
          <div style={{ color: "white", fontWeight: 800, fontSize: 17 }}>
            <span style={{ color: "#10B981" }}>Auto</span>Valu Admin
          </div>
          <div style={{ color: "#64748b", fontSize: 12 }}>
            Price Intelligence Dashboard
          </div>
        </div>
        <button
          onClick={load}
          style={{
            marginLeft: "auto",
            padding: "7px 16px",
            background: "#10B981",
            color: "white",
            border: "none",
            borderRadius: 8,
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ↻ Refresh
        </button>
        <button
          onClick={logout}
          style={{
            marginLeft: 8,
            padding: "7px 14px",
            background: "transparent",
            color: "#DC2626",
            border: "1px solid #DC2626",
            borderRadius: 8,
            cursor: "pointer",
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          Sign out
        </button>
      </div>

      {/* TABS */}
      <div
        style={{
          background: "white",
          borderBottom: "1px solid #E5E7EB",
          padding: "0 32px",
          display: "flex",
        }}
      >
        {(["submissions", "queries", "stats"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "12px 18px",
              border: "none",
              background: "transparent",
              borderBottom:
                tab === t ? "2px solid #10B981" : "2px solid transparent",
              color: tab === t ? "#10B981" : "#6B7280",
              fontWeight: tab === t ? 700 : 500,
              cursor: "pointer",
              fontSize: 13,
              textTransform: "capitalize",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      <div style={{ padding: "24px 32px" }}>
        {/* SUBMISSIONS */}
        {tab === "submissions" && (
          <div>
            <div
              style={{
                display: "flex",
                gap: 8,
                marginBottom: 20,
                alignItems: "center",
              }}
            >
              {["pending", "approved", "rejected", "all"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  style={{
                    padding: "6px 16px",
                    borderRadius: 20,
                    border: filter === f ? "none" : "1px solid #E5E7EB",
                    background: filter === f ? "#0f172a" : "white",
                    color: filter === f ? "white" : "#6B7280",
                    fontWeight: 600,
                    cursor: "pointer",
                    fontSize: 13,
                    textTransform: "capitalize",
                  }}
                >
                  {f}
                </button>
              ))}
              <span
                style={{ marginLeft: "auto", color: "#6B7280", fontSize: 13 }}
              >
                {submissions.length} results
              </span>
            </div>

            {loading && (
              <div
                style={{ textAlign: "center", padding: 60, color: "#6B7280" }}
              >
                Loading...
              </div>
            )}

            {!loading && submissions.length === 0 && (
              <div
                style={{ textAlign: "center", padding: 60, color: "#9CA3AF" }}
              >
                No {filter} submissions.
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {submissions.map((sub) => (
                <div key={sub.id} style={s.card}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: 14,
                    }}
                  >
                    <div>
                      <span
                        style={{
                          fontWeight: 800,
                          fontSize: 15,
                          textTransform: "uppercase",
                        }}
                      >
                        {sub.brand} {sub.model}
                      </span>
                      <span
                        style={{
                          color: "#6B7280",
                          fontSize: 13,
                          marginLeft: 8,
                        }}
                      >
                        {sub.year} · {sub.fuel} · {sub.car_condition}
                      </span>
                    </div>
                    <div
                      style={{ display: "flex", alignItems: "center", gap: 8 }}
                    >
                      {badge(sub.status)}
                      <span style={{ color: "#9CA3AF", fontSize: 12 }}>
                        {String(sub.timestamp).slice(0, 16)}
                      </span>
                    </div>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4,1fr)",
                      gap: 10,
                      marginBottom: 14,
                    }}
                  >
                    {[
                      {
                        label: "USER PRICE",
                        value: fmt(sub.user_price),
                        bold: true,
                      },
                      {
                        label: "MODEL PREDICTED",
                        value: fmt(sub.predicted_price),
                        bold: false,
                      },
                      {
                        label: "DIFFERENCE",
                        value: diffPct(sub.user_price, sub.predicted_price),
                        color: diffColor(sub.user_price, sub.predicted_price),
                      },
                      {
                        label: "MILEAGE / CC",
                        value: `${sub.mileage_km ? sub.mileage_km.toLocaleString() + " km" : "—"} · ${sub.engine_cc ? sub.engine_cc + "cc" : "—"}`,
                      },
                    ].map((item, i) => (
                      <div
                        key={i}
                        style={{
                          background: "#F9FAFB",
                          borderRadius: 8,
                          padding: "10px 14px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: 10,
                            color: "#6B7280",
                            fontWeight: 700,
                            marginBottom: 4,
                            letterSpacing: "0.05em",
                          }}
                        >
                          {item.label}
                        </div>
                        <div
                          style={{
                            fontWeight: 700,
                            fontSize: 15,
                            color: item.color || "#111827",
                          }}
                        >
                          {item.value}
                        </div>
                      </div>
                    ))}
                  </div>

                  {sub.status === "pending" && (
                    <div
                      style={{ display: "flex", gap: 8, alignItems: "center" }}
                    >
                      <input
                        placeholder="Optional note..."
                        value={notes[sub.id] || ""}
                        onChange={(e) =>
                          setNotes((p) => ({ ...p, [sub.id]: e.target.value }))
                        }
                        style={{
                          flex: 1,
                          padding: "8px 12px",
                          border: "1px solid #E5E7EB",
                          borderRadius: 8,
                          fontSize: 13,
                          outline: "none",
                          background: "#F9FAFB",
                        }}
                      />
                      <button
                        onClick={() => review(sub.id, "approve")}
                        style={{
                          padding: "8px 20px",
                          background: "#10B981",
                          color: "white",
                          border: "none",
                          borderRadius: 8,
                          fontWeight: 700,
                          cursor: "pointer",
                          fontSize: 13,
                        }}
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => review(sub.id, "reject")}
                        style={{
                          padding: "8px 20px",
                          background: "#DC2626",
                          color: "white",
                          border: "none",
                          borderRadius: 8,
                          fontWeight: 700,
                          cursor: "pointer",
                          fontSize: 13,
                        }}
                      >
                        ✗ Reject
                      </button>
                    </div>
                  )}

                  {sub.status !== "pending" && sub.admin_note && (
                    <div
                      style={{ color: "#6B7280", fontSize: 13, marginTop: 8 }}
                    >
                      Note: {sub.admin_note}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STATS */}
        {tab === "stats" && stats && (
          <div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4,1fr)",
                gap: 16,
                marginBottom: 24,
              }}
            >
              {[
                {
                  label: "Total Queries",
                  value: stats.total_queries,
                  color: "#10B981",
                },
                {
                  label: "Total Submissions",
                  value: stats.submissions.total,
                  color: "#3B82F6",
                },
                {
                  label: "Pending Review",
                  value: stats.submissions.pending,
                  color: "#D97706",
                },
                {
                  label: "Approved",
                  value: stats.submissions.approved,
                  color: "#10B981",
                },
              ].map((card) => (
                <div key={card.label} style={s.card}>
                  <div
                    style={{
                      fontSize: 11,
                      color: "#6B7280",
                      fontWeight: 700,
                      marginBottom: 8,
                    }}
                  >
                    {card.label}
                  </div>
                  <div
                    style={{ fontSize: 30, fontWeight: 900, color: card.color }}
                  >
                    {card.value}
                  </div>
                </div>
              ))}
            </div>

            <div style={s.card}>
              <div style={{ fontWeight: 700, marginBottom: 16, fontSize: 14 }}>
                Top searched brands
              </div>
              {stats.top_brands.map((b, i) => (
                <div
                  key={b.brand}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    marginBottom: 10,
                  }}
                >
                  <span style={{ color: "#9CA3AF", width: 20, fontSize: 12 }}>
                    {i + 1}
                  </span>
                  <span
                    style={{
                      flex: 1,
                      fontWeight: 600,
                      textTransform: "capitalize",
                    }}
                  >
                    {b.brand}
                  </span>
                  <div
                    style={{
                      width: `${Math.round((b.count / stats.top_brands[0].count) * 180)}px`,
                      height: 8,
                      background: "#10B981",
                      borderRadius: 4,
                      minWidth: 4,
                    }}
                  />
                  <span
                    style={{
                      color: "#6B7280",
                      fontSize: 13,
                      width: 40,
                      textAlign: "right",
                    }}
                  >
                    {b.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* QUERIES */}
        {tab === "queries" && (
          <div>
            <div style={{ marginBottom: 14, color: "#6B7280", fontSize: 13 }}>
              Last 100 user queries every check including ones without a user
              price
            </div>
            <div style={{ ...s.card, padding: 0, overflow: "hidden" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: 13,
                }}
              >
                <thead>
                  <tr
                    style={{
                      background: "#F9FAFB",
                      borderBottom: "1px solid #E5E7EB",
                    }}
                  >
                    {[
                      "Time",
                      "Brand",
                      "Model",
                      "Year",
                      "Mileage",
                      "Predicted",
                      "User Price",
                      "Segment",
                      "KNN",
                    ].map((h) => (
                      <th
                        key={h}
                        style={{
                          padding: "10px 14px",
                          textAlign: "left",
                          fontWeight: 700,
                          color: "#6B7280",
                          fontSize: 11,
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {queries.map((q, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #F3F4F6" }}>
                      <td
                        style={{
                          padding: "9px 14px",
                          color: "#9CA3AF",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {String(q.timestamp || "").slice(0, 16)}
                      </td>
                      <td
                        style={{
                          padding: "9px 14px",
                          fontWeight: 600,
                          textTransform: "capitalize",
                        }}
                      >
                        {String(q.brand || "")}
                      </td>
                      <td style={{ padding: "9px 14px", color: "#374151" }}>
                        {String(q.model || "—")}
                      </td>
                      <td style={{ padding: "9px 14px" }}>
                        {String(q.year || "")}
                      </td>
                      <td style={{ padding: "9px 14px", color: "#6B7280" }}>
                        {q.mileage_km
                          ? Number(q.mileage_km).toLocaleString()
                          : "—"}
                      </td>
                      <td
                        style={{
                          padding: "9px 14px",
                          fontWeight: 700,
                          color: "#10B981",
                        }}
                      >
                        {q.predicted_price
                          ? fmt(Number(q.predicted_price))
                          : "—"}
                      </td>
                      <td style={{ padding: "9px 14px" }}>
                        {q.user_price ? fmt(Number(q.user_price)) : "—"}
                      </td>
                      <td style={{ padding: "9px 14px" }}>
                        <span
                          style={{
                            background:
                              q.segment === "mid" ? "#EFF6FF" : "#F0FDF4",
                            color: q.segment === "mid" ? "#3B82F6" : "#10B981",
                            padding: "2px 8px",
                            borderRadius: 20,
                            fontSize: 11,
                            fontWeight: 700,
                          }}
                        >
                          {String(q.segment || "")}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "9px 14px",
                          color: q.knn_price ? "#10B981" : "#9CA3AF",
                          fontSize: 12,
                        }}
                      >
                        {q.knn_price
                          ? `${Number(q.knn_price).toLocaleString()} DT`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {queries.length === 0 && !loading && (
                <div
                  style={{ textAlign: "center", padding: 60, color: "#9CA3AF" }}
                >
                  No queries yet.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
