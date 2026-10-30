# Online Mock Test – Kivy APK (built with GitHub Actions)

## Folder structure
```
mocktest/
├── main.py                      # Kivy app
├── questions.json               # your 72 questions (edit this to change questions)
├── buildozer.spec               # Android build settings
├── fonts/
│   └── NotoSansBengali-Regular.ttf   # YOU must add this file (see Step 2)
└── .github/workflows/build-apk.yml   # GitHub Actions build script
```

## Step 1 – Install Git (once)
Download from https://git-scm.com and install. Create a free account at https://github.com.

## Step 2 – Add the Bengali font (required!)
Kivy's default font cannot show Bengali. Download "Noto Sans Bengali" from
https://fonts.google.com/noto/specimen/Noto+Sans+Bengali , unzip, and copy the
regular weight file into the `fonts/` folder, renamed exactly:

    fonts/NotoSansBengali-Regular.ttf

(If you use a static file, pick `NotoSansBengali-Regular.ttf`. A variable font
file also works – just rename it to the same name.)

## Step 3 – (Optional) Test on your PC
    pip install kivy
    python main.py
Keyboard shortcuts work on PC: A/B/C/D, ← →, Enter.

## Step 4 – Create the GitHub repository
1. GitHub → "+" → New repository → name it `mocktest` → Create (keep it Public or Private).
2. Do NOT tick "Add README".

## Step 5 – Upload the project
In a terminal inside the `mocktest` folder:

    git init
    git add .
    git commit -m "first commit"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/mocktest.git
    git push -u origin main

(Make sure the hidden `.github` folder is included – `git add .` does that.)

## Step 6 – Watch the build
GitHub repo → **Actions** tab → "Build Android APK" runs automatically on every push.
First build takes about 20–40 minutes (it downloads the Android SDK/NDK);
later builds are faster because of caching.
You can also press **Run workflow** to start it manually.

## Step 7 – Download the APK
Open the finished run (green ✔) → scroll to **Artifacts** → click `mocktest-apk`
→ unzip → you get `mocktest-1.0-arm64-v8a_armeabi-v7a-debug.apk`.

## Step 8 – Install on your phone
Copy the APK to your phone → open it → allow "Install unknown apps" when asked → Install.

## Changing things later
* Questions: edit `questions.json` (each item: `q`, `options` (4 items), `answer` = 0-based index of the correct option; 0=a, 1=b, 2=c, 3=d).
* Time / negative marking: top of `main.py` (`TOTAL_SECONDS`, `NEGATIVE_MARK`, `NEGATIVE_VALUE`).
* App name / package / version: `buildozer.spec`.
* After any change: `git add . && git commit -m "update" && git push` → new APK is built.

## Troubleshooting
| Problem | Fix |
|---|---|
| Bengali shows as squares ▯▯▯ | The font file is missing or misnamed in `fonts/`. |
| Build fails: "Cython" error | Keep `cython<3` in the workflow and `kivy==2.3.0` in the spec. |
| Build fails with license error | Keep `android.accept_sdk_license = True`. |
| App crashes at start on phone | Run `adb logcat \| grep python` or check that `questions.json` is committed. |
| Workflow doesn't appear | The file must be exactly `.github/workflows/build-apk.yml` on branch `main`. |
| Bengali conjuncts (যুক্তাক্ষর) look broken | Update to a newer Kivy/p4a, or tell me and I'll switch the UI to a WebView version. |
