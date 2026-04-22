# Sport corpus — licenses, attribution, and redistribution boundary

Every `.mp4` in this directory is a clip from **HMDB-51** (human-action
recognition dataset, Serre Lab, Brown University, ICCV 2011).

## Dataset-level license

**License:** [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)

**Required attribution:**

> Kuehne, H., Jhuang, H., Garrote, E., Poggio, T., Serre, T. 
> *HMDB: a large video database for human motion recognition.* 
> International Conference on Computer Vision (ICCV), 2011. 
> <https://serre.lab.brown.edu/hmdb51.html>

**Accessed via:** the `divm/hmdb51` HuggingFace mirror, which hosts per-clip
pre-extracted `.mp4` files derived from the Serre Lab RAR archive.

## Residual copyright — read before use

HMDB-51 was compiled from **mixed source footage** — YouTube user uploads, DVDs,
and broadcast clips (examples visible in the manifest below: 'Tour de France',
'APOCALYPTO', 'BRIAN CLOUGH'). The Serre Lab's CC-BY-4.0 license applies to the
**dataset as a research compilation** — the act of collecting, organising,
labelling, and publishing the corpus. Individual clips may retain residual
copyright from their original sources.

This is HMDB-51's well-known posture and is how every downstream paper handles
it. Aegis inherits the same discipline:

1. **Benchmark use only.** These clips feed `backend/detect.py` in the LOCAL
   pipeline and `benchmark/run.py` to compute recall / match-rate / precision.
   They never leave the developer or Cloud Run environment.
2. **Not redistributed.** `.gitignore` excludes `data/originals/*.mp4`. They are
   not in the public GitHub repo, not in the benchmark results JSON, and not in
   the submission tarball.
3. **Not shown in the public demo video.** The 2:45 demo video published on
   YouTube uses **team-generated** or **clearly-CC-licensed** footage for every
   on-screen moment — see `docs/demo-cold-open.md` and `data/case-study/`. No
   HMDB-51 clip is ever rendered to a public surface.
4. **Derived artefacts (benchmark variants) inherit the same boundary.** The
   output of `benchmark/generate_variants.py` is also gitignored and not
   published in any submission artefact.

If your reviewer needs a CC-0-clean corpus (no residual copyright anywhere), swap
HMDB-51 for a Pexels / Pixabay / Mixkit custom download in `scripts/download_corpus.py`.
The rest of the pipeline is indifferent to the source.

## Clip manifest

