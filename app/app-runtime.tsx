'use client';
import {useEffect} from 'react';
export default function AppRuntime(){useEffect(()=>{if('serviceWorker' in navigator&&window.isSecureContext){navigator.serviceWorker.register('/sw.js',{scope:'/',updateViaCache:'none'}).catch(e=>console.warn('App offline screen could not be registered',e));}},[]);return null}
