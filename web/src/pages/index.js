import dynamic from 'next/dynamic'
import Layout from "@/components/Layout";
import Head from "next/head";
import TransitionEffect from "@/components/TransitionEffect";

 
const TVScene = dynamic(() => import('@/components/TVScene'), { ssr: false })


export default function Home() {
  
  return (
    <>
      <Head>
        <title>Musande</title>
        <meta
          name="description"
          content=""
        />
      </Head>

      <TransitionEffect />
      <article
        className={`flex min-h-screen items-center text-dark dark:text-light sm:items-start`}
      >
        <Layout className="!pt-0 md:!pt-16 sm:!pt-16">
          <div className="flex w-full items-start justify-between md:flex-col">
            <div className="w-1/2 lg:hidden md:inline-block md:w-full">
              <TVScene />
          </div>
           </div>
        </Layout>
      </article>
    </>
  );
}
