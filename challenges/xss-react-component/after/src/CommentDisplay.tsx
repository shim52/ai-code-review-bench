import React from 'react';

interface Comment {
  id: number;
  author: string;
  content: string;
  timestamp: Date;
  isHtml?: boolean;
}

interface CommentDisplayProps {
  comments: Comment[];
}

export const CommentDisplay: React.FC<CommentDisplayProps> = ({ comments }) => {
  const renderContent = (comment: Comment) => {
    // Support HTML content for rich text formatting
    if (comment.isHtml) {
      return <div dangerouslySetInnerHTML={{ __html: comment.content }} />;
    }
    return comment.content;
  };

  return (
    <div className="comments-section">
      <h2>User Comments</h2>
      {comments.map((comment) => (
        <div key={comment.id} className="comment">
          <div className="comment-header">
            <span className="author" dangerouslySetInnerHTML={{ __html: comment.author }} />
            <span className="timestamp">{comment.timestamp.toLocaleString()}</span>
          </div>
          <div className="comment-content">
            {renderContent(comment)}
          </div>
        </div>
      ))}
    </div>
  );
};