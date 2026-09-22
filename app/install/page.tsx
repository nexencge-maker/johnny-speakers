import type {Metadata} from 'next';
import InstallClient from './install-client';
export const metadata:Metadata={title:'Get the Johnny Speakers App',description:'Add Johnny Speakers to your home screen for beats, videos and creative connections with JDP.'};
export default function Install(){return <InstallClient/>}
