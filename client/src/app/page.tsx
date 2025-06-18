import Image from "next/image";
import styles from "./page.module.css";
import Header from "./components/Header";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import CardContent from "./components/CardContent";
import NewsSection from "./components/NewSections";
import Credits from "./components/Credits";

export default function Home() {
  return (
    <div >      
       
        <div className="container">
          <CardContent />
          <NewsSection />
          <Credits />
        </div>
        
       
    </div>
  );
}
