# Setup Guide — GitHub → Vercel → Unbounce

No command line needed. ~20 minutes. You'll put the files on GitHub, connect Vercel (which gives
you a live URL), then embed that URL in Unbounce.

The folder you're uploading is `industry-risk-radar/` — the one containing `public/`, `pipeline/`,
`data/`, `README.md`, and `vercel.json`.

---

## Part 1 — Put the project on GitHub (web upload, no git)

1. **Create a GitHub account** (skip if you have one): go to https://github.com → Sign up.
2. **Create a new repository:** click the **+** (top-right) → **New repository**.
   - Repository name: `industry-risk-radar`
   - Set it to **Private** (you can make it public later if you want).
   - Do **not** tick "Add a README" (we already have one).
   - Click **Create repository**.
3. **Upload the files:** on the new empty repo page, click **uploading an existing file**
   (the link in "Get started by … uploading an existing file").
   - Open the `industry-risk-radar` folder on your computer.
   - Select **everything inside it** (the `public`, `pipeline`, `data` folders + `README.md` +
     `vercel.json`) and **drag it into the browser**. GitHub keeps the folder structure.
   - Wait for all files to finish uploading (you should see `public/index.html`, `public/app.js`,
     `public/data.js`, etc.).
4. Scroll down, leave the "Commit changes" message as-is, click **Commit changes**.

✅ Your code is now on GitHub.

> Tip: to update files later, open the file on GitHub → pencil icon → edit → commit. Or re-upload.
> When we wire the monthly automation, this is what the job updates for you.

---

## Part 2 — Deploy with Vercel (gives you a live URL)

1. Go to https://vercel.com → **Sign up** → **Continue with GitHub** (easiest — links the two).
2. Click **Add New… → Project**.
3. Find `industry-risk-radar` in the list → **Import**.
4. On the configure screen:
   - **Framework Preset:** Other.
   - **Root Directory:** leave as the repo root (`./`). Our `vercel.json` already points the site
     at the `public/` folder — don't change the output directory.
   - Leave build/install commands empty.
5. Click **Deploy**. After ~30 seconds you'll get a live URL like
   `https://industry-risk-radar.vercel.app`.

✅ Open that URL — you should see the Risk Radar exactly like the local preview.

> Every time the GitHub files change, Vercel automatically rebuilds and updates this URL.

---

## Part 3 — Embed in Unbounce

1. In your Unbounce page builder, drag a **Custom HTML** element onto the page where you want the
   radar.
2. Paste this, replacing the URL with your Vercel URL:

   ```html
   <iframe
     src="https://industry-risk-radar.vercel.app"
     style="width:100%; height:1400px; border:0;"
     title="Signal AI Industry Risk Radar"
     loading="lazy">
   </iframe>
   ```

3. Adjust `height` so it fits without an inner scrollbar (1400px is a good start; nudge up/down).
4. Publish the Unbounce page.

✅ The radar now lives inside your Unbounce landing page, served from Vercel.

> If you'd rather not use an iframe, Unbounce also lets you point a section to an external URL, or
> you can link out to the Vercel URL with a button — but the iframe keeps people on your page.

---

## What happens at refresh time

The page only reads `public/data.js`. Each month the refresh job regenerates `data.js`
(+ `data.json`) and commits to GitHub → Vercel redeploys → Unbounce shows the new month. The page
itself never changes.

## When you're done, tell Claude:
- Your **GitHub repo URL** and **Vercel URL**, and
- Where you want the monthly review ping (email / Slack).

Then Claude can wire up the monthly scheduled task (with the human-review gate) against the real URL,
and swap the placeholder logo for the official Signal AI asset if needed.

---

## Optional: the developer (git) route

If you or a colleague prefer the command line:
```bash
cd industry-risk-radar
git init && git add . && git commit -m "Industry Risk Radar"
git branch -M main
git remote add origin https://github.com/<you>/industry-risk-radar.git
git push -u origin main
```
Then import the repo in Vercel as in Part 2.
