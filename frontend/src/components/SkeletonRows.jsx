import React from 'react';

export default function SkeletonRows({ count = 3 }) {
  const rows = new Array(count).fill(0);
  return (
    <div className="settings-loading">
      {rows.map((_, i) => (
        <div className="settings-loading__row" key={i} />
      ))}
    </div>
  );
}
