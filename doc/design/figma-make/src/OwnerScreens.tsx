import { useMemo, useState, type ReactNode } from "react";

type OwnerId = "login" | "dashboard" | "bookings" | "services" | "therapists" | "waitlist-owner" | "settings" | "session-error" | "owner-flows";
type OIconName = "leaf" | "dashboard" | "calendar" | "services" | "user" | "clock" | "settings" | "menu" | "warning" | "close" | "download" | "printer" | "check";

function OIcon({ name, size = 20 }: { name: OIconName; size?: number }) {
  const p: Record<OIconName, ReactNode> = {
    leaf: <><path className="fill" d="M21 4C12 5 6 10 5 20c6 2 13-1 16-7 1-4 1-7 0-9Z"/><path d="M6 20c4-5 8-8 14-12"/></>,
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4m8-4v4M3 10h18"/></>,
    services: <><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="8" cy="7" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="17" r="2"/></>,
    user: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/></>,
    menu: <path d="M4 7h16M4 12h16M4 17h16"/>,
    warning: <><path d="M12 3 2.5 20h19L12 3Z"/><path d="M12 9v5m0 3h.01"/></>,
    close: <path d="M6 6l12 12M18 6 6 18"/>,
    download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 20h14"/></>,
    printer: <><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v7H6z"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
  };
  return <svg className="o-icon" aria-hidden="true" viewBox="0 0 24 24" width={size} height={size} fill="none">{p[name]}</svg>;
}

const nav = [
  ["dashboard", "Dashboard", "dashboard"], ["bookings", "Bookings", "calendar"],
  ["services", "Services & add-ons", "services"], ["therapists", "Therapists & hours", "user"],
  ["waitlist-owner", "Waitlist", "clock"], ["settings", "Studio settings", "settings"],
] as const;

const ownerStates: Record<OwnerId, {value:string;label:string}[]> = {
  login: ["empty","missing","wrong","locked","submitting"].map(v => ({value:v,label:v === "empty" ? "Empty" : v === "missing" ? "Missing fields" : v === "wrong" ? "Wrong login" : v === "locked" ? "Locked" : "Submitting"})),
  dashboard: [
    {value:"default",label:"Default"},{value:"loading",label:"Loading"},{value:"empty",label:"Empty day / no data"},
    {value:"error-network",label:"Page error · no response"},{value:"error-server",label:"Page error · server"},
    {value:"menu-open",label:"Mobile menu open"},
  ],
  bookings: [
    {value:"day",label:"Day view"},{value:"week",label:"Week view"},{value:"list",label:"List view"},{value:"empty",label:"Empty"},
    {value:"loading",label:"Loading"},{value:"filter-error",label:"Range error"},{value:"load-error",label:"Page load error"},
    {value:"detail",label:"Booking detail"},{value:"detail-ben",label:"Repeat no-show detail"},{value:"detail-late",label:"Late cancellation detail"},
    {value:"status-error",label:"Status error"},{value:"status-saved",label:"Status saved"},
    {value:"items",label:"Adjust items"},{value:"items-error",label:"Items error"},{value:"items-saved",label:"Items saved"},
    {value:"receipt-ready",label:"Done · receipt enabled"},{value:"receipt-error",label:"Receipt error"},
    {value:"receipt-sent",label:"Receipt sent"},{value:"detail-loading",label:"Detail loading"},{value:"detail-error",label:"Detail not found"},
    {value:"add",label:"Add phone booking"},{value:"add-placeholder",label:"Phone booking · pick services"},{value:"add-loading",label:"Phone booking · loading times"},{value:"add-empty",label:"Phone booking · no times"},
    {value:"add-error",label:"Phone booking · error"},{value:"add-success",label:"Phone booking · success"},
  ],
  services: [
    {value:"default",label:"Default"},{value:"loading",label:"Loading"},{value:"load-error",label:"Page load error"},
    {value:"add",label:"Add service"},{value:"edit",label:"Edit service"},{value:"service-error",label:"Service validation"},
    {value:"addon",label:"Add add-on"},{value:"addon-edit",label:"Edit add-on"},{value:"addon-error",label:"Add-on validation"},
    {value:"toast-hidden",label:"Visibility toast"},
  ],
  therapists: [
    {value:"default",label:"Default"},{value:"empty",label:"Empty days off"},{value:"loading",label:"Loading"},{value:"load-error",label:"Page load error"},
    {value:"add",label:"Add therapist"},{value:"edit",label:"Edit therapist"},{value:"therapist-error",label:"Therapist validation"},
    {value:"hours",label:"Weekly hours"},{value:"hours-special",label:"Split-shift hint"},{value:"hours-error",label:"Hours validation"},
    {value:"dayoff",label:"Add day off"},{value:"dayoff-error",label:"Day-off validation"},
  ],
  "waitlist-owner": [
    {value:"default",label:"Default"},{value:"empty-all",label:"Empty · all upcoming"},{value:"empty-day",label:"Empty · day"},
    {value:"loading",label:"Loading"},{value:"load-error",label:"Page load error"},{value:"removed",label:"Removed toast"},
  ],
  settings: [
    {value:"default",label:"Default"},{value:"validation",label:"Validation errors"},{value:"saved",label:"Saved toast"},
    {value:"loading",label:"Loading"},{value:"load-error",label:"Page load error"},
  ],
  "session-error": [{value:"network",label:"Session check · no response"},{value:"server",label:"Session check · server error"}],
  "owner-flows": [{value:"all",label:"All flows"}],
};

