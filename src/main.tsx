import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Item = {
  id: string;
  title: string;
  kind: string;
  address: string;
  neighborhood: string;
  distance: string;
  status: "scheduled" | "heard" | "deferred" | "continued" | "approved" | "denied" | "closed";
  date: string;
  x: number;
  y: number;
  confidence: number;
  bbl?: string | null;
  geo_confidence?: number;
  longitude?: number | null;
  latitude?: number | null;
  excerpt: string;
  source: string;
};

const fallbackItems: Item[] = [
  {
    id: "east-midtown", title: "East Midtown Special District", kind: "Land use", address: "350 Madison Avenue", neighborhood: "Midtown East", distance: "0.4 mi from your saved place", status: "heard", date: "September 12, 2026", x: 57, y: 26, confidence: 96,
    excerpt: "The application seeks a modification to facilitate commercial redevelopment within the East Midtown Subdistrict.", source: "CB6 Land Use Committee agenda"
  },
  {
    id: "first-ave", title: "First Avenue Street Safety Plan", kind: "Transportation", address: "First Avenue & East 34th Street", neighborhood: "Murray Hill", distance: "0.8 mi from your saved place", status: "scheduled", date: "September 18, 2026", x: 64, y: 50, confidence: 93,
    excerpt: "DOT will present a proposed safety treatment for the First Avenue corridor and invite public comment.", source: "CB6 Transportation Committee agenda"
  },
  {
    id: "liquor", title: "New liquor license: East 27th Street", kind: "Licensing", address: "213 East 27th Street", neighborhood: "Kips Bay", distance: "0.2 mi from your saved place", status: "deferred", date: "August 20, 2026", x: 46, y: 62, confidence: 99,
    excerpt: "Application for an on-premises liquor license was laid over pending an amended operations plan.", source: "CB6 Business Affairs Committee minutes"
  },
  {
    id: "waterside", title: "Waterside Plaza site plan", kind: "Development", address: "25 Waterside Plaza", neighborhood: "Tudor City", distance: "0.6 mi from your saved place", status: "approved", date: "July 30, 2026", x: 77, y: 41, confidence: 91,
    excerpt: "The committee voted to support the revised site plan subject to the stated public-space conditions.", source: "CB6 full board resolution"
  }
];

const lifecycle = ["Scheduled", "Heard", "Deferred", "Decision"];
const docs = ["Committee agenda", "Applicant materials", "Meeting minutes", "Public testimony"];

type ApiItem = Pick<Item, "id" | "title" | "address" | "status" | "confidence" | "bbl" | "geo_confidence" | "longitude" | "latitude"> & { category: string; evidence: string; lifecycle?: { date: string }[] };

function MapCanvas({ items, selected, onSelect }: { items: Item[]; selected: Item; onSelect: (item: Item) => void }) {
  const located = items.filter((item): item is Item & { longitude: number; latitude: number } => item.longitude !== null && item.longitude !== undefined && item.latitude !== null && item.latitude !== undefined);
  const longitude = located.map((item) => item.longitude);
  const latitude = located.map((item) => item.latitude);
  const bounds = { west: Math.min(...longitude), east: Math.max(...longitude), south: Math.min(...latitude), north: Math.max(...latitude) };
  const position = (item: Item) => {
    if (item.longitude === null || item.longitude === undefined || item.latitude === null || item.latitude === undefined || located.length < 2) return { left: `${item.x}%`, top: `${item.y}%` };
    const width = bounds.east - bounds.west || 1;
    const height = bounds.north - bounds.south || 1;
    return { left: `${15 + 70 * (item.longitude - bounds.west) / width}%`, top: `${18 + 64 * (bounds.north - item.latitude) / height}%` };
  };
  return <section className="map" aria-label="Community Board 6 decision map">
    <div className="map-controls"><button aria-label="Zoom in">+</button><button aria-label="Zoom out">−</button><button aria-label="Recenter map">◎</button></div>
    <div className="map-key"><span><i className="dot" /> Decision</span><span><i className="box" /> Parcel</span><span><i className="ring" /> Saved place</span></div>
    <div className="river east">EAST RIVER</div><div className="river west">EAST RIVER</div>
    <div className="district">MANHATTAN<br /><strong>COMMUNITY BOARD 6</strong></div>
    <div className="streets" />
    {items.map((item, index) => <button key={item.id} className={`pin ${selected.id === item.id ? "active" : ""}`} style={position(item)} onClick={() => onSelect(item)} aria-label={`Show ${item.title}`}><span>{index + 1}</span></button>)}
    <div className="saved-pin" style={{ left: "54%", top: "57%" }} title="Saved place" />
    <div className="scale">0 <b /> 500 <b /> 1000 ft</div>
  </section>;
}

function Detail({ item }: { item: Item }) {
  const stage = item.status === "scheduled" ? 0 : item.status === "heard" ? 1 : item.status === "deferred" || item.status === "continued" ? 2 : 3;
  return <aside className="detail">
    <div className="kicker">{item.kind} · resolver confidence {item.confidence}%</div>
    <h2>{item.title}</h2>
    <p className="case">CB6 item · {item.id.toUpperCase()}</p>
    <div className="lifecycle">{lifecycle.map((label, index) => <div className={index <= stage ? "done" : ""} key={label}><i>{index < stage ? "✓" : index + 1}</i><b>{label}</b></div>)}</div>
    <dl><div><dt>Near</dt><dd>{item.address}<br />{item.neighborhood}<br /><em>{item.distance}</em></dd></div>{item.bbl && <div><dt>Parcel</dt><dd>{item.bbl}<br /><em>geo confidence {item.geo_confidence}%</em></dd></div>}<div><dt>Next signal</dt><dd>{item.date}</dd></div></dl>
    <div className="excerpt"><span>Evidence excerpt</span><p>“{item.excerpt}”</p><small>— {item.source}</small></div>
    <button className="source-button">Open source evidence <span>↗</span></button>
  </aside>;
}

