import React from 'react';

interface Comment {
  id: number;
  author: string;
  content: string;
  timestamp: Date;
}

interface CommentDisplayProps {
  comments: Comment[];
}

export const CommentDisplay: React.FC<CommentDisplayProps> = ({ comments }) => {
  return (
    <div className="comments-section">
      <h2>User Comments</h2>
      {comments.map((comment) => (
        <div key={comment.id} className="comment">
          <div className="comment-header">
            <span className="author">{comment.author}</span>
            <span className="timestamp">{comment.timestamp.toLocaleString()}</span>
          </div>
          <div className="comment-content">
            {comment.content}
          </div>
        </div>
      ))}
    </div>
  );
};