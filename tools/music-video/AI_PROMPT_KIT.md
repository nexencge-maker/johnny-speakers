# Fifty Million: AI video prompt kit

Use this kit to upgrade the cut-out animation (`animate.py`) to real AI animation: dancing with full body movement, mouths synced to the rap, and wings that look real.

Make each clip with an image-to-video tool (Runway, Kling, Pika or similar). Use a lip-sync tool (Hedra, or the lip-sync feature in Kling or Runway) for the shots where he raps to camera. Then drop the clips into `clips/` and run `assemble_clips.py`. It trims every clip to its slot so the cuts land on the beat.

The song runs at about 120.5 BPM. One bar is about 1.99 s, and the first downbeat is at 0:00.35. Every slot below is a whole number of bars.

## Before you start

1. **Reference image.** Upload one of the photos in `photos/` with every prompt so the character stays consistent. `03-night-cap.png` is the best face reference: it's front-on and evenly lit.
2. **Aspect ratio.** Generate at 16:9, 1080p if the tool offers it.
3. **Clip length.** Most tools make 5 s or 10 s clips. Generate 10 s for slots longer than 5 s. The assembler trims longer clips and slows down shorter ones.
4. **Lip-sync audio.** Cut the song section for each rap shot and give it to the lip-sync tool:
   ```bash
   ffmpeg -ss 56.12 -t 7.97 -i public/media/fifty-video.mp4 -vn -c:a libmp3lame rap_bird.mp3
   ```
   `-ss` is the slot start and `-t` is its length, both from the table.
5. **Style line.** Add this to the end of every prompt so all the clips match:
   > *stylized anime-realism illustration, cel-shaded, rich warm rim light, cinematic, 24fps film look*

## Shot list

