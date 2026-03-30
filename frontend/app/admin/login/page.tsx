'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const ML_API = process.env.NEXT_PUBLIC_ML_URL ?? 'http://localhost:8000';

export default function AdminLogin() {
  const [form,    setForm]    = useState({ username:'', password:'' });
  const [error,   setError]   = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res  = await fetch(`${ML_API}/admin/login`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(form),
      });
      if (!res.ok) { setError('Invalid username or password.'); setLoading(false); return; }
      const data = await res.json();
      sessionStorage.setItem('autovalu_token', data.token);
      router.push('/admin');
    } catch {
      setError('Cannot connect to server.');
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight:'100vh', background:'#0A0F1E',
      display:'flex', alignItems:'center', justifyContent:'center', padding:24
    }}>
      <div style={{
        background:'#111827', border:'1px solid #1E293B',
        borderRadius:16, padding:'40px 36px', width:'100%', maxWidth:380
      }}>
        <div style={{textAlign:'center', marginBottom:32}}>
          <div style={{
            width:48, height:48, background:'linear-gradient(135deg,#10B981,#059669)',
            borderRadius:12, display:'flex', alignItems:'center', justifyContent:'center',
            fontSize:24, margin:'0 auto 14px'
          }}>🚗</div>
          <div style={{color:'white', fontWeight:900, fontSize:'1.2rem', letterSpacing:'-0.5px'}}>
            <span style={{color:'#10B981'}}>Auto</span>Valu Admin
          </div>
          <div style={{color:'#475569', fontSize:'0.82rem', marginTop:4}}>
            Sign in to access the dashboard
          </div>
        </div>

        <form onSubmit={submit} style={{display:'flex',flexDirection:'column',gap:14}}>
          <div style={{display:'flex',flexDirection:'column',gap:5}}>
            <label style={{fontSize:'0.72rem',fontWeight:700,color:'#64748B',textTransform:'uppercase',letterSpacing:'0.07em'}}>
              Username
            </label>
            <input
              type="text" value={form.username} required
              onChange={e=>setForm(p=>({...p,username:e.target.value}))}
              placeholder="Enter username"
              style={{
                background:'#1E293B', border:'1.5px solid #334155', borderRadius:8,
                color:'#E2E8F0', padding:'10px 12px', fontSize:'0.92rem',
                outline:'none', width:'100%'
              }}
            />
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:5}}>
            <label style={{fontSize:'0.72rem',fontWeight:700,color:'#64748B',textTransform:'uppercase',letterSpacing:'0.07em'}}>
              Password
            </label>
            <input
              type="password" value={form.password} required
              onChange={e=>setForm(p=>({...p,password:e.target.value}))}
              placeholder="Enter password"
              style={{
                background:'#1E293B', border:'1.5px solid #334155', borderRadius:8,
                color:'#E2E8F0', padding:'10px 12px', fontSize:'0.92rem',
                outline:'none', width:'100%'
              }}
            />
          </div>

          {error && (
            <div style={{
              background:'rgba(220,38,38,0.1)', border:'1px solid rgba(220,38,38,0.3)',
              borderRadius:8, padding:'9px 12px', color:'#F87171', fontSize:'0.83rem'
            }}>{error}</div>
          )}

          <button type="submit" disabled={loading} style={{
            padding:'12px', background: loading ? '#065F46' : '#10B981',
            color:'white', border:'none', borderRadius:8,
            fontWeight:700, fontSize:'0.93rem', cursor: loading ? 'not-allowed' : 'pointer',
            marginTop:4, transition:'background 0.15s'
          }}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}