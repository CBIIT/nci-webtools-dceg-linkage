import React from "react";
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