| # | Slot (start → end) | File name | Tool | Prompt |
|---|---|---|---|---|
| 1 | 0:00.0 → 0:08.31 | `01_cube_wide.mp4` | image-to-video | Night ocean under a full moon and stars. A huge glowing glass cube floats on calm water, filled with colored party lights and a dancing crowd. The camera glides slowly toward it, and neon light reflects in the ripples. |
| 2 | 0:08.31 → 0:16.28 | `02_cube_dance_cap.mp4` | image-to-video + ref `03` | Inside a glass cube party floating on the ocean at night. The young man in the pink cap and floral jacket dances to a hip-hop beat in the center: shoulders bouncing, head nodding, a smooth two-step. Colored spotlight beams sweep, and the crowd's silhouettes have hands in the air. The moon is visible through the glass walls. |
| 3 | 0:16.28 → 0:20.27 | `03_cube_wide2.mp4` | image-to-video | Closer wide shot of the glowing glass cube on the water. Silhouettes of dancers jump inside, and confetti sparkles. The cube's lights pulse in reflections on the waves. |
| 4 | 0:20.27 → 0:28.23 | `04_cube_dance_shades.mp4` | image-to-video + ref `01` | Inside the glass cube party. The man with locs, gold sunglasses and a black tee dances loose and confident: arm waves, a body roll, then a point at the camera. Party beams and a crowd behind him. |
| 5 | 0:28.23 → 0:32.22 | `05_cube_profile.mp4` | image-to-video + ref `02` | Side-profile close-up of the man in the floral jacket nodding to the beat. His locs bounce and warm party lights flare behind him. |
| 6 | 0:32.22 → 0:40.18 | `06_cube_trio.mp4` | image-to-video + refs `01` `02` `03` | Three versions of the same young man dance side by side in sync inside the glass cube: one in sunglasses and a black tee, one in a floral jacket, one in a pink cap. The crowd cheers and confetti falls. |
| 7 | 0:40.18 → 0:48.15 | `07_cube_fireworks.mp4` | image-to-video | Wide night shot. Fireworks burst above the glowing glass cube on the ocean, and the party lights flash on the beat. |
| 8 | 0:48.15 → 0:56.12 | `08_birds_wide.mp4` | image-to-video + ref `03` | Sunset over the ocean. Three enormous white sea birds glide over the waves, each with a young man riding on its back. Slow powerful wingbeats, golden light and pink clouds. |
| 9 | 0:56.12 → 1:04.08 | `09_bird_rap_cap.mp4` | **lip-sync**: image-to-video first, then lip-sync | Medium close-up. The young man in the pink cap rides on the back of a giant white bird over a sunset ocean, rapping to camera with confident hand gestures. Wind blows his locs and the wings beat behind him. |
| 10 | 1:04.08 → 1:12.05 | `10_bird_rap_profile.mp4` | **lip-sync** | Same setup with the floral-jacket man in profile, rapping as he looks out over the sea from the giant bird's back. |
| 11 | 1:12.05 → 1:20.02 | `11_birds_low.mp4` | image-to-video | Low angle just above the waves. Giant birds with riders sweep overhead and the spray catches the sunlight. |
| 12 | 1:20.02 → 1:27.98 | `12_bird_rap_shades.mp4` | **lip-sync** + ref `01` | The man in gold sunglasses stands up on the giant bird's back, arms out wide, then rapping to camera. The sunset is behind him. |
| 13 | 1:27.98 → 1:35.95 | `13_bird_tight.mp4` | **lip-sync** + ref `03` | Tight close-up on the pink-cap rider's face as he raps intensely. Feathers flutter in the foreground. |
| 14 | 1:35.95 → 1:43.92 | `14_birds_wide2.mp4` | image-to-video | The flock of giant birds climbs toward the clouds, the riders silhouetted against the sun. |
| 15 | 1:43.92 → 1:51.88 | `15_city_walk_profile.mp4` | **lip-sync** + ref `02` | Night city street with neon signs and wet pavement. The floral-jacket man walks toward the right of frame, rapping as he goes, in a tracking side shot with bokeh lights behind him. |
| 16 | 1:51.88 → 1:59.85 | `16_city_walk_front.mp4` | **lip-sync** + ref `03` | He walks straight toward the camera down a neon-lit avenue, rapping to the lens. A slow push-in, with city lights in shallow focus. |
| 17 | 1:59.85 → 2:07.82 | `17_city_walk_shades.mp4` | **lip-sync** + ref `01` | The man in sunglasses and the black tee walks past glowing storefronts, rapping. Street lamps pass in the foreground. |
| 18 | 2:07.82 → 2:15.78 | `18_city_front2.mp4` | **lip-sync** + ref `03` | Crossing a busy crosswalk at night, rapping to camera as traffic light trails streak behind him. |
| 19 | 2:15.78 → 2:23.75 | `19_city_rain.mp4` | image-to-video + ref `02` | Breakdown moment. Light rain on a neon street; he stops and looks up as reflections ripple in the puddles. |
| 20 | 2:23.75 → 2:31.72 | `20_city_walk_final.mp4` | **lip-sync** + ref `01` | He walks and raps with energy and pulls the sunglasses down to look at the camera. |
| 21 | 2:31.72 → 2:39.68 | `21_cube_trio2.mp4` | image-to-video + refs | Back in the glass cube party at full energy. The trio dances in sync and the crowd jumps. Confetti storm. |
| 22 | 2:39.68 → 2:47.65 | `22_cube_cap.mp4` | **lip-sync** + ref `03` | The pink-cap man raps the hook in the middle of the party, with the crowd's hands up behind him. |
| 23 | 2:47.65 → 2:51.63 | `23_cube_fireworks.mp4` | image-to-video | Fireworks over the glass cube, reflected in the ocean. |
| 24 | 2:51.63 → 2:55.62 | `24_cube_shades.mp4` | image-to-video + ref `01` | Quick dance move: a spin, then a freeze pose with sunglasses flashing. |
| 25 | 2:55.62 → 3:03.58 | `25_cube_trio_final.mp4` | image-to-video + refs | The final big dance moment: the trio hits the same move on the downbeat as lights strobe. |
| 26 | 3:03.58 → end | `26_outro_birds.mp4` | image-to-video | The giant birds and their riders fly off into the setting sun over the ocean, and the camera pulls back to a wide shot. |

## Editing the clips to the beat

```bash
python3 tools/music-video/assemble_clips.py \
    --audio public/media/fifty-video.mp4 \
    --clips tools/music-video/clips \
    --fallback public/media/fifty-animated.mp4 \
    --out fifty-million-ai.mp4
```

Any slot whose file is missing is filled from the matching moment of the cut-out animation. That means you can generate a few shots at a time and re-run the script to check progress.

## Tips

- If a tool changes the character's face, re-roll the clip or lower the motion strength. Keeping the face consistent matters more than big movement.
- For lip sync, front-facing shots (`03`) work much better than profiles (`02`).
- The birds should be original creatures, not any specific cartoon or branded mascot. Describe them as "enormous white sea birds".
