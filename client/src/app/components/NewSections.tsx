"use client";

import { useEffect } from "react";

export default function NewsSection() {
  useEffect(() => {
    // Load jQuery logic once DOM is ready
    const runJQueryLogic = async () => {
      if (typeof window === "undefined") return;

      const $ = (await import("jquery")).default;

      $(document).ready(() => {
        const newsList: string[] = [];

        $.get("news.html?v=5.7.0", function (data) {
          let tmpData = data.split("<p>");
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

          newsList.push(
            lastNews +
              '<p style="margin-bottom:0px; margin-top:5px;">(See <a class="version-link">Version History</a>)</p>'
          );

          newsList.push(
            '<p><b>LDlinkR</b><br></p><div style="height:4px;"/><p style="margin:0;">Interested in accessing LDlink\'s API using R? <br style="margin-bottom:5px;">Check out the new LDlinkR package now available on <a href="https://cran.r-project.org/web/packages/LDlinkR/index.html" title="LDlinkR CRAN" target="_blank">CRAN</a>.</p>'
          );

          newsList.push(
            '<p><b>GWAS Explorer</b><br></p><div style="height:4px;"/><p>Visualize and interact with genome-wide association study results from PLCO Atlas. <br style="margin-bottom:5px;">Check out <a href="https://exploregwas.cancer.gov/plco-atlas/" title="GWAS Explorer" target="_blank">GWAS Explorer</a>. </p>'
          );

          $("#news-card-1").html(newsList[0].replace("<br>", ""));
          $("#news-card-2").html(newsList[1]);
          $("#news-card-3").html(newsList[2]);

          $(".version-link").on("click", function () {
            $("#version-tab-anchor").click();
            window.scrollTo(0, 0);
          });
        });
      });
    };

    runJQueryLogic();
  }, []);

  return (
    <div className="news-and-credits-section">
      <br />
      <br />
      <h2 className="text-center" style={{ color: "#566473" }}>
        What&apos;s New
      </h2>

      <div className="container">
        <div className="news-row d-flex align-items-center">
          <div id="news-left-arrow" className="news-scroller disabled-news-scroller">
            <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>
              &lsaquo;
            </div>
          </div>

          {[1, 2, 3].map((id) => (
            <div key={id} className="news-card-outside">
              <div className="card d-flex flex-row align-items-start">
                <div className="news-card-left" style={{ fontSize: id === 1 ? "32px" : undefined }}>
                  {/* Optional icon or image */}
                </div>
                <div id={`news-card-${id}`} className="news-card-body"></div>
              </div>
            </div>
          ))}

          <div id="news-right-arrow" className="news-scroller disabled-news-scroller">
            <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>
              &rsaquo;
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
