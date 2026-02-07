import React from 'react'
import ReactDOM from 'react-dom/client'

function App() {
    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: 'white',
            fontFamily: 'sans-serif'
        }}>
            <div style={{ textAlign: 'center', padding: '40px' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>🌱 Health Stack</h1>
                <p style={{ fontSize: '1.2rem', opacity: 0.9 }}>React가 정상 작동합니다!</p>
                <button
                    onClick={() => alert('클릭됨!')}
                    style={{
                        marginTop: '20px',
                        padding: '12px 24px',
                        fontSize: '1rem',
                        background: 'white',
                        color: '#059669',
                        border: 'none',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        fontWeight: 'bold'
                    }}
                >
                    테스트 버튼
                </button>
            </div>
        </div>
    )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
)
