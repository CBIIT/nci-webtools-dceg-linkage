import Image from "next/image";
import styles from "./page.module.css";
import Header from "./components/Header";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import MainContent from "./components/MainContent";

export default function Home() {
  return (
    <div >      
        <Header />
        <Navbar />
        <div className="container">
          <MainContent />
        </div>       
        <Footer />
    </div>
  );
}
