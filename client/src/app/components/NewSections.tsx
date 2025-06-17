"use client";
export default function NewsSection() {
  return (
    <div className="news-and-credits-section">
      <br />
      <br />
      <h2 className="text-center" style={{ color: "#566473" }}>
        What&apos;s New
      </h2>

        <div className="container">
            <div className="news-row d-flex align-items-center">
                <div id="news-left-arrow" className="news-scroller disabled-news-scroller" style={{ float: "left" }}>
                    <div style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>&lsaquo;</div>
                </div>

                {[1, 2, 3].map((id) => (
                    <div key={id} id={`news-card-outside-${id}`} className="news-card-outside">
                    <div className="card">
                        <div className="news-card-left" style={{ fontSize: id === 1 ? "32px" : undefined }}>
                        {/* Optional title or icon space */}
                        </div>
                        <div id={`news-card-${id}`} className="news-card-body">
                        
                        </div>
                    </div>
                    </div>
                ))}

                <div id="news-right-arrow" className="news-scroller disabled-news-scroller" style={{ float: "right" }}>
                    <p style={{ textAlign: "center", lineHeight: "210px", fontSize: "48px" }}>&rsaquo;</p>
                </div>
            </div>
      </div>

     
    </div>
  );
}
