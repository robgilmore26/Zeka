# Usernames & Friends System Design

## Overview
Replace the name/email profile with a username-based social system. Users pick usernames, generate friend codes, search for friends, and view each other's stats.

## Firestore Data Model

```
users/{uid}
  username: "robby123"
  friendCode: "ZK-A7X3"       // 6-char unique code, generated once
  usernameSetAt: timestamp     // for 30-day change limit
  friends: ["uid2", "uid3"]    // accepted friend UIDs
  langs.sr: { elo, xp, streak, completed, ws, ... }
  langs.it: { ... }

usernames/{username_lowercase}
  uid: "abc123"                // enforces uniqueness, enables lookup

friendCodes/{code}
  uid: "abc123"                // maps code → uid

friendRequests/{uid}
  requests: [{ fromUid, fromUsername, sentAt }, ...]
```

## Profile Screen Layout

### Top Area (signed in, has username)
- Avatar (Zeka bunny icon)
- Username displayed as `@robby123`
- ELO level label + rating
- Friend code as copyable badge: `ZK-A7X3 📋`

### Top Area (no username set)
- Prompt with text input + save button
- Validation: 3-20 chars, alphanumeric + underscores, unique check

### Stats Grid (unchanged)
- Streak, XP, Lessons, Words

### Friends Section
- "Friends (N)" header + "Add Friend" button
- Friend list: username, most active language flag, ELO
- Tap friend → read-only profile view (stats + achievements)
- Pending requests at top with accept/decline

### Add Friend Modal
- Two tabs: "Search" | "Friend Code"
- Search: type username → result → "Send Request"
- Code: paste code to add, OR display own code to share

### Achievements (moved below friends)

### Sign Out (bottom)

## Friend Adding Flows

### Search by Username
1. User types username in search field
2. Client queries `usernames/{input}` doc
3. If exists, fetch `users/{uid}` for display name + ELO
4. User taps "Send Request"
5. Append to `friendRequests/{targetUid}.requests[]`

### Friend Code
1. User enters code (e.g. `ZK-A7X3`)
2. Client queries `friendCodes/{code}` → gets target UID
3. Same request flow as search

### Accepting/Declining
- Accept: add each UID to both users' `friends[]` array, remove request
- Decline: remove request

## Username Rules
- 3-20 characters, lowercase alphanumeric + underscores
- Stored lowercase for case-insensitive lookup
- Can change once every 30 days (enforced by `usernameSetAt`)
- Old username doc deleted, new one created on change

## Approach
- Firestore only, no Cloud Functions
- All logic client-side
- Friend code: 2 letters + dash + 4 alphanumeric (e.g. `ZK-A7X3`)