function OStatus({tone,children,outlined=false}:{tone:string;children:ReactNode;outlined?:boolean}) {
  return <span className={`badge badge--${tone} ${outlined ? "badge--outlined":""}`}><span className="badge__dot"/>{children}</span>;
}

function OwnerShell({page,state,children}:{page:OwnerId;state:string;children:ReactNode}) {
  const current = nav.find(n => n[0] === page)?.[1] ?? "Dashboard";
  return <div className="o-shell">
    <aside className="o-sidebar">
      <div className="o-logo"><OIcon name="leaf" size={28}/><strong>Slotwise</strong></div>
      <nav aria-label="Owner menu">{nav.map(([id,label,icon]) => <button key={id} className={page===id ? "is-current":""}><OIcon name={icon}/><span>{label}</span></button>)}</nav>
      <div className="o-sidebar__bottom"><button className="button button--text"><span>Classic look</span></button><button className="button button--text">Log out</button></div>
    </aside>
    <header className="o-mobile-head"><div className="o-logo"><OIcon name="leaf" size={26}/><strong>Slotwise</strong></div><div><strong>{current}</strong><button className="icon-button" aria-label="Owner menu"><OIcon name="menu"/></button></div></header>
    {state==="menu-open" && <div className="o-mobile-menu" aria-label="Owner menu">{nav.map(([id,label,icon]) => <button key={id} className={page===id ? "is-current":""}><OIcon name={icon}/>{label}</button>)}<button>Classic look</button><button>Log out</button></div>}
    <div className="o-main">{children}</div>
  </div>;
}

function PageHead({title,subtitle,children}:{title:string;subtitle?:string;children?:ReactNode}) {
  return <header className="o-page-head"><div><h1>{title}</h1>{subtitle&&<p>{subtitle}</p>}</div>{children&&<div className="o-page-actions">{children}</div>}</header>;
}

function PageError({server=false,session=false}:{server?:boolean;session?:boolean}) {
  const body = <div className="o-page-error"><span className="o-error-icon"><OIcon name="warning" size={28}/></span><h2>This page couldn't load</h2>
    <p>{server ? "Something went wrong. Please try again." : "Could not reach the server. Please check your connection."}</p>
    <small>Details: {server ? "status 500 · /owner/dashboard" : "no response from the server"} · 14:32</small>
    <h3>What you can try:</h3><ul><li>Wait a moment and try again. On the free hosting plan the server sleeps when nobody uses it and can take up to a minute to wake up.</li><li>Check your internet connection.</li><li>Switch to the Classic look. If only the new look has a problem, the classic one keeps working.</li><li>If it keeps happening, send the details line above to your developer.</li></ul>
    <div><button className="button">Try again</button><button className="button button--ghost">Switch to Classic look</button></div>
  </div>;
  return session ? <main className="o-session-error">{body}</main> : body;
}

function Loading({label="Loading…"}:{label?:string}) {
  return <div className="o-loading"><span className="o-spinner"/><p>{label}</p><div className="skeleton o-loading-block"/></div>;
}

function Toast({children}:{children:ReactNode}) { return <div className="o-toast">{children}</div>; }

function Login({state}:{state:string}) {
  const message = state==="missing" ? "Please enter your email and password." : state==="wrong" ? "Email or password is wrong." : state==="locked" ? "Too many attempts. Try again in 5 minutes." : "";
  return <main className="o-login"><div><article className="o-login-card"><div className="o-logo"><OIcon name="leaf" size={30}/><strong>Slotwise</strong></div><h1>Studio login</h1><p>Sign in to manage bookings, the menu and your team.</p>{message&&<div className="alert alert--danger"><OIcon name="warning"/>{message}</div>}<label className="field"><span>Email</span><input type="email"/></label><label className="field"><span>Password</span><input type="password"/></label><button className="button button--full" disabled={state==="submitting"}>{state==="submitting" ? "Logging in…" : "Log in"}</button></article><a href="#">Back to studio page</a></div></main>;
}

const appointments = [
  ["10:00","Anna Müller","Lena","Deep tissue massage","€82","Confirmed","success"],
  ["11:30","Ben Fischer ⚠","Lena","Back and neck massage","€39","Booked","warning"],
  ["12:00","Priya Shah","Sofia","Classic facial","€68","Awaiting email","info"],
];

