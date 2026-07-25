// =====================================================================
//  /sandbox — the Agent Smith sandbox page.
//
//  This is the page the whole "economic skin" exists for. The sibling
//  /agent-smith page is the full instrument: it demands the theory AND the
//  DSL syntax AND a live model key before it shows you anything — an AND-gate
//  almost nobody clears cold. This page removes every prerequisite:
//
//    - pre-written scripts in a trading-desk vocabulary (no syntax to learn),
//    - an offline deterministic engine (no key, no network),
//    - charts that surface the framework quantities as the ANSWER to the
//      story's own question ("why can't the desk zero its risk?" → β > 0).
//
//  The shell touches window/refs (brush geometry, styled-jsx), so it mounts
//  client-only via dynamic(import, { ssr:false }).
// =====================================================================
import Head from "next/head";
import Link from "next/link";
import dynamic from "next/dynamic";

const AgentSmithSandbox = dynamic(
  () => import("@/sandbox/AgentSmithSandbox"),
  { ssr: false, loading: () => <Loading /> }
);

export default function SandboxPage() {
  return (
    <>
      <Head>
        <title>Agent Smith — sandbox</title>
        <meta
          name="description"
          content="Run economic agents in the browser. A trading-desk story that teaches the framework's core — character χ, split attention, the irreducible edge — by running it, no theory or keys required."
        />
      </Head>
      <main className="min-h-screen w-full bg-neutral-950 px-4 py-6 text-neutral-100 md:px-8">
        <header className="mx-auto mb-5 max-w-[1400px]">
          <h1 className="text-2xl font-bold tracking-tight">
            Agent&nbsp;Smith — sandbox
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-neutral-400">
            A trading desk that never stops trading is a{" "}
            <em>character</em>. Its attention, split across order books, divides
            by <em>water-filling</em>. The edge it can never arbitrage away is a{" "}
            <em>floor</em> that stays above zero. Open a file, press a slice of a
            chart, and watch the line of code that produced it light up. No
            theory, no syntax, no keys — just run the desk.
          </p>
        </header>
        <div className="mx-auto max-w-[1400px]">
          <AgentSmithSandbox />
        </div>
        <footer className="mx-auto mt-5 max-w-[1400px] text-center text-xs text-neutral-600">
          the same engine Buhera OS imports · runs offline · four invariants held by construction ·{" "}
          <Link href="/agent-smith" className="underline hover:text-neutral-400">
            the full instrument →
          </Link>
        </footer>
      </main>
    </>
  );
}

function Loading() {
  return (
    <div className="flex h-[82vh] min-h-[620px] items-center justify-center rounded-[10px] border border-neutral-800 bg-neutral-900 font-mono text-sm text-neutral-500">
      loading the sandbox…
    </div>
  );
}
