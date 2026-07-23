import dynamic from "next/dynamic";
import Head from "next/head";

// The landing page is just the GLB TV, fullscreen, on black.
const TVScene = dynamic(() => import("@/components/TVScene"), { ssr: false });

export default function Home() {
  return (
    <>
      <Head>
        <title>Musande</title>
        <meta
          name="description"
          content="Agent Smith — specify and instantiate purpose-directed agents."
        />
      </Head>
      <main className="fixed inset-0 h-screen w-screen bg-dark">
        <TVScene />
      </main>
    </>
  );
}
