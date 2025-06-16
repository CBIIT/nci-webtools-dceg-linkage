import Image from "next/image";
import styles from "./page.module.css";
import Header from "./components/Header";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <div >      
        <Header />
        <Navbar />
        <div className="container">
        </div>       
        <Footer />
    </div>
  );
}
