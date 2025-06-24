"use client";
import { useEffect, useState } from "react";

export default function NewsSection() {
  const [newsList, setNewsList] = useState<string[]>([]);
  const [startIndex, setStartIndex] = useState(0);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch("news.html?v=5.7.0");
        const text = await res.text();

        const list: string[] = [];
        const tmpData = text.split("<p>");
        let versionNews = tmpData[1].replace("<br>", "");
        let lastNews = "";

        if (versionNews.includes("</li>")) {
          lastNews += versionNews.substring(0, versionNews.indexOf("</li>") + 5);
          versionNews = versionNews.substring(versionNews.indexOf("</li>") + 6);
        }

        if (versionNews.includes("</li>")) {
          lastNews += '</ul> <a class="version-link">Show more...</a>';
        }

        lastNews =
          lastNews.substring(0, lastNews.indexOf("<ul>") + 3) +
          ' style="padding-left:10px; margin-bottom:0;"' +
          lastNews.substring(lastNews.indexOf("<ul>") + 3);

        list.push(
          lastNews +
            '<p style="margin-bottom:0px; margin-top:5px;">(See <a class="version-link">Version History</a>)</p>'
        );
        list.push(
          '<p><b>LDlinkR</b><br></p><div style="height:4px;"/><p>Check <a href="https://cran.r-project.org/web/packages/LDlinkR/index.html" target="_blank">CRAN</a>.</p>'
        );
        list.push(
          '<p><b>GWAS Explorer</b><br></p><div style="height:4px;"/><p>Visit <a href="https://exploregwas.cancer.gov/plco-atlas/" target="_blank">GWAS Explorer</a>.</p>'
        );

        setNewsList(list);
      } catch (err) {
        console.error("Failed to load news.html:", err);
      }
    };

    fetchNews();
  }, []);

  const handleLeft = () => {
    setStartIndex((prev) => Math.max(prev - 1, 0));
  };

  const handleRight = () => {
    if (startIndex + 3 < newsList.length) {
      setStartIndex((prev) => prev + 1);
    }
  };

  return (
    <div className="news-and-credits-section">
      <h2 className="text-center" style={{ color: "#566473" }}>What&apos;s New</h2>
      <div className="container">
        <div className="news-row d-flex align-items-center">
          <div
            id="news-left-arrow"
            className={`news-scroller ${startIndex > 0 ? "enabled-news-scroller" : "disabled-news-scroller"}`}
            onClick={handleLeft}
          >
            <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>&lsaquo;</div>
          </div>

          {[0, 1, 2].map((offset) => {
            const news = newsList[startIndex + offset] ?? "";
            return (
              <div key={offset} className="news-card-outside" id={`news-card-outside-${offset}`}>
                <div className="card d-flex flex-row align-items-start">
                  <div className="news-card-left" />
                  <div
                    className="news-card-body"
                    dangerouslySetInnerHTML={{ __html: news }}
                  />
                </div>
              </div>
            );
          })}

          <div
            id="news-right-arrow"
            className={`news-scroller ${
              startIndex + 3 < newsList.length ? "enabled-news-scroller" : "disabled-news-scroller"
            }`}
            onClick={handleRight}
          >
            <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>&rsaquo;</div>
          </div>
        </div>
      </div>
    </div>
  );
}
