import {env} from 'cloudflare:workers';
import {getChatGPTUser} from '@/app/chatgpt-auth';
import {initialTracks,initialSettings,Track} from './catalog';
export const runtime=()=>env as typeof env & {OWNER_SETUP_CODE?:string;STRIPE_SECRET_KEY?:string;SITE_URL?:string};
export function db(){if(!env.DB)throw new Error('Store storage is unavailable. Please try again.');return env.DB}
export async function getSetting(key:string){return (await db().prepare('SELECT value FROM settings WHERE key=?').bind(key).first<{value:string}>())?.value}
export async function settings(){const v=await getSetting('public');return v?{...initialSettings,...JSON.parse(v)}:initialSettings}
export async function allTracks(){const r=await db().prepare('SELECT data FROM tracks').all<{data:string}>();const map=new Map(initialTracks.map(t=>[t.id,t]));for(const t of r.results) {const x=JSON.parse(t.data);map.set(x.id,x)}return [...map.values()] as Track[]}
export async function isOwner(){const user=await getChatGPTUser();return !!user&&await getSetting('owner')===user.userId}
export async function mustOwner(){if(!await isOwner())throw new Error('Artist access required. Sign in to your studio.');}
export function textValue(x:unknown,max=3000){return typeof x==='string'?x.trim().slice(0,max):''}
export function sameOrigin(req:Request){const origin=req.headers.get('origin');if(!origin||origin!==new URL(req.url).origin)throw new Error('Request origin rejected.');}
export async function stripe(path:string,body?:URLSearchParams){const key=runtime().STRIPE_SECRET_KEY;if(!key)throw new Error('Purchases are not open yet. Please contact JDP to reserve this beat.');const r=await fetch('https://api.stripe.com/v1/'+path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+key,...(body?{'Content-Type':'application/x-www-form-urlencoded'}:{})},body});const data:any=await r.json();if(!r.ok){console.error('Stripe request failed',r.status);throw new Error('Payment service is unavailable. Please try again.')}return data}