| File | Class | Source path (repo) | Duration (s) | Size (bytes) |
|---|---|---|---:|---:|
| match-01.mp4 | catch | divm/hmdb51:test/catch_Ball_hochwerfen_-_Rolle_-_Ball_fangen_(Timo_3)_catch_f_cm_np1_le_goo_0.mp4 | 1.27 | 55,121 |
| match-02.mp4 | catch | divm/hmdb51:test/catch_Fangen_und_Werfen_catch_u_nm_np1_fr_bad_0.mp4 | 1.10 | 28,626 |
| match-03.mp4 | catch | divm/hmdb51:test/catch_Florian_Fromlowitz_beim_Training_der_U_21_Nationalmannschaft_catch_u_cm_np1_le_med_1.mp4 | 1.10 | 91,540 |
| match-04.mp4 | catch | divm/hmdb51:test/catch_Goal_Keeping_Tips_catch_f_cm_np1_fr_med_0.mp4 | 2.33 | 206,767 |
| match-05.mp4 | dribble | divm/hmdb51:test/dribble_10YearOldYouthBasketballStarBaller_dribble_f_cm_np1_fr_med_2.mp4 | 3.30 | 143,409 |
| match-06.mp4 | dribble | divm/hmdb51:test/dribble_10YearOldYouthBasketballStarBaller_dribble_f_cm_np1_fr_med_7.mp4 | 11.93 | 272,701 |
| match-07.mp4 | dribble | divm/hmdb51:test/dribble_10YearOldYouthBasketballStarBaller_dribble_f_cm_np1_fr_med_8.mp4 | 5.60 | 220,506 |
| match-08.mp4 | dribble | divm/hmdb51:test/dribble_Basic_Basketball_Moves_dribble_f_cm_np1_ri_goo_6.mp4 | 2.60 | 123,274 |
| match-09.mp4 | golf | divm/hmdb51:test/golf_Ben_Hogan_Swing_golf_f_nm_np1_ri_med_2.mp4 | 2.60 | 74,971 |
| match-10.mp4 | golf | divm/hmdb51:test/golf_Ernie_Els_Swing__Big_easy!_golf_f_cm_np1_fr_med_0.mp4 | 2.57 | 153,653 |
| match-11.mp4 | golf | divm/hmdb51:test/golf_Evian_Masters_Junior_Cup_Highlights_2009_golf_f_nm_np1_ba_goo_0.mp4 | 2.57 | 131,273 |
| match-12.mp4 | golf | divm/hmdb51:test/golf_Golf_Swing_#6Iron_golf_f_cm_np1_fr_med_2.mp4 | 2.27 | 65,973 |
| match-13.mp4 | kick_ball | divm/hmdb51:test/kick_ball_Amazing_Soccer_#2_kick_ball_f_cm_np1_ba_bad_5.mp4 | 1.40 | 88,872 |
| match-14.mp4 | kick_ball | divm/hmdb51:test/kick_ball_Amazing_Soccer_#2_kick_ball_f_cm_np1_le_bad_2.mp4 | 1.10 | 70,741 |
| match-15.mp4 | kick_ball | divm/hmdb51:test/kick_ball_Awesome_Amazing_Great_Soccer_Free_Kicks_kick_ball_f_cm_np1_ba_bad_0.mp4 | 1.53 | 103,386 |
| match-16.mp4 | kick_ball | divm/hmdb51:test/kick_ball_BRIAN_CLOUGH_-_ON_THE_TRAINING_GROUND_kick_ball_f_cm_np1_ri_med_0.mp4 | 2.23 | 69,986 |
| match-17.mp4 | ride_bike | divm/hmdb51:test/ride_bike_1989_Tour_de_France_Final_Time_Trial_ride_bike_f_cm_np1_ba_med_1.mp4 | 8.17 | 357,976 |
| match-18.mp4 | ride_bike | divm/hmdb51:test/ride_bike_1989_Tour_de_France_Final_Time_Trial_ride_bike_f_cm_np1_fr_med_7.mp4 | 5.97 | 518,453 |
| match-19.mp4 | ride_bike | divm/hmdb51:test/ride_bike_1989_Tour_de_France_Final_Time_Trial_ride_bike_f_cm_np1_le_med_4.mp4 | 2.67 | 234,248 |
| match-20.mp4 | ride_bike | divm/hmdb51:test/ride_bike_1996_Tour_de_France_-_Indurain_Cracks_ride_bike_f_cm_np1_le_med_0.mp4 | 2.60 | 306,008 |
| match-21.mp4 | shoot_ball | divm/hmdb51:test/shoot_ball_3PointJumpShotPractice-09_21_07_shoot_ball_f_nm_np1_ri_med_0.mp4 | 2.53 | 47,935 |
| match-22.mp4 | shoot_ball | divm/hmdb51:test/shoot_ball_3PointJumpShotPractice-09_21_07_shoot_ball_f_nm_np1_ri_med_1.mp4 | 2.83 | 56,112 |
| match-23.mp4 | shoot_ball | divm/hmdb51:test/shoot_ball_3PointJumpShotPractice-09_21_07_shoot_ball_f_nm_np1_ri_med_3.mp4 | 3.00 | 61,850 |
| match-24.mp4 | shoot_ball | divm/hmdb51:test/shoot_ball_3PointJumpShotPractice-09_21_07_shoot_ball_f_nm_np1_ri_med_8.mp4 | 3.50 | 76,103 |
| match-25.mp4 | swing_baseball | divm/hmdb51:test/swing_baseball_BaseballSwingAnalysis_swing_baseball_f_nm_np1_fr_med_14.mp4 | 6.93 | 174,369 |
| match-26.mp4 | swing_baseball | divm/hmdb51:test/swing_baseball_BaseballSwingAnalysis_swing_baseball_f_nm_np1_fr_med_17.mp4 | 7.50 | 198,601 |
| match-27.mp4 | swing_baseball | divm/hmdb51:test/swing_baseball_BaseballSwingAnalysis_swing_baseball_f_nm_np1_fr_med_8.mp4 | 4.97 | 250,354 |
| match-28.mp4 | throw | divm/hmdb51:test/throw_2008-08-09GiantsGameDodgersPracticeClaytonKershaw_throw_f_cm_np1_fr_med_0.mp4 | 3.67 | 167,367 |
| match-29.mp4 | throw | divm/hmdb51:test/throw_APOCALYPTO_throw_f_nm_np1_fr_med_1.mp4 | 1.80 | 141,223 |
| match-30.mp4 | throw | divm/hmdb51:test/throw_AdamandAlvonplayingbasketball2_throw_f_nm_np1_fr_med_1.mp4 | 2.63 | 63,592 |

## Notes

- Rerunning `scripts/download_corpus.py` is idempotent — it skips files already present.
- The `_cache/` subdirectory holds the HuggingFace snapshot download (gitignored).
- `.benchmark_clip_map.json` is written by `benchmark/run.py --ingest-first` and maps
  source stems to clip UUIDs issued at ingest time.