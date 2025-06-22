"use client";
import { useEffect, useRef } from "react";

export default function NewsSection() {
  const homeStartBox = useRef(0); // this replaces global var
  const newsList = useRef<string[]>([]);

  useEffect(() => {
    const runJQueryLogic = async () => {
      if (typeof window === "undefined") return;
      const $ = (await import("jquery")).default;

      $.get("news.html?v=5.7.0", function (data) {
        const list: string[] = [];
        const tmpData = data.split("<p>");
        let versionNews = tmpData[1].replace("<br>", "");
        let lastNews = "";

        if (versionNews.indexOf("</li>") !== -1) {
          lastNews += versionNews.substring(0, versionNews.indexOf("</li>") + 5);
          versionNews = versionNews.substring(versionNews.indexOf("</li>") + 6);
        }

        if (versionNews.indexOf("</li>") !== -1) {
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

        newsList.current = list;

        // Render initial 3
        $("#news-card-1").html(list[0]);
        $("#news-card-2").html(list[1]);
        $("#news-card-3").html(list[2]);

        // Now attach click listeners
        $("#news-right-arrow").on("click", () => {
          if ($("#news-right-arrow").hasClass("enabled-news-scroller")) {
            if (homeStartBox.current + 3 < newsList.current.length) {
              homeStartBox.current += 1;
              $("#news-card-1").html(newsList.current[homeStartBox.current]);
              $("#news-card-2").html(newsList.current[homeStartBox.current + 1]);
              $("#news-card-3").html(newsList.current[homeStartBox.current + 2]);

              if (homeStartBox.current + 3 >= newsList.current.length) {
                $("#news-right-arrow").removeClass("enabled-news-scroller").addClass("disabled-news-scroller");
              }
              $("#news-left-arrow").removeClass("disabled-news-scroller").addClass("enabled-news-scroller");
            }
          }
        });

        $("#news-left-arrow").on("click", () => {
          if ($("#news-left-arrow").hasClass("enabled-news-scroller")) {
            if (homeStartBox.current > 0) {
              homeStartBox.current -= 1;
              $("#news-card-1").html(newsList.current[homeStartBox.current]);
              $("#news-card-2").html(newsList.current[homeStartBox.current + 1]);
              $("#news-card-3").html(newsList.current[homeStartBox.current + 2]);

              if (homeStartBox.current <= 0) {
                $("#news-left-arrow").removeClass("enabled-news-scroller").addClass("disabled-news-scroller");
              }
              $("#news-right-arrow").removeClass("disabled-news-scroller").addClass("enabled-news-scroller");
            }
          }
        });
      });
    };

    runJQueryLogic();
  }, []);

  return (
    <div className="news-and-credits-section">
      <h2 className="text-center" style={{ color: "#566473" }}>What&apos;s New</h2>
      <div className="container">
        <div className="news-row d-flex align-items-center">
          <div id="news-left-arrow" className="news-scroller disabled-news-scroller">
            <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>&lsaquo;</div>
          </div>

          {[1, 2, 3].map((id) => (
            <div key={id} className="news-card-outside" id={`news-card-outside-${id}`}>
              <div className="card d-flex flex-row align-items-start">
                <div className="news-card-left" />
                <div id={`news-card-${id}`} className="news-card-body"></div>
              </div>
            </div>
          ))}

          <div id="news-right-arrow" className="news-scroller enabled-news-scroller">
            <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>&rsaquo;</div>
          </div>
        </div>
      </div>
    </div>
  );
}
