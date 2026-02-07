import React from 'react';

const TestPage: React.FC = () => {
  return (
    <div style={{ padding: '50px', fontSize: '24px' }}>
      <h1>TEST PAGE - If you see this, React works!</h1>
      <p>Current time: {new Date().toLocaleString()}</p>
    </div>
  );
};

export default TestPage;
