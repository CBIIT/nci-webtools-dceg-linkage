// components/cards/NewsCard.tsx
import React from "react";

type NewsCardProps = {
  title: string;
  body: React.ReactNode;
  newCardId?: number; // This is now consistent
};

export default function NewsCard({ title, body, newCardId }: NewsCardProps) {
  return (
    <div className="news-card-outside">
      <div className="card">
        <div className="news-card-left">
          {title && (
            <div className="news-titles-container">
              <div className="news-titles"></div>
            </div>
          )}
        </div>
        <div className="news-card-body" id={`news-card-${newCardId}`}>
          <p>
            <b>
                {title}
            </b>
          </p>
          <div>
            {body}  
          </div>
          
        </div>
      </div>
    </div>
  );
}

