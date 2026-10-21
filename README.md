# NBA Instagram bot (experimental)

Free-cost educational starter. **Not guaranteed production-ready.** No paid services required, but NBA data endpoint is undocumented and may stop working; news is discovery-only. Publishing is disabled by default.

## Setup
1. Create a PUBLIC GitHub repository and upload all files including `.github/workflows/bot.yml`.
2. Settings > Pages > Build and deployment > Source: **GitHub Actions**.
3. Settings > Actions > General > Workflow permissions: Read and write permissions.
4. Create a Meta developer app with Instagram Graph API content publishing permissions; use a professional Instagram account and associated Facebook Page for the Facebook Login route. Complete any required app review / access setup. Obtain a long-lived Page-linked Instagram publishing token and Instagram professional account ID.
5. Settings > Secrets and variables > Actions: Secrets `IG_ACCESS_TOKEN`, `IG_USER_ID`; Variables `PUBLIC_BASE_URL` (e.g. `https://USERNAME.github.io/REPO`), `GRAPH_VERSION` (current supported version), `DRY_RUN` = `true` initially.
6. Run Actions > NBA Instagram Bot > Run workflow. Check generated `docs/images` and logs.
7. Set `DRY_RUN=false` after permissions, token, and public URL are verified. First run queues a score image, next run publishes after Pages deploy.

## Important limitations
- GitHub Actions scheduled jobs can be delayed or skipped. Cron is UTC; the included schedule is not DST-aware.
- `site.api.espn.com` is an unofficial/undocumented data interface. Verify ESPN terms and permission for your use, especially commercial use.
- Public repository and Pages images are visible to everyone. Never commit secrets.
- The sample publishes only scores. News headlines are deliberately NOT auto-published because RSS alone cannot verify trades. Player stats require a separately licensed/reliable source and are not implemented here.
- This starter can duplicate a post if Instagram publishes successfully but the state commit fails. A production implementation should reconcile remote media IDs.
- Images and captions should not use unlicensed league marks or player photography.
- Pending publication waits for a subsequent scheduled/manual run, and can be superseded by newer candidates; refine the queue before high volume.
- Meta API versions, access tokens, permissions, and review requirements change; consult Meta's current docs.