function Dashboard({state}:{state:string}) {
  if(state==="loading") return <OwnerShell page="dashboard" state={state}><Loading/></OwnerShell>;
  if(state.startsWith("error")) return <OwnerShell page="dashboard" state={state}><PageError server={state==="error-server"}/></OwnerShell>;
  const empty=state==="empty";
  return <OwnerShell page="dashboard" state={state}><PageHead title="Welcome back, Studio owner" subtitle="Tuesday 13 October 2026"><label className="field o-day-field"><span>Day</span><input type="date" defaultValue="2026-10-13"/></label></PageHead>
    <div className="o-tile-grid o-tile-grid--3"><Metric label="Bookings on this day" value={empty?"0":"6"} note="not counting cancellations"/><Metric label="Expected revenue" value={empty?"€0":"€398"} note="pay at the studio"/><Metric label="Confirmed by customer" value={empty?"–":"67%"} note="via the reminder link"/></div>
    <SectionTitle title="Is it working? (last 30 days)" note="13 Sep – 13 Oct, by appointment date. Goals from the project plan."/>
    <div className="o-tile-grid o-tile-grid--4"><Metric label="No-show rate" value={empty?"–":"3.8%"} note="no-shows ÷ (done + no-shows)" goal={empty?"none":"good"}/><Metric label="Refilled from waitlist" value={empty?"–":"40%"} note="waitlist bookings ÷ cancellations" goal={empty?"none":"bad"}/><Metric label="Booked online" value={empty?"–":"72%"} note="online ÷ all bookings" goal={empty?"none":"online"}/><Metric label="Revenue recovered" value={empty?"–":"€134"} note="through the waitlist" goal={empty?"none":undefined}/></div>
    <SectionTitle title="Appointments on this day"/>{empty?<div className="empty-state">No appointments on this day.</div>:<OwnerTable heads={["Time","Customer","Therapist","Services","Total","Status"]}>{appointments.map(r=><tr key={r[0]}><td>{r[0]}</td><td title={r[1].includes("⚠")?"2 or more no-shows":undefined}>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td className="number">{r[4]}</td><td><OStatus tone={r[6]}>{r[5]}</OStatus></td></tr>)}</OwnerTable>}
    <SectionTitle title="No-shows and late cancellations per week" note="The last 8 weeks. Hover or focus a week for the numbers."/><Chart empty={empty}/>
  </OwnerShell>;
}

function Metric({label,value,note,goal}:{label:string;value:string;note:string;goal?:"good"|"bad"|"online"|"none"}) {
  return <article className="dashboard-tile"><span>{label}</span><strong>{value}</strong><small>{note}</small>{goal&&<span className={`goal goal--${goal==="bad"?"warning":goal==="none"?"neutral":"success"}`}>{goal==="bad"?"▲ Off target · goal ≥ 50%":goal==="none"?"No data yet":goal==="online"?"✓ On target · goal ≥ 60%":"✓ On target · goal < 5%"}</span>}</article>;
}
function SectionTitle({title,note,action}:{title:string;note?:string;action?:ReactNode}) { return <div className="o-section-title"><div><h2>{title}</h2>{note&&<p>{note}</p>}</div>{action}</div>; }
function OwnerTable({heads,children}:{heads:string[];children:ReactNode}) { return <div className="table-scroll o-table"><table><thead><tr>{heads.map((h,i)=><th key={h} className={["Total","Price"].includes(h)?"number":""}>{h}{i===heads.length-1&&h===""?<span className="sr-only">Actions</span>:null}</th>)}</tr></thead><tbody>{children}</tbody></table></div>; }

function Chart({empty}:{empty:boolean}) {
  const a=[2,1,3,1,2,0,1,1], b=[1,2,1,3,2,2,1,2];
  return <div className="o-chart-card"><div className="o-chart-legend"><span><i className="chart-1"/>No-shows</span><span><i className="chart-2"/>Late cancellations</span></div><div className="o-chart"><div className="o-grid-lines">{[0,1,2,3].map(n=><i key={n}/>)}</div>{a.map((v,i)=><button key={i} className="o-chart-week" title={`Week of ${i===7?"5 Oct":"17 Aug"} · No-shows: ${empty?0:v} · Late cancellations: ${empty?0:b[i]}`}><span className="bar bar--1" style={{height:`${empty?0:v*22}px`}}/><span className="bar bar--2" style={{height:`${empty?0:b[i]*22}px`}}/><small>{i===0?"17 Aug":i===7?"5 Oct":`${24+i*7} Aug`}</small></button>)}</div><details><summary>Show as table</summary><OwnerTable heads={["Week of","No-shows","Late cancellations"]}><tr><td>5 Oct</td><td>1</td><td>2</td></tr></OwnerTable></details></div>;
}

