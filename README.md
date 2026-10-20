# Unsigned LÖVE iOS engine builder

This repository builds only the open-source LÖVE 11.5 engine for arm64 iPhones.
It contains no game data, game source, Apple credentials, signing certificates,
or API secrets. The upstream source archive is pinned by SHA-256. LÖVE's
licenses are included in the upstream app bundle.

Run **Actions → Build unsigned iOS engine → Run workflow** in a public
repository. The workflow refuses to build in private repositories. It uses a
standard macOS runner, which GitHub provides free for public repositories,
and retains only the small unsigned engine artifact for one day. It never
enables billing, App Store services, paid runners, or signing.

Download the artifact, then combine its engine with your own game locally.
The output is not directly installable until signed by your own installation
tool. Apple's free signing normally needs renewal every seven days.

Sources:
- https://github.com/love2d/love/releases/tag/11.5
- https://love2d.org/wiki/Game_Distribution
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://developer.apple.com/help/account/basics/about-your-developer-account
