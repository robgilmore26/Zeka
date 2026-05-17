# Shipping Zeka to App Store & Play Store with Capacitor

Zeka is a PWA. Capacitor wraps the existing `index.html` + assets into native iOS/Android apps without rewriting anything. This guide walks the full publishing path.

## What you get

- **Native iOS app** (App Store) and **Android app** (Play Store) from the same `index.html`
- **Real Taptic Engine haptics** on iPhone (not the silent Web Vibration API)
- **Native splash screen** (no flash of empty screen on launch)
- **Native push notifications** (Web Push doesn't work on iOS at all)
- **Better PWA installability** for users who'd never install a "website to home screen"

## One-time setup

You need these installed locally:

### Both platforms
```bash
# Node 18+
node -v

# Install Capacitor + plugins (run from the project root)
npm install
```

### iOS (Mac only, for actual builds)
- **Xcode 15+** (Mac App Store, ~30 GB)
- **CocoaPods**: `sudo gem install cocoapods`
- An **Apple Developer account** ($99/year)

### Android
- **Android Studio** with Android SDK
- A **Google Play Console account** ($25 one-time)

## Initial scaffold (one time)

After `npm install`:

```bash
# Add the iOS platform (creates ios/ folder)
npx cap add ios

# Add the Android platform (creates android/ folder)
npx cap add android

# Sync web code into both
npx cap sync
```

`ios/` and `android/` are Xcode/Android Studio projects that wrap `index.html`.

## Typical dev loop

After every change to `index.html`, `sw.js`, etc.:

```bash
npx cap copy        # copies web files into native projects
npx cap sync        # also syncs plugin/dependency changes
```

Then open the native project to build:

```bash
npx cap open ios      # opens Xcode
npx cap open android  # opens Android Studio
```

In Xcode/Android Studio, hit Run to test on a simulator or real device.

## App Store (iOS) — first submission

1. Open `ios/App/App.xcworkspace` in Xcode (`npx cap open ios`)
2. In Xcode → Project settings:
   - **Bundle identifier**: `one.zeka.app` (matches `capacitor.config.json`)
   - **Version**: `1.0.0`, **Build**: `1`
   - **Signing**: Sign in with your Apple Developer account
   - **App icons & splash**: drag `icon-1024.png` into `App/Assets.xcassets/AppIcon`
3. Set the **scheme** to "Any iOS Device" and Product → Archive
4. In the Organizer that opens, choose **Distribute App** → App Store Connect → Upload
5. Go to App Store Connect (web), create the app listing, attach screenshots, write the description, and submit for review

App Store review typically takes 24–48 hours. First submission may take longer if they ask questions.

## Play Store (Android) — first submission

1. Open Android Studio (`npx cap open android`)
2. Sync Gradle (it'll happen automatically)
3. **Build → Generate Signed Bundle / APK → Android App Bundle (AAB)**
4. Create a new keystore (this is your signing key — back up the file and password, you'll need it for every update forever)
5. Sign the bundle
6. Go to Google Play Console (web), create the app, upload the `.aab`, fill out the store listing, run through the content rating questionnaire, and submit for review

Play review typically takes a few hours to a couple days.

## Things that will be different in native vs. PWA

| Feature | PWA (browser) | Capacitor (native) |
|---|---|---|
| Haptics | `navigator.vibrate` — silent on iOS | Native Taptic Engine / Android haptics |
| Push notifications | Doesn't work on iOS Safari | Full APNs / FCM support |
| Splash screen | Browser's default | Custom branded splash |
| Status bar | Browser chrome | Customizable via plugin |
| Audio autoplay | Blocked until user gesture | Allowed |
| Storage | localStorage / Firestore | Same, plus native KV plugins |
| Updates | Push to GitHub Pages, users get new code instantly | App Store review cycle (1-2 days) |

## Suggested update flow once you're live

1. **PWA stays the canonical version** at zeka.one — gets every change instantly
2. **Native apps update on a slower cadence** — batch maybe 2-4 weeks of changes per release, since App Store review takes time and users get notified of updates
3. Bumping a version: edit `package.json`, `capacitor.config.json`, and the version numbers in `ios/App/App.xcodeproj/project.pbxproj` + `android/app/build.gradle`. Then `npx cap sync` and rebuild.

## Native-only features to consider once shipped

- **Native push notifications** for daily-streak reminders (huge for retention)
- **Local notifications** ("you haven't reviewed in 3 days")
- **Native deep links** so `zeka.one/lesson/42` opens the right unit inside the app
- **In-App Purchase / Subscription** if you ever monetize (Stripe doesn't work for Apple, must use IAP)
- **Sign in with Apple** (required by Apple if you offer any other social sign-in)

## Common gotchas

- **CORS**: Capacitor serves your files from `capacitor://localhost` — make sure Firebase auth redirects and any API requests handle that origin
- **Service Worker**: Mostly irrelevant inside Capacitor (no caching needed — the app IS the bundle). The PWA service worker can stay; it just won't fire in native mode.
- **Icons**: Capacitor needs `icon-1024.png` (App Store) and `icon-512.png` for adaptive Android icons. Use [`@capacitor/assets`](https://github.com/ionic-team/capacitor-assets) to auto-generate every size from one source.
- **iOS App Store rejection reasons** (common):
  - Missing Sign-in with Apple if you offer Google Sign-in (Apple requires both)
  - "Doesn't provide enough functionality" — make sure your app store description is feature-heavy
  - Webview-only apps without offline functionality are sometimes rejected — Zeka's offline support helps

## Cost summary

| | One-time | Recurring |
|---|---|---|
| Apple Developer | — | $99/year |
| Google Play | $25 | — |
| Capacitor + plugins | Free, MIT | Free |
| Mac (for Xcode builds) | Mac mini ~$600 | — |

Total to ship both: ~$125 + a Mac (or rent a cloud Mac via MacInCloud).
