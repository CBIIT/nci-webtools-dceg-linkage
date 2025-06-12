import Image from "next/image";
import styles from "./page.module.css";
import Header from "./components/Header";
import Navbar from "./components/Navbar";

export default function Home() {
  return (
    <>
      <a className="sr-only sr-only-focusable" href="#content">Skip to main content</a>
      <h1 className="sr-only sr-only-focusable">LDlink Webtool</h1>
      <Header />
      <Navbar />
      {/* You can now start inserting tab components, footers, content sections */}
    </>
  );
}
