import Link from "next/link";
import React from "react";
import { useRouter } from "next/router";

// Minimal dark navbar: brand → home (the TV), a link to the Showcase demo,
// and the Agent Smith tool. Nothing else.
const NavLink = ({ href, title }) => {
  const router = useRouter();
  const active = router.asPath === href;
  return (
    <Link
      href={href}
      className={`relative text-sm tracking-wide transition-colors ${
        active ? "text-light" : "text-neutral-400 hover:text-light"
      }`}
    >
      {title}
      <span
        className={`absolute -bottom-1 left-0 h-px bg-light transition-[width] duration-300 ${
          active ? "w-full" : "w-0"
        }`}
      />
    </Link>
  );
};

const Navbar = () => {
  return (
    <header className="absolute top-0 left-0 z-20 flex w-full items-center justify-between px-6 py-5 sm:px-4">
      <Link
        href="/"
        className="font-mono text-sm font-semibold tracking-widest text-light/90 hover:text-light"
      >
        MUSANDE
      </Link>
      <nav className="flex items-center gap-6">
        <NavLink href="/showcase" title="Showcase" />
        <NavLink href="/agent-smith" title="Agent Smith" />
      </nav>
    </header>
  );
};

export default Navbar;