function Bookings({state}:{state:string}) {
  if(state==="loading") return <OwnerShell page="bookings" state={state}><Loading/></OwnerShell>;
  if(state==="load-error") return <OwnerShell page="bookings" state={state}><PageError/></OwnerShell>;
  const view=["week","list"].includes(state)?state:"day";
  const dialog=state.startsWith("detail")||["status-error","status-saved","items","items-error","items-saved","receipt-ready","receipt-error","receipt-sent","add-success"].includes(state);
  const add=state.startsWith("add")&&state!=="add-success";
  return <OwnerShell page="bookings" state={state}><PageHead title="Bookings"><button className="button button--ghost button--small"><OIcon name="download"/>Export CSV</button><button className="button button--small">Add booking</button></PageHead>
    <BookingToolbar view={view}/>{state==="filter-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Please choose a range of up to 3 months.</div>}
    {view==="day"&&<DayView empty={state==="empty"}/>} {view==="week"&&<WeekView/>} {view==="list"&&<BookingList empty={state==="empty"}/>}
    {dialog&&<BookingDialog state={state}/>} {add&&<PhoneDialog state={state}/>} {state==="add-success"&&<Toast>Booked 10:00 with Lena; confirmation emailed</Toast>}
  </OwnerShell>;
}

function BookingToolbar({view}:{view:string}) {
  return <div className="o-booking-tools"><div className="o-tool-row"><div className="segmented" aria-label="View">{["Day","Week","List"].map(x=><button key={x} className={view===x.toLowerCase()?"is-selected":""}>{x}</button>)}</div><div className="button-pair"><button className="icon-button" aria-label="Previous">‹</button><button className="button button--ghost button--small">Today</button><button className="icon-button" aria-label="Next">›</button></div><strong>{view==="week"?"Mon 12 Oct – Sun 18 Oct":"Tuesday 13 October 2026"}</strong></div><div className="o-tool-row"><select aria-label="Therapist"><option>All therapists</option><option>Lena</option><option>Sofia</option></select><select aria-label="Status"><option>All statuses</option><option>Awaiting email</option><option>Booked</option><option>Confirmed</option><option>Done</option><option>No-show</option><option>Cancelled</option><option>Not confirmed</option></select><label className="o-search"><span className="sr-only">Search</span><input placeholder="Search name, email or phone"/></label></div></div>;
}
function CalendarCard({time,name="Anna Müller",service="Deep tissue massage",tone="confirmed",extra}:{time:string;name?:string;service?:string;tone?:string;extra?:string}) {
  return <button className={`o-calendar-card o-calendar-card--${tone}`}><strong>{time}</strong><span>{name}</span><small>{service}</small>{extra&&<em>{extra}</em>}</button>;
}
function DayView({empty}:{empty:boolean}) { return <div className="o-day-columns">{["Lena","Sofia"].map((n,i)=><section key={n}><h3>{n}</h3>{empty?<p className="notice">No bookings</p>:i===0?<><CalendarCard time="10:00 · 75 min"/><CalendarCard time="11:30 · 30 min" name="Ben Fischer ⚠" service="Back and neck massage" tone="booked"/></>:<CalendarCard time="12:00 · 55 min" name="Priya Shah" service="Classic facial" tone="awaiting" extra="Awaiting email"/>}</section>)}</div>; }
function WeekView(){return <div className="o-week">{["Mon 12 Oct","Tue 13 Oct","Wed 14 Oct","Thu 15 Oct","Fri 16 Oct","Sat 17 Oct","Sun 18 Oct"].map((d,i)=><section className={i===1?"is-today":""} key={d}><h3>{d}</h3>{i%3===0?<p className="notice">No bookings</p>:<CalendarCard time={i===1?"10:00":"11:00"} name={i===1?"Anna Müller":"Mia Wagner"} extra={i===1?"Lena":"Sofia"}/>}</section>)}</div>}
function BookingList({empty}:{empty:boolean}) { return empty?<div className="empty-state">No bookings in this range.</div>:<OwnerTable heads={["Date","Time","Customer","Therapist","Services","Total","Status"]}><tr tabIndex={0}><td>Tue 13 Oct</td><td>10:00</td><td>Anna Müller</td><td>Lena</td><td>Deep tissue massage</td><td className="number">€82</td><td><OStatus tone="success">Confirmed</OStatus></td></tr></OwnerTable>; }

function Dialog({title,children}:{title:string;children:ReactNode}) { return <div className="o-dialog-layer"><div className="o-dialog-backdrop"/><aside className="dialog-panel o-dialog"><header><h2>{title}</h2><button className="icon-button" aria-label="Close"><OIcon name="close"/></button></header><div className="dialog-panel__body">{children}</div></aside></div>; }
function BookingDialog({state}:{state:string}) {
  if(state==="detail-loading") return <Dialog title="Booking details"><Loading/></Dialog>;
  if(state==="detail-error") return <Dialog title="Booking details"><div className="alert alert--danger"><OIcon name="warning"/>Booking not found.</div></Dialog>;
  const ben=state==="detail-ben", editing=state==="items"||state==="items-error", sent=state==="receipt-sent", done=["receipt-ready","receipt-error","receipt-sent","status-saved","items-saved"].includes(state), late=state==="detail-late";
  return <Dialog title={ben?"Ben Fischer":"Anna Müller"}><div className="badge-grid"><OStatus tone="success" outlined={done}>{done?"Done":"Confirmed"}</OStatus>{late&&<OStatus tone="danger">Late cancellation</OStatus>}</div>
    <dl className="facts facts--stack"><div><dt>When</dt><dd>Tuesday 13 October 2026, 10:00 (75 min)</dd></div><div><dt>Therapist</dt><dd>Lena</dd></div><div><dt>Email</dt><dd><a href="mailto:anna.mueller@example.com">anna.mueller@example.com</a></dd></div><div><dt>Phone</dt><dd><a href="tel:+4915100000001">+49 151 0000 0001</a></dd></div><div><dt>No-shows</dt><dd className={ben?"o-danger":""}>{ben?"2 ⚠ repeat no-show":"0"}</dd></div><div><dt>Source</dt><dd>{state==="add-success"?"phone":"online"}</dd></div><div><dt>Note</dt><dd>Please focus on my shoulders.</dd></div></dl>
    <section className="o-dialog-section"><h3>Status</h3><div className="o-inline-form"><select defaultValue={done?"Done":"Confirmed"}><option>Awaiting email</option><option>Not confirmed</option><option>Booked</option><option>Confirmed</option><option>Done</option><option>No-show</option><option>Cancelled</option></select><button className="button button--small" disabled={sent}>Save status</button></div><small>Done and no-show can be set once the appointment has started.</small>{state==="status-error"&&<div className="alert alert--danger"><OIcon name="warning"/>This status change is not allowed.</div>}</section>
    <section className="o-dialog-section">{editing?<ItemsEditor error={state==="items-error"}/>:<><h3>Items</h3><dl className="item-lines"><div><dt>Deep tissue massage</dt><dd>€70</dd></div><div className="item-lines__addon"><dt>+ Hot stones</dt><dd>€12</dd></div><div className="item-lines__total"><dt>Total</dt><dd>€82</dd></div></dl>{!sent&&<button className="button button--ghost button--small">Adjust items</button>}</>}</section>
    <section className="o-dialog-section"><h3>Receipt</h3>{state==="receipt-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Only bookings marked done can get a receipt.</div>}{sent?<><p><strong>Receipt IW-2026-0042 sent</strong> · <a href="#">Print receipt</a></p><button className="button button--ghost">Resend receipt</button></>:<><button className="button" disabled={!done}>Send receipt</button>{!done&&<small>Mark the booking done to send a receipt.</small>}</>}</section>
    {sent&&<Toast>Receipt IW-2026-0042 sent</Toast>}{state==="status-saved"&&<Toast>Status: Done</Toast>}{state==="items-saved"&&<Toast>Items saved</Toast>}
  </Dialog>;
}
function ItemsEditor({error}:{error:boolean}) { return <div className="o-items-editor"><h3>Adjust items</h3><p>Lines done on the day, e.g. extra time or a product sold. Prices in EUR.</p>{error&&<div className="alert alert--danger"><OIcon name="warning"/>Please check the item lines.</div>}{["Deep tissue massage","Hot stones"].map((n,i)=><div className="o-item-edit" key={n}><label className="field"><span>Type</span><select><option>{i?"add-on":"service"}</option><option>extra</option></select></label><label className="field"><span>Name</span><input defaultValue={n}/></label><label className="field"><span>Price EUR</span><input type="number" defaultValue={i?12:70}/></label><label className="field"><span>Quantity</span><input type="number" defaultValue="1"/></label><button className="icon-button" aria-label={`Remove ${n}`}><OIcon name="close"/></button></div>)}<div className="button-pair"><button className="button button--ghost">+ Add line</button><button className="button">Save items</button><button className="button button--ghost">Cancel</button></div></div>; }
function PhoneDialog({state}:{state:string}) { return <Dialog title="Add phone booking"><div className="o-dialog-section"><h3>Services</h3>{["Deep tissue massage · 60 min · €70","+ Hot stones (€12)"].map((x,i)=><label className="check-row" key={x}><input type="checkbox" defaultChecked={state!=="add-placeholder"&&i===0}/>{x}</label>)}</div><div className="o-form-grid"><label className="field"><span>Therapist</span><select><option>No preference</option><option>Lena</option></select></label><label className="field"><span>Day</span><input type="date" defaultValue="2026-10-13"/></label><label className="field o-full"><span>Time</span><select><option>{state==="add-placeholder"?"Pick services and a day":state==="add-loading"?"Loading…":state==="add-empty"?"No free times":"10:00 · Lena"}</option></select></label><label className="field"><span>First name</span><input defaultValue="Anna"/></label><label className="field"><span>Last name</span><input defaultValue="Müller"/></label><label className="field"><span>Email</span><input aria-invalid={state==="add-error"||undefined} defaultValue={state==="add-error"?"anna@":"anna.mueller@example.com"}/></label><label className="field"><span>Phone</span><input defaultValue="+49 151 0000 0001"/></label><label className="field o-full"><span>Note (optional)</span><textarea/></label></div>{state==="add-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Please enter a valid email address.</div>}<button className="button button--full">Save booking</button></Dialog>; }

function Services({state}:{state:string}) {
  if(state==="loading") return <OwnerShell page="services" state={state}><Loading/></OwnerShell>;
  if(state==="load-error") return <OwnerShell page="services" state={state}><PageError server/></OwnerShell>;
  const editor=["add","edit","service-error"].includes(state), addon=state.startsWith("addon");
  return <OwnerShell page="services" state={state}><PageHead title="Services & add-ons"><button className="button button--small">Add service</button></PageHead><p className="o-lead">Inactive services are hidden from customers. Existing bookings always keep the name and price they were booked with.</p><ServiceTable/>
    {editor&&<ServiceEditor state={state}/>} {addon&&<AddonEditor state={state}/>} {state==="toast-hidden"&&<Toast>Deep tissue massage is now hidden</Toast>}
  </OwnerShell>;
}
function ServiceTable(){return <OwnerTable heads={["Category","Service","Duration","Price","Buffer after","Active",""]}><tr><td>Massages</td><td><strong>Deep tissue massage</strong><small>Firm pressure for tight muscles and knots.</small></td><td>60 min</td><td className="number">€70</td><td>10 min</td><td><label className="check-row"><input type="checkbox" defaultChecked/>Yes<span className="sr-only">Deep tissue massage active</span></label></td><td><div className="button-pair"><button className="button button--ghost button--small">Edit</button><button className="button button--ghost button--small">+ Add-on</button></div></td></tr><tr className="o-addon-row"><td/><td>+ Hot stones</td><td>+15 min</td><td className="number">+€12</td><td/><td>Yes</td><td><button className="button button--ghost button--small">Edit add-on</button></td></tr><tr className="is-inactive"><td>Facials</td><td><strong>Express facial</strong><small>A quick refresh for busy days.</small></td><td>30 min</td><td className="number">€39</td><td>0 min</td><td>No</td><td><button className="button button--ghost button--small">Edit</button></td></tr></OwnerTable>}
function ServiceEditor({state}:{state:string}) { const edit=state!=="add"; return <Dialog title={edit?"Edit Deep tissue massage":"Add service"}>{state==="service-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Duration must be 15 to 240 minutes in steps of 15.</div>}<div className="o-form-grid"><label className="field o-full"><span>Category</span><select><option>Massages</option><option>Facials</option><option>Reflexology</option></select></label><label className="field o-full"><span>Name</span><input defaultValue={edit?"Deep tissue massage":""}/></label><label className="field o-full"><span>One-line description</span><input defaultValue={edit?"Firm pressure for tight muscles and knots.":""}/></label><label className="field"><span>Name (German)</span><input/><small>Shown to German-speaking customers; leave empty to use the English name.</small></label><label className="field"><span>Description (German)</span><textarea/></label><label className="field"><span>Duration (minutes)</span><input aria-invalid={state==="service-error"||undefined} type="number" defaultValue="60"/><small>15 to 240, steps of 15</small></label><label className="field"><span>Price (EUR)</span><input type="number" defaultValue="70"/></label><label className="field"><span>Cleanup buffer after (minutes)</span><input type="number" defaultValue="10"/><small>0 to 30</small></label><label className="check-row o-full"><input type="checkbox" defaultChecked/>Shown to customers</label></div><button className="button button--full">Save</button></Dialog>; }
function AddonEditor({state}:{state:string}) { const edit=state==="addon-edit"; return <Dialog title={edit?"Edit add-on: Hot stones":"Add-on for Deep tissue massage"}>{state==="addon-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Extra time must be 0 to 60 minutes.</div>}<div className="o-form-grid"><label className="field o-full"><span>Name</span><input defaultValue={edit?"Hot stones":""}/></label><label className="field o-full"><span>Name (German)</span><input/><small>Leave empty to use the English name.</small></label><label className="field"><span>Extra time (minutes)</span><input aria-invalid={state==="addon-error"||undefined} type="number" defaultValue="15"/><small>0 to 60</small></label><label className="field"><span>Price (EUR)</span><input type="number" defaultValue="12"/></label><label className="check-row o-full"><input type="checkbox" defaultChecked/>Shown to customers</label></div><button className="button button--full">Save</button></Dialog>; }

function Therapists({state}:{state:string}) {
  if(state==="loading") return <OwnerShell page="therapists" state={state}><Loading/></OwnerShell>;
  if(state==="load-error") return <OwnerShell page="therapists" state={state}><PageError/></OwnerShell>;
  return <OwnerShell page="therapists" state={state}><PageHead title="Therapists & hours"><button className="button button--small">Add therapist</button></PageHead><TherapistTable/><SectionTitle title="Days off" action={<button className="button button--small">Add day off</button>}/>{state==="empty"?<div className="empty-state">No upcoming days off.</div>:<OwnerTable heads={["Date","Who","Reason",""]}><tr><td>Thu 24 Dec 2026</td><td>Whole studio closed</td><td>Christmas Eve</td><td><button className="button button--ghost button--small">Remove</button></td></tr><tr><td>Mon 19 Oct 2026</td><td>Sofia</td><td>Holiday</td><td><button className="button button--ghost button--small">Remove</button></td></tr></OwnerTable>}
    {["add","edit","therapist-error"].includes(state)&&<TherapistEditor state={state}/>} {state.startsWith("hours")&&<HoursEditor state={state}/>} {state.startsWith("dayoff")&&<DayOff state={state}/>}
  </OwnerShell>;
}
function TherapistTable(){return <OwnerTable heads={["Name","Services offered","Weekly hours","Active",""]}><tr><td><strong>Lena</strong><small>Massages and foot reflexology</small></td><td>Relaxation massage, Deep tissue massage, Back and neck massage, Foot reflexology</td><td>Mon 10:00–19:00 · Tue 10:00–19:00 · Wed 10:00–19:00 · Thu 10:00–19:00 · Fri 10:00–19:00 · Sat 10:00–14:00</td><td>Yes</td><td><div className="button-pair"><button className="button button--ghost button--small">Edit</button><button className="button button--ghost button--small">Hours</button></div></td></tr><tr><td><strong>Sofia</strong><small>Facials and relaxation massage</small></td><td>Relaxation massage, Classic facial, Express facial</td><td>Tue 09:00–17:00 · Wed 09:00–17:00 · Thu 09:00–17:00 · Fri 09:00–17:00 · Sat 09:00–17:00</td><td>Yes</td><td><div className="button-pair"><button className="button button--ghost button--small">Edit</button><button className="button button--ghost button--small">Hours</button></div></td></tr></OwnerTable>}
function TherapistEditor({state}:{state:string}) {const edit=state!=="add";return <Dialog title={edit?"Edit Lena":"Add therapist"}>{state==="therapist-error"&&<div className="alert alert--danger"><OIcon name="warning"/>A therapist with this name already exists.</div>}<div className="o-form-grid"><label className="field o-full"><span>Name</span><input aria-invalid={state==="therapist-error"||undefined} defaultValue={edit?"Lena":""}/></label><label className="field o-full"><span>Short bio</span><textarea defaultValue={edit?"Massages and foot reflexology":""}/></label><label className="field o-full"><span>Short bio (German)</span><textarea/><small>Leave empty to use the English bio.</small></label><fieldset className="o-check-fieldset o-full"><legend>Services offered</legend>{["Relaxation massage","Deep tissue massage","Back and neck massage","Classic facial (inactive)","Foot reflexology"].map(x=><label className="check-row" key={x}><input type="checkbox" defaultChecked={!x.includes("Classic")}/>{x}</label>)}</fieldset><label className="check-row o-full"><input type="checkbox" defaultChecked/>Active (can be booked)</label></div><button className="button button--full">Save</button></Dialog>}
const days=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
function HoursEditor({state}:{state:string}) {return <Dialog title="Weekly hours: Lena">{state==="hours-special"&&<div className="notice">Split shifts on the same day are kept only for the first window when saved here.</div>}{state==="hours-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Each day needs a start time before its end time.</div>}<div className="o-hours-grid"><strong>Day</strong><strong>Start</strong><strong>End</strong><strong>Closed</strong>{days.map((d,i)=><div className="o-hours-row" key={d}><span>{d}</span><input type="time" defaultValue={i===6?"":"10:00"} disabled={i===6}/><input type="time" defaultValue={i===6?"":"19:00"} disabled={i===6}/><label className="check-row"><input type="checkbox" defaultChecked={i===6}/><span className="sr-only">{d} closed</span></label></div>)}</div><button className="button button--full">Save</button></Dialog>}
function DayOff({state}:{state:string}){return <Dialog title="Add day off">{state==="dayoff-error"&&<div className="alert alert--danger"><OIcon name="warning"/>Please choose a date.</div>}<label className="field"><span>Who</span><select><option>Whole studio (closed)</option><option>Lena</option><option>Sofia</option></select></label><label className="field"><span>Date</span><input aria-invalid={state==="dayoff-error"||undefined} type="date"/></label><label className="field"><span>Reason</span><input placeholder="e.g. Holiday"/></label><button className="button button--full">Save</button></Dialog>}

const waitRows=[
  ["Lukas Schmidt","lukas.schmidt@example.com","+49 151 0000 0006","Foot reflexology","Thu 15 Oct, 09:00–18:00","Any","12 Oct, 17:20","Awaiting email","info"],
  ["Mia Wagner","mia.wagner@example.com","+49 151 0000 0005","Relaxation massage","Thu 15 Oct, 09:00–18:00","Sofia","12 Oct, 18:40","Waiting","warning"],
  ["Jonas Klein","jonas.klein@example.com","+49 151 0000 0002","Deep tissue massage","Fri 16 Oct, 10:00–16:00","Any","12 Oct, 19:15","Offered","success"],
  ["Sara Rossi","sara.rossi@example.com","+49 151 0000 0007","Classic facial","Sat 17 Oct, 09:00–14:00","Sofia","13 Oct, 08:10","Booked","success"],
  ["Tom Becker","tom.becker@example.com","+49 151 0000 0004","Back and neck massage","Sat 17 Oct, 10:00–15:00","Lena","13 Oct, 08:30","Offer expired","neutral"],
  ["Priya Shah","priya.shah@example.com","+49 151 0000 0003","Express facial","Sun 18 Oct, 10:00–16:00","Sofia","13 Oct, 09:00","Removed / declined","neutral"],
];
function OwnerWaitlist({state}:{state:string}) {
  if(state==="loading")return <OwnerShell page="waitlist-owner" state={state}><Loading/></OwnerShell>;
  if(state==="load-error")return <OwnerShell page="waitlist-owner" state={state}><PageError/></OwnerShell>;
  const empty=state.startsWith("empty");
  return <OwnerShell page="waitlist-owner" state={state}><PageHead title="Waitlist"><label className="field o-day-field"><span>Day</span><input type="date" defaultValue="2026-10-15"/></label><button className="button button--ghost button--small">All upcoming</button></PageHead>{empty?<div className="empty-state">{state==="empty-day"?"Nobody is waiting for this day.":"Nobody is on the waitlist."}</div>:<OwnerTable heads={["Customer","Services","Day and window","Therapist","Joined","Status",""]}>{waitRows.map(r=><tr key={r[0]}><td><strong>{r[0]}</strong><small>{r[1]}<br/>{r[2]}</small></td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td><td><OStatus tone={r[8]} outlined={r[7]==="Booked"}>{r[7]}</OStatus>{r[7]==="Offered"&&<small>Offered 11:00<br/>until 13 Oct, 10:30</small>}{r[7]==="Booked"&&<small><a href="#">View booking</a></small>}</td><td>{["Awaiting email","Waiting","Offered"].includes(r[7])&&<button className="button button--ghost button--small">Remove</button>}</td></tr>)}</OwnerTable>}{state==="removed"&&<Toast>Mia Wagner removed from the waitlist</Toast>}</OwnerShell>;
}

function Settings({state}:{state:string}) {
  if(state==="loading")return <OwnerShell page="settings" state={state}><Loading/></OwnerShell>;
  if(state==="load-error")return <OwnerShell page="settings" state={state}><PageError server/></OwnerShell>;
  const err=state==="validation";
  return <OwnerShell page="settings" state={state}><PageHead title="Studio settings"/>{err&&<div className="alert alert--danger"><OIcon name="warning"/>Minimum notice must be 0 to 72 hours.</div>}<form className="o-settings-form">
    <fieldset className="o-settings-card"><legend>Studio details</legend><p>Shown on the home page, on receipts and in every email. Customer replies to emails go to the email address below.</p><label className="field"><span>Studio name</span><input defaultValue="Isar Wellness"/></label><label className="field"><span>Address</span><input defaultValue="Isarstraße 12, 80469 München"/></label><div className="o-form-grid"><label className="field"><span>Phone</span><input defaultValue="+49 89 0000 0000"/></label><label className="field"><span>Email (reply-to)</span><input defaultValue="hello@isar-wellness.example.com"/></label></div><label className="field"><span>Opening hours (as shown on the home page)</span><textarea defaultValue="Mon 10:00–19:00 · Tue–Fri 9:00–19:00 · Sat 9:00–17:00 · Sun closed"/><small>Separate parts with ' · ', e.g. Mon 10:00–19:00 · Sat 9:00–17:00 · Sun closed. Bookable times come from Therapists & hours.</small></label><label className="field"><span>Opening hours (German)</span><textarea/><small>e.g. Mo 10–19 Uhr · Sa 9–17 Uhr · So geschlossen. Leave empty to use the English text.</small></label></fieldset>
    <fieldset className="o-settings-card"><legend>Booking rules</legend><p>Apply from now on. Existing bookings keep their times and prices.</p><div className="o-form-grid"><label className="field"><span>Minimum notice (hours)</span><input aria-invalid={err||undefined} type="number" defaultValue={err?"80":"2"}/><small>Customers can't book later than this; phone bookings can.</small></label><label className="field"><span>Book up to (days ahead)</span><input type="number" defaultValue="60"/></label><label className="field"><span>Free cancellation until (hours before)</span><input type="number" defaultValue="24"/><small>Later cancellations are allowed but marked late.</small></label><label className="field"><span>Waitlist offer lasts (minutes)</span><input type="number" defaultValue="30"/></label></div></fieldset>
    <fieldset className="o-settings-card"><legend>Receipts</legend><label className="field"><span>Receipt number prefix</span><input defaultValue="IW"/><small>Receipts are numbered PREFIX-YEAR-0001. A new prefix starts again at 0001.</small></label></fieldset>
    <button className="button o-save-settings">Save settings</button></form>{state==="saved"&&<Toast>Settings saved</Toast>}
  </OwnerShell>;
}

function FlowNode({children}:{children:ReactNode}){return <span className="c-flow-node">{children}</span>} function Arrow(){return <span className="c-flow-arrow">→</span>}
function OwnerFlows(){return <div className="o-owner-flows"><p className="eyebrow">Owner journeys</p><h1>Owner flows</h1><Flow title="Login to dashboard" nodes={["Studio login","Log in","Dashboard","Appointment row","Bookings · detail"]}/><Flow title="Phone booking" nodes={["Bookings","Add booking","Fill form","Save booking","Toast","Booking detail"]}/><Flow title="After the visit" nodes={["Booking detail","Status: Done","Save status","Adjust items","+ Add line","Save items","Send receipt","Print receipt","A4 receipt"]}/></div>}
function Flow({title,nodes}:{title:string;nodes:string[]}){return <section className="o-flow"><h2>{title}</h2><div className="c-flow-row">{nodes.map((n,i)=><span className="o-flow-piece" key={n}><FlowNode>{n}</FlowNode>{i<nodes.length-1&&<Arrow/>}</span>)}</div></section>}

function Render({screen,state}:{screen:OwnerId;state:string}) {
  if(screen==="login")return <Login state={state}/>;
  if(screen==="dashboard")return <Dashboard state={state}/>;
  if(screen==="bookings")return <Bookings state={state}/>;
  if(screen==="services")return <Services state={state}/>;
  if(screen==="therapists")return <Therapists state={state}/>;
  if(screen==="waitlist-owner")return <OwnerWaitlist state={state}/>;
  if(screen==="settings")return <Settings state={state}/>;
  if(screen==="session-error")return <PageError session server={state==="server"}/>;
  return <OwnerFlows/>;
}

export default function OwnerScreens(){
  const [screen,setScreen]=useState<OwnerId>("login"),[state,setState]=useState("empty"),[viewport,setViewport]=useState<"desktop"|"mobile">("desktop");
  const states=useMemo(()=>ownerStates[screen],[screen]);
  const change=(id:OwnerId)=>{setScreen(id);setState(ownerStates[id][0].value)};
  return <main id="main-content" className="customer-gallery"><header className="gallery-head"><div><p className="eyebrow">Part 3 · Owner experience</p><h1>Owner screens</h1><p>Every owner page, operational state and dialog in the shared Calm modern system.</p></div><div className="gallery-controls"><label className="field"><span>Screen</span><select value={screen} onChange={e=>change(e.target.value as OwnerId)}><option value="login">O1 · Studio login</option><option value="dashboard">O2 · Dashboard</option><option value="bookings">O3 · Bookings</option><option value="services">O4 · Services & add-ons</option><option value="therapists">O5 · Therapists & hours</option><option value="waitlist-owner">O6 · Waitlist</option><option value="settings">O7 · Studio settings</option><option value="session-error">Session-check error</option><option value="owner-flows">Owner flows</option></select></label><label className="field"><span>Frame / state</span><select value={state} onChange={e=>setState(e.target.value)}>{states.map(s=><option key={s.value} value={s.value}>{s.label}</option>)}</select></label><div className="field"><span>Viewport</span><div className="segmented"><button className={viewport==="mobile"?"is-selected":""} onClick={()=>setViewport("mobile")}>390</button><button className={viewport==="desktop"?"is-selected":""} onClick={()=>setViewport("desktop")}>1440</button></div></div></div></header><div className={`customer-preview owner-preview customer-preview--${viewport}`}><div className="customer-preview__label">{viewport==="mobile"?"390px · Mobile":"1440px · Desktop"}</div><div className="customer-preview__canvas"><Render screen={screen} state={state}/></div></div></main>;
}
