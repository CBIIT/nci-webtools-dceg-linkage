"use client";
import React, { useState, useEffect } from "react";
import NewsCard from "@/components/cards/news-card";
import { newsData } from "../ldLinkData/newsData";

export default function WhatsNew() {
  const [startIndex, setStartIndex] = useState(0);
  const visibleCount = 3;

  const handlePrev = () => {
    setStartIndex((prev) => Math.max(prev - visibleCount, 0));
  };

  const handleNext = () => {
    setStartIndex((prev) =>
      Math.min(prev + visibleCount, newsData.length - visibleCount)
    );
  };

  const visibleNews = newsData.slice(startIndex, startIndex + visibleCount);

  useEffect(() => {
    const handler = () => {
      const anchor = document.getElementById("version-tab-anchor");
      if (anchor) {
        anchor.click();
        window.scrollTo(0, 0);
      }
    };
    const links = document.querySelectorAll(".version-link");
    links.forEach((link) => link.addEventListener("click", handler));
    return () => {
      links.forEach((link) => link.removeEventListener("click", handler));
    };
  }, [startIndex]);

  return (
    <div className="container py-4">
      <h2 className="text-center" style={{ color: "#566473" }}>
        What&apos;s New
      </h2>

      <div className="news-row d-flex align-items-center">
        <div
          id="news-left-arrow"
          className={`news-scroller ${startIndex === 0 ? "disabled-news-scroller" : ""}`}
          onClick={handlePrev}
          style={{ cursor: "pointer", textAlign: "center", lineHeight: "210px", fontSize: "48px" }}
        >
          &lsaquo;
        </div>

        {visibleNews.map((entry, index) => (
          <NewsCard
            key={startIndex + index}
            newCardId={startIndex + index + 1}
            title={entry.title}
            body={
              <div style={{ marginBottom: "0" }}>
                {entry.items.map((item, idx) => (
                <p
                    key={idx}
                    style={{ marginBottom: "0.5rem" }}
                    dangerouslySetInnerHTML={{
                    __html:
                        startIndex === 0 && index === 0 && idx === entry.items.length - 1
                        ? item + ' <span style="display:block;margin-top:5px;">(See <a class="version-link" href="/history">Version History</a>)</span>'
                        : item,
                    }}
                />
                ))}

              </div>
            }
          />
        ))}

        <div
          id="news-right-arrow"
          className={`news-scroller ${startIndex + visibleCount >= newsData.length ? "disabled-news-scroller" : ""}`}
          onClick={handleNext}
          style={{ cursor: "pointer", textAlign: "center", lineHeight: "210px", fontSize: "48px" }}
        >
          &rsaquo;
        </div>
      </div>
    </div>
  );
}