function App() {
  const [items, setItems] = useState(fallbackItems);
  const [selected, setSelected] = useState(fallbackItems[0]);
  const [saved, setSaved] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [address, setAddress] = useState("");
  const [saveError, setSaveError] = useState("");
  const [alertCount, setAlertCount] = useState(0);
  const [showMethod, setShowMethod] = useState(false);
  const endpoint = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
  useEffect(() => {
    fetch(`${endpoint}/items`)
      .then((response) => response.ok ? response.json() : Promise.reject(response.statusText))
      .then((records: ApiItem[]) => {
        if (!records.length) return;
        const hydrated = records.map((record, index) => {
          const presentation = fallbackItems.find((item) => item.address === record.address) ?? fallbackItems[index % fallbackItems.length];
          return { ...presentation, ...record, kind: record.category.replace("_", " "), date: record.lifecycle?.at(-1)?.date ?? presentation.date, excerpt: record.evidence, source: "CB6 source record" };
        });
        setItems(hydrated);
        setSelected(hydrated[0]);
      })
      .catch(() => undefined);
    fetch(`${endpoint}/alerts`).then((response) => response.ok ? response.json() : []).then((alerts: unknown[]) => setAlertCount(alerts.length)).catch(() => undefined);
  }, [endpoint]);
  async function saveAddress() {
    setSaveError("");
    try {
      const response = await fetch(`${endpoint}/saved-places`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ address, radius_meters: 800 }) });
      if (!response.ok) throw new Error("Save failed");
      const sync = await fetch(`${endpoint}/monitor/sync`, { method: "POST" });
      const result = await sync.json() as { alerts_created: number };
      setAlertCount((count) => count + result.alerts_created);
      setSaved(true); setSaveOpen(false); setAddress("");
    } catch {
      setSaveError("The monitor is unavailable. Start the API and try again.");
    }
  }
  return <main>
    <header><a className="logo" href="#top">QUORUM</a><span className="strap">Civic decision intelligence</span><nav><a className="selected" href="#map">Map</a><a href="#alerts">Alerts {alertCount > 0 && <sup>{alertCount}</sup>}</a><button onClick={() => setShowMethod(!showMethod)}>Methodology</button></nav><button className="cta" onClick={() => setSaveOpen(true)}>{saved ? "ADDRESS SAVED" : "SAVE AN ADDRESS"}</button></header>
    {saveOpen && <div className="modal-backdrop" role="presentation"><form className="save-modal" onSubmit={(event) => { event.preventDefault(); void saveAddress(); }}><button className="close" type="button" onClick={() => setSaveOpen(false)} aria-label="Close">×</button><h2>WATCH THIS PLACE</h2><p>We alert only when a high-confidence civic item reaches a decision state.</p><label htmlFor="address">Street address</label><input id="address" value={address} onChange={(event) => setAddress(event.target.value)} placeholder="90 Park Avenue" minLength={5} required autoFocus />{saveError && <small className="error">{saveError}</small>}<button className="cta" type="submit">SAVE + MONITOR</button></form></div>}
    {showMethod && <section className="method" role="status"><strong>MODEL STATUS: SILVER BASELINE</strong><span>The entity linker learns from recurring official DOB job IDs, not human-adjudicated labels. Its score ranks review candidates only; alerts remain evidence- and rule-gated.</span></section>}
    <section className="hero" id="top"><h1>WHAT’S DECIDING</h1><p>NEAR YOUR<br />ADDRESS</p></section>
    <section className="workspace" id="map"><Detail item={selected} /><MapCanvas items={items} selected={selected} onSelect={setSelected} /><aside className="manifesto"><h2>DECISIONS HAPPEN NEAR YOU.</h2><p>Every marker is a public item entering a decision point in Community Board 6.</p><div><b>01 / Linked</b><p>Case IDs, named projects, and addresses are resolved into one civic record.</p></div><div><b>02 / Explained</b><p>Open the evidence trail before you decide whether it matters.</p></div><div><b>03 / Watched</b><p>Saved places receive a signal only when an item actually changes state.</p></div><button className="outline" onClick={() => setSaveOpen(true)}>Watch this place →</button></aside></section>
    <section className="evidence" id="alerts"><div className="rail-intro"><h2>Evidence rail</h2><p>Documents and records that support every decision.</p><a href="#map">Back to map →</a></div>{docs.map((doc, index) => <button className="doc" key={doc} onClick={() => setSelected(items[index % items.length])}><span>▱</span><b>{doc}</b><strong>{index === 0 ? selected.source : `${selected.title} · record ${index + 1}`}</strong><small>{selected.date} · PDF</small></button>)}<button className="all-docs">See all<br />documents →</button></section>
    <footer>QUORUM / MANHATTAN CB6 / CURATED DEMO SNAPSHOT · All records are public-source civic data.</footer>
  </main>;
}

createRoot(document.getElementById("root")!).render(<App />);
