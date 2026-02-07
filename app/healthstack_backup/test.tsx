import React from 'react';
import { createRoot } from 'react-dom/client';

const TestApp = () => {
    return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
            <h1>🌱 Health Stack 테스트</h1>
            <p>React가 정상적으로 로드되었습니다!</p>
        </div>
    );
};

const root = createRoot(document.getElementById('root')!);
root.render(<TestApp />);
